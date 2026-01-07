import csv
import io
import time
from typing import List, Tuple, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from models import Store, Service, StoreType, StoreStatus
from schemas import ImportResult, ImportReport
from geocoding_service import get_coordinates_from_address, get_coordinates_from_postal_code
import redis

def validate_hours(hours_str: str) -> bool:
    """Validate hours format."""
    if not hours_str or hours_str.lower() == "closed":
        return True
    try:
        parts = hours_str.split('-')
        if len(parts) != 2:
            return False
        open_time, close_time = parts
        # Validate time format (be lenient with single digit hours)
        for t in [open_time.strip(), close_time.strip()]:
            if ':' not in t:
                return False
            h, m = t.split(':')
            if not (0 <= int(h) <= 24 and 0 <= int(m) <= 59):
                return False
            if int(h) == 24 and int(m) > 0:
                return False
        return True
    except:
        return False

def parse_services(services_str: str) -> List[str]:
    """Parse pipe-separated services string."""
    if not services_str:
        return []
    return [s.strip() for s in services_str.split('|') if s.strip()]

def validate_store_row(row: dict) -> Tuple[bool, Optional[str]]:
    """Validate a single store row. Only strictly require store_id and name."""
    required_fields = ['store_id', 'name']
    
    for field in required_fields:
        if not row.get(field):
            return False, f"Missing required field: {field}"
    
    # Validate store_type if provided
    if row.get('store_type'):
        try:
            StoreType(row['store_type'].lower())
        except ValueError:
            return False, f"Invalid store_type: {row['store_type']}"
    
    # Validate status if provided
    if row.get('status'):
        try:
            StoreStatus(row['status'].lower())
        except ValueError:
            return False, f"Invalid status: {row['status']}"
    
    # Validate coordinates if provided
    for coord_field in ['latitude', 'longitude']:
        val = row.get(coord_field)
        if val and str(val).strip():
            try:
                f_val = float(val)
                if coord_field == 'latitude' and (f_val < -90 or f_val > 90):
                    return False, f"Latitude out of range: {f_val}"
                if coord_field == 'longitude' and (f_val < -180 or f_val > 180):
                    return False, f"Longitude out of range: {f_val}"
            except ValueError:
                return False, f"Invalid {coord_field}: {val}"
    
    # Validate hours if provided
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    for day in days:
        hours_field = f'hours_{day}'
        if row.get(hours_field):
            if not validate_hours(row[hours_field]):
                return False, f"Invalid hours format for {day}: {row[hours_field]}"
    
    return True, None

def process_csv_import(
    csv_content: str,
    db: Session,
    redis_client: redis.Redis
) -> ImportReport:
    """Process CSV import and return import report."""
    # Use DictReader but pre-process content to strip headers
    f = io.StringIO(csv_content)
    # Get first line to check headers
    header_line = f.readline()
    if not header_line:
        raise ValueError("CSV file is empty")
    
    # Re-create reader with stripped headers
    f.seek(0)
    raw_reader = csv.reader(f)
    headers = [h.strip() for h in next(raw_reader)]
    
    # Use the stripped headers for DictReader
    f.seek(0)
    next(f) # skip original header line
    reader = csv.DictReader(f, fieldnames=headers)
    
    results: List[ImportResult] = []
    created_count = 0
    updated_count = 0
    failed_count = 0
    
    # Only store_id and name are strictly required in headers
    essential_headers = ['store_id', 'name']
    missing_headers = [h for h in essential_headers if h not in headers]
    if missing_headers:
        raise ValueError(f"Missing essential headers: {', '.join(missing_headers)}")
    
    # Cache services to avoid repeated lookups
    service_cache: Dict[str, Service] = {s.name: s for s in db.query(Service).all()}
    
    # Process each row
    for row_number, raw_row in enumerate(reader, start=2):
        # Strip all values in the row
        row = {k: (v.strip() if v else v) for k, v in raw_row.items()}
        
        # Validate row
        is_valid, error = validate_store_row(row)
        if not is_valid:
            results.append(ImportResult(
                row_number=row_number,
                store_id=row.get('store_id', 'N/A'),
                status="failed",
                error=error
            ))
            failed_count += 1
            continue
        
        store_id = row['store_id']
        
        # Use nested transaction (savepoint) for each row
        # This allows rolling back a single row without affecting others
        with db.begin_nested():
            try:
                # Check if store exists
                existing_store = db.query(Store).filter(Store.store_id == store_id).first()
                
                # ... coordinates handling ...
                latitude = None
                longitude = None
                
                lat_val = row.get('latitude')
                lon_val = row.get('longitude')
                
                if lat_val and lon_val:
                    try:
                        latitude = float(lat_val)
                        longitude = float(lon_val)
                    except ValueError:
                        pass # Fall back to geocoding
                
                if latitude is None or longitude is None:
                    # Try geocoding if we have enough address info
                    address_parts = [
                        row.get('address_street'),
                        row.get('address_city'),
                        row.get('address_state'),
                        row.get('address_postal_code')
                    ]
                    address_parts = [p for p in address_parts if p]
                    
                    if address_parts:
                        address = ", ".join(address_parts)
                        # Check cache first to avoid sleeping
                        cache_key = f"geocoding:{address}"
                        if not redis_client.exists(cache_key):
                            # Respect Nominatim's rate limit if not cached
                            time.sleep(1)
                        
                        coords = get_coordinates_from_address(address, redis_client)
                        if coords:
                            latitude = coords['latitude']
                            longitude = coords['longitude']
                    
                    # If still no coordinates and it's a new store, we might have an issue
                    if latitude is None and not existing_store:
                        results.append(ImportResult(
                            row_number=row_number,
                            store_id=store_id,
                            status="failed",
                            error="Could not determine coordinates from CSV or geocoding"
                        ))
                        failed_count += 1
                        # We use raise to trigger the savepoint rollback
                        raise ValueError("Row-level validation failed")
                
                # Parse services
                services_list = parse_services(row.get('services', ''))
                
                # Helper to get/create service from cache/db
                def get_service(name):
                    if name in service_cache:
                        return service_cache[name]
                    svc = db.query(Service).filter(Service.name == name).first()
                    if not svc:
                        svc = Service(service_id=f"SVC_{name.upper()}", name=name)
                        db.add(svc)
                        db.flush() # Get the object state ready
                    service_cache[name] = svc
                    return svc

                if existing_store:
                    # Update existing store
                    existing_store.name = row['name']
                    if row.get('store_type'):
                        existing_store.store_type = StoreType(row['store_type'].lower())
                    if row.get('status'):
                        existing_store.status = StoreStatus(row['status'].lower())
                    
                    if latitude is not None:
                        existing_store.latitude = latitude
                    if longitude is not None:
                        existing_store.longitude = longitude
                        
                    for field in [
                        'address_street', 'address_city', 'address_state', 
                        'address_postal_code', 'address_country', 'phone'
                    ]:
                        if row.get(field):
                            setattr(existing_store, field, row[field])
                    
                    # Update hours if provided
                    for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
                        field = f'hours_{day}'
                        if row.get(field):
                            setattr(existing_store, field, row[field])
                    
                    # Update services if column exists
                    if 'services' in row:
                        existing_store.services.clear()
                        for service_name in services_list:
                            existing_store.services.append(get_service(service_name))
                    
                    updated_count += 1
                    results.append(ImportResult(
                        row_number=row_number,
                        store_id=store_id,
                        status="updated"
                    ))
                else:
                    # Create new store
                    new_store = Store(
                        store_id=store_id,
                        name=row['name'],
                        store_type=StoreType(row.get('store_type', 'regular').lower()),
                        status=StoreStatus(row.get('status', 'active').lower()),
                        latitude=latitude,
                        longitude=longitude,
                        address_street=row.get('address_street'),
                        address_city=row.get('address_city'),
                        address_state=row.get('address_state'),
                        address_postal_code=row.get('address_postal_code'),
                        address_country=row.get('address_country', 'USA'),
                        phone=row.get('phone'),
                        hours_mon=row.get('hours_mon', 'closed'),
                        hours_tue=row.get('hours_tue', 'closed'),
                        hours_wed=row.get('hours_wed', 'closed'),
                        hours_thu=row.get('hours_thu', 'closed'),
                        hours_fri=row.get('hours_fri', 'closed'),
                        hours_sat=row.get('hours_sat', 'closed'),
                        hours_sun=row.get('hours_sun', 'closed')
                    )
                    
                    # Add services
                    for service_name in services_list:
                        new_store.services.append(get_service(service_name))
                    
                    db.add(new_store)
                    created_count += 1
                    results.append(ImportResult(
                        row_number=row_number,
                        store_id=store_id,
                        status="created"
                    ))
                
                # Periodically flush to avoid huge memory usage for large imports
                if (created_count + updated_count) % 50 == 0:
                    db.flush()
                
            except Exception as e:
                # This block runs if an error occurred within the with db.begin_nested()
                # The nested transaction will be rolled back automatically
                if str(e) != "Row-level validation failed":
                    results.append(ImportResult(
                        row_number=row_number,
                        store_id=store_id,
                        status="failed",
                        error=f"Unexpected error: {str(e)}"
                    ))
                    failed_count += 1
    
    return ImportReport(
        total_rows=len(results),
        created=created_count,
        updated=updated_count,
        failed=failed_count,
        results=results
    )


