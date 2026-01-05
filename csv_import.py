import csv
import io
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from models import Store, Service, StoreType, StoreStatus
from schemas import ImportResult, ImportReport
from geocoding_service import get_coordinates_from_address, get_coordinates_from_postal_code
import redis

def validate_hours(hours_str: str) -> bool:
    """Validate hours format."""
    if hours_str.lower() == "closed":
        return True
    try:
        parts = hours_str.split('-')
        if len(parts) != 2:
            return False
        open_time, close_time = parts
        # Validate time format
        datetime.strptime(open_time.strip(), '%H:%M')
        datetime.strptime(close_time.strip(), '%H:%M')
        return True
    except:
        return False

def parse_services(services_str: str) -> List[str]:
    """Parse pipe-separated services string."""
    if not services_str:
        return []
    return [s.strip() for s in services_str.split('|') if s.strip()]

def validate_store_row(row: dict, row_number: int) -> Tuple[bool, Optional[str]]:
    """Validate a single store row."""
    required_fields = [
        'store_id', 'name', 'store_type', 'status', 'address_street',
        'address_city', 'address_state', 'address_postal_code', 'address_country', 'phone'
    ]
    
    for field in required_fields:
        if not row.get(field):
            return False, f"Missing required field: {field}"
    
    # Validate store_type
    try:
        StoreType(row['store_type'])
    except ValueError:
        return False, f"Invalid store_type: {row['store_type']}"
    
    # Validate status
    try:
        StoreStatus(row['status'])
    except ValueError:
        return False, f"Invalid status: {row['status']}"
    
    # Validate coordinates if provided
    if row.get('latitude'):
        try:
            lat = float(row['latitude'])
            if lat < -90 or lat > 90:
                return False, f"Latitude out of range: {lat}"
        except ValueError:
            return False, f"Invalid latitude: {row['latitude']}"
    
    if row.get('longitude'):
        try:
            lon = float(row['longitude'])
            if lon < -180 or lon > 180:
                return False, f"Longitude out of range: {lon}"
        except ValueError:
            return False, f"Invalid longitude: {row['longitude']}"
    
    # Validate hours
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    for day in days:
        hours_field = f'hours_{day}'
        if hours_field in row and row[hours_field]:
            if not validate_hours(row[hours_field]):
                return False, f"Invalid hours format for {day}: {row[hours_field]}"
    
    return True, None

def process_csv_import(
    csv_content: str,
    db: Session,
    redis_client: redis.Redis
) -> ImportReport:
    """Process CSV import and return import report."""
    reader = csv.DictReader(io.StringIO(csv_content))
    
    results: List[ImportResult] = []
    created_count = 0
    updated_count = 0
    failed_count = 0
    
    # Validate CSV headers
    required_headers = [
        'store_id', 'name', 'store_type', 'status', 'latitude', 'longitude',
        'address_street', 'address_city', 'address_state', 'address_postal_code',
        'address_country', 'phone', 'services', 'hours_mon', 'hours_tue',
        'hours_wed', 'hours_thu', 'hours_fri', 'hours_sat', 'hours_sun'
    ]
    
    if not reader.fieldnames:
        raise ValueError("CSV file is empty or invalid")
    
    missing_headers = [h for h in required_headers if h not in reader.fieldnames]
    if missing_headers:
        raise ValueError(f"Missing required headers: {', '.join(missing_headers)}")
    
    # Process each row
    for row_number, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
        # Validate row
        is_valid, error = validate_store_row(row, row_number)
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
        
        try:
            # Check if store exists
            existing_store = db.query(Store).filter(Store.store_id == store_id).first()
            
            # Get or create coordinates
            latitude = None
            longitude = None
            
            if row.get('latitude') and row.get('longitude'):
                latitude = float(row['latitude'])
                longitude = float(row['longitude'])
            elif row.get('address_street') and row.get('address_city'):
                # Geocode address
                address = f"{row['address_street']}, {row['address_city']}, {row['address_state']} {row['address_postal_code']}"
                coords = get_coordinates_from_address(address, redis_client)
                if coords:
                    latitude = coords['latitude']
                    longitude = coords['longitude']
                else:
                    results.append(ImportResult(
                        row_number=row_number,
                        store_id=store_id,
                        status="failed",
                        error="Could not geocode address"
                    ))
                    failed_count += 1
                    continue
            else:
                results.append(ImportResult(
                    row_number=row_number,
                    store_id=store_id,
                    status="failed",
                    error="Missing coordinates and address"
                ))
                failed_count += 1
                continue
            
            # Parse services
            services_list = parse_services(row.get('services', ''))
            
            if existing_store:
                # Update existing store
                existing_store.name = row['name']
                existing_store.store_type = StoreType(row['store_type'])
                existing_store.status = StoreStatus(row['status'])
                existing_store.latitude = latitude
                existing_store.longitude = longitude
                existing_store.address_street = row['address_street']
                existing_store.address_city = row['address_city']
                existing_store.address_state = row['address_state']
                existing_store.address_postal_code = row['address_postal_code']
                existing_store.address_country = row['address_country']
                existing_store.phone = row['phone']
                existing_store.hours_mon = row.get('hours_mon', 'closed')
                existing_store.hours_tue = row.get('hours_tue', 'closed')
                existing_store.hours_wed = row.get('hours_wed', 'closed')
                existing_store.hours_thu = row.get('hours_thu', 'closed')
                existing_store.hours_fri = row.get('hours_fri', 'closed')
                existing_store.hours_sat = row.get('hours_sat', 'closed')
                existing_store.hours_sun = row.get('hours_sun', 'closed')
                
                # Update services
                existing_store.services.clear()
                for service_name in services_list:
                    service = db.query(Service).filter(Service.name == service_name).first()
                    if not service:
                        service = Service(service_id=f"SVC_{service_name}", name=service_name)
                        db.add(service)
                    existing_store.services.append(service)
                
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
                    store_type=StoreType(row['store_type']),
                    status=StoreStatus(row['status']),
                    latitude=latitude,
                    longitude=longitude,
                    address_street=row['address_street'],
                    address_city=row['address_city'],
                    address_state=row['address_state'],
                    address_postal_code=row['address_postal_code'],
                    address_country=row['address_country'],
                    phone=row['phone'],
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
                    service = db.query(Service).filter(Service.name == service_name).first()
                    if not service:
                        service = Service(service_id=f"SVC_{service_name}", name=service_name)
                        db.add(service)
                    new_store.services.append(service)
                
                db.add(new_store)
                created_count += 1
                results.append(ImportResult(
                    row_number=row_number,
                    store_id=store_id,
                    status="created"
                ))
            
        except Exception as e:
            results.append(ImportResult(
                row_number=row_number,
                store_id=store_id,
                status="failed",
                error=str(e)
            ))
            failed_count += 1
    
    return ImportReport(
        total_rows=len(results),
        created=created_count,
        updated=updated_count,
        failed=failed_count,
        results=results
    )

