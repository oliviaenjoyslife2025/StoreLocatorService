from fastapi import FastAPI, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
import json
from collections import defaultdict
import redis
from datetime import timedelta

from schemas import (
    SearchRequest, SearchResultsResponse, StoreResponse, SearchMetadata, StoreTypeEnum, SearchFilters,
    LoginRequest, TokenResponse, RefreshTokenRequest, AccessTokenResponse,
    StoreCreate, StoreUpdate, StoreListResponse,
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    ImportReport
)
from database import get_db, get_redis_client, create_all_tables
from geocoding_service import get_coordinates_from_address, get_coordinates_from_postal_code
from distance_calculator import calculate_bounding_box, calculate_distance
from models import Store, Service, StoreType, StoreStatus, User, RefreshToken, Role
from rate_limiter import rate_limit
from config import settings
from auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    hash_token, verify_token_hash, get_current_user
)
from permissions import require_admin, require_admin_or_marketer, require_viewer_or_above
from csv_import import process_csv_import
from init_db import init_roles_and_permissions, create_default_admin
from database import SessionLocal

app = FastAPI(
    title="Store Locator Service",
    description="API service for multi-location retail business",
    version="1.0.0",
)

@app.on_event("startup")
def on_startup():
    create_all_tables()
    db = SessionLocal()
    try:
        init_roles_and_permissions(db)
        create_default_admin(db)
    finally:
        db.close()

@app.get("/", tags=["Health Check"])
async def root(current_user: User = Depends(require_viewer_or_above)):
    return {"message": f"Welcome to the Store Locator Service, {current_user.email}!"}

def is_store_open(store: Store) -> bool:
    """
    Checks if a store is currently open based on its operating hours.
    """
    if store.status != StoreStatus.active:
        return False

    now = datetime.datetime.now(datetime.timezone.utc).astimezone() # Get local time with timezone info
    current_day = now.strftime('%a').lower() # e.g., 'mon', 'tue'

    hours_field_name = f"hours_{current_day}"
    hours_str = getattr(store, hours_field_name, "closed")

    if hours_str == "closed":
        return False

    try:
        open_time_str, close_time_str = hours_str.split('-')
        open_time = datetime.datetime.strptime(open_time_str, '%H:%M').time()
        close_time = datetime.datetime.strptime(close_time_str, '%H:%M').time()

        current_time = now.time()

        if open_time <= close_time:
            return open_time <= current_time < close_time
        else: # Overnight hours, e.g., 22:00-06:00
            return current_time >= open_time or current_time < close_time
    except ValueError:
        return False 

@app.post("/api/stores/search", response_model=SearchResultsResponse, tags=["Store Search"], dependencies=[Depends(rate_limit)])
async def search_stores(
    request: SearchRequest,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    # Generate a cache key based on the request (location and filters)
    cache_key = f"search:{request.model_dump_json()}"
    print(f"Cache key: {cache_key}")
    cached_response = redis_client.get(cache_key)
    print(f"Cached response: {cached_response}")
    if cached_response:
        print(f"Cache hit for search: {cache_key}")
        return SearchResultsResponse.model_validate_json(cached_response)

    search_lat: Optional[float] = None
    search_lon: Optional[float] = None

    # Determine search coordinates
    if request.location.latitude is not None and request.location.longitude is not None:
        search_lat = request.location.latitude
        search_lon = request.location.longitude
    elif request.location.address:
        coords = get_coordinates_from_address(request.location.address, redis_client)
        if not coords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not geocode address: {request.location.address}"
            )
        search_lat = coords["latitude"]
        search_lon = coords["longitude"]
    elif request.location.postal_code:
        coords = get_coordinates_from_postal_code(request.location.postal_code, redis_client)
        if not coords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not geocode postal code: {request.location.postal_code}"
            )
        search_lat = coords["latitude"]
        search_lon = coords["longitude"]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either latitude/longitude, address, or postal_code must be provided."
        )
    # Default radius from schema: 10.0
    radius_miles = request.filters.radius_miles if request.filters else 10.0 
    
    # Calculate bounding box for initial SQL filter
    bbox = calculate_bounding_box(search_lat, search_lon, radius_miles)

    # Build base query
    query = db.query(Store).filter(
        Store.latitude.between(bbox["min_lat"], bbox["max_lat"]),
        Store.longitude.between(bbox["min_lon"], bbox["max_lon"]),
        Store.status == StoreStatus.active
    )

    # Apply service filter 
    if request.filters and request.filters.services:
        for service_name in request.filters.services:
            query = query.join(Store.services).filter(Service.name == service_name)

    # Apply store_type filter: in_() is used to filter the query by a list of values
    if request.filters and request.filters.store_types:
        query = query.filter(Store.store_type.in_([t.value for t in request.filters.store_types]))

    # Execute query
    potential_stores = query.all()

    # Calculate exact distances and filter by radius
    stores_with_distance = []
    for store in potential_stores:
        distance = calculate_distance(search_lat, search_lon, store.latitude, store.longitude)
        if distance <= radius_miles:
            stores_with_distance.append({
                "store": store,
                "distance": distance
            })

    # Sort by distance
    stores_with_distance.sort(key=lambda x: x["distance"])

    final_stores: List[StoreResponse] = []
    for item in stores_with_distance:
        store = item["store"]
        distance = item["distance"]
        is_open = is_store_open(store)

        if request.filters and request.filters.open_now and not is_open:
            continue # Skip if open_now filter is active and store is closed

        # Convert store.services to a list of strings
        service_names = [s.name for s in store.services]
        
        store_response_data = store.__dict__
        store_response_data['services'] = service_names # Replace ORM objects with list of names

        final_stores.append(
            StoreResponse(
                **store_response_data,
                distance=distance,
                is_open_now=is_open
            )
        )
    
    response = SearchResultsResponse(
        data=final_stores,
        metadata=SearchMetadata(
            searched_location=request.location,
            applied_filters=request.filters if request.filters else SearchFilters(),
            total_results=len(final_stores)
        )
    )
    # Cache the search results
    redis_client.setex(
        cache_key,
        datetime.timedelta(minutes=settings.SEARCH_RESULTS_CACHE_TTL_MINUTES),
        response.model_dump_json() # Use model_dump_json to serialize Pydantic model
    )
    print(f"Search results cached for: {cache_key}")
    return response

# Authentication Endpoints
@app.post("/api/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login and get access + refresh tokens."""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Get user role
    role = db.query(Role).filter(Role.role_id == user.role_id).first()
    
    # Create access token
    access_token_data = {
        "user_id": user.user_id,
        "email": user.email,
        "role": role.name if role else "viewer"
    }
    access_token = create_access_token(access_token_data)
    
    # Create refresh token
    refresh_token = create_refresh_token()
    token_hash = hash_token(refresh_token)
    
    # Store refresh token
    refresh_token_obj = RefreshToken(
        token_id=f"RT_{user.user_id}_{datetime.datetime.utcnow().timestamp()}",
        user_id=user.user_id,
        token_hash=token_hash,
        expires_at=datetime.datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(refresh_token_obj)
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@app.post("/api/auth/refresh", response_model=AccessTokenResponse, tags=["Authentication"])
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    # Find refresh token
    refresh_tokens = db.query(RefreshToken).filter(RefreshToken.revoked == False).all()
    
    for token_obj in refresh_tokens:
        if verify_token_hash(request.refresh_token, token_obj.token_hash):
            # Check if token is expired
            if token_obj.expires_at < datetime.datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has expired"
                )
            
            # Get user
            user = db.query(User).filter(User.user_id == token_obj.user_id).first()
            if not user or user.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Get role
            role = db.query(Role).filter(Role.role_id == user.role_id).first()
            
            # Create new access token
            access_token_data = {
                "user_id": user.user_id,
                "email": user.email,
                "role": role.name if role else "viewer"
            }
            access_token = create_access_token(access_token_data)
            
            return AccessTokenResponse(access_token=access_token)
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token"
    )

@app.post("/api/auth/logout", tags=["Authentication"])
async def logout(
    request: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke refresh token."""
    refresh_tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.user_id,
        RefreshToken.revoked == False
    ).all()
    
    for token_obj in refresh_tokens:
        if verify_token_hash(request.refresh_token, token_obj.token_hash):
            token_obj.revoked = True
            db.commit()
            return {"message": "Logged out successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid refresh token"
    )

# Store Management Endpoints (CRUD)
@app.post("/api/admin/stores", response_model=StoreResponse, tags=["Store Management"])
async def create_store(
    store_data: StoreCreate,
    current_user: User = Depends(require_admin_or_marketer),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Create a new store."""
    # Check if store_id already exists
    existing = db.query(Store).filter(Store.store_id == store_data.store_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Store with ID {store_data.store_id} already exists"
        )
    
    # Get or geocode coordinates
    latitude = store_data.latitude
    longitude = store_data.longitude
    
    # Validate: either coordinates or complete address must be provided
    has_coords = latitude is not None and longitude is not None
    has_address = all([
        store_data.address_street,
        store_data.address_city,
        store_data.address_state,
        store_data.address_postal_code
    ])
    
    if not has_coords and not has_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either coordinates (latitude, longitude) or complete address must be provided"
        )
    
    if not latitude or not longitude:
        if has_address:
            address = f"{store_data.address_street}, {store_data.address_city}, {store_data.address_state} {store_data.address_postal_code}"
            coords = get_coordinates_from_address(address, redis_client)
            if not coords:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not geocode address and coordinates not provided"
                )
            latitude = coords["latitude"]
            longitude = coords["longitude"]
    
    # Create store
    new_store = Store(
        store_id=store_data.store_id,
        name=store_data.name,
        store_type=StoreType(store_data.store_type.value),
        status=StoreStatus(store_data.status.value),
        latitude=latitude,
        longitude=longitude,
        address_street=store_data.address_street,
        address_city=store_data.address_city,
        address_state=store_data.address_state,
        address_postal_code=store_data.address_postal_code,
        address_country=store_data.address_country,
        phone=store_data.phone,
        hours_mon=store_data.hours_mon,
        hours_tue=store_data.hours_tue,
        hours_wed=store_data.hours_wed,
        hours_thu=store_data.hours_thu,
        hours_fri=store_data.hours_fri,
        hours_sat=store_data.hours_sat,
        hours_sun=store_data.hours_sun
    )
    
    # Add services
    for service_name in store_data.services:
        service = db.query(Service).filter(Service.name == service_name).first()
        if not service:
            service = Service(service_id=f"SVC_{service_name}", name=service_name)
            db.add(service)
        new_store.services.append(service)
    
    db.add(new_store)
    db.commit()
    db.refresh(new_store)
    
    service_names = [s.name for s in new_store.services]
    store_dict = new_store.__dict__
    store_dict['services'] = service_names
    
    return StoreResponse(**store_dict)

@app.get("/api/admin/stores", response_model=StoreListResponse, tags=["Store Management"])
async def list_stores(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    """List stores with pagination."""
    offset = (page - 1) * page_size
    
    total = db.query(Store).count()
    stores = db.query(Store).offset(offset).limit(page_size).all()
    
    store_responses = []
    for store in stores:
        service_names = [s.name for s in store.services]
        store_dict = store.__dict__
        store_dict['services'] = service_names
        store_responses.append(StoreResponse(**store_dict))
    
    total_pages = (total + page_size - 1) // page_size
    
    return StoreListResponse(
        data=store_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@app.get("/api/admin/stores/{store_id}", response_model=StoreResponse, tags=["Store Management"])
async def get_store(
    store_id: str,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    """Get store details by ID."""
    store = db.query(Store).filter(Store.store_id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found"
        )
    
    service_names = [s.name for s in store.services]
    store_dict = store.__dict__
    store_dict['services'] = service_names
    
    return StoreResponse(**store_dict)

@app.patch("/api/admin/stores/{store_id}", response_model=StoreResponse, tags=["Store Management"])
async def update_store(
    store_id: str,
    store_update: StoreUpdate,
    current_user: User = Depends(require_admin_or_marketer),
    db: Session = Depends(get_db)
):
    """Partially update a store."""
    store = db.query(Store).filter(Store.store_id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found"
        )
    
    # Update allowed fields
    update_data = store_update.model_dump(exclude_unset=True)
    
    if "name" in update_data:
        store.name = update_data["name"]
    if "phone" in update_data:
        store.phone = update_data["phone"]
    if "status" in update_data:
        store.status = StoreStatus(update_data["status"].value)
    if "services" in update_data:
        store.services.clear()
        for service_name in update_data["services"]:
            service = db.query(Service).filter(Service.name == service_name).first()
            if not service:
                service = Service(service_id=f"SVC_{service_name}", name=service_name)
                db.add(service)
            store.services.append(service)
    
    # Update hours
    for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
        hours_field = f"hours_{day}"
        if hours_field in update_data:
            setattr(store, hours_field, update_data[hours_field])
    
    db.commit()
    db.refresh(store)
    
    service_names = [s.name for s in store.services]
    store_dict = store.__dict__
    store_dict['services'] = service_names
    
    return StoreResponse(**store_dict)

@app.delete("/api/admin/stores/{store_id}", tags=["Store Management"])
async def delete_store(
    store_id: str,
    current_user: User = Depends(require_admin_or_marketer),
    db: Session = Depends(get_db)
):
    """Deactivate a store (soft delete)."""
    store = db.query(Store).filter(Store.store_id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found"
        )
    
    store.status = StoreStatus.inactive
    db.commit()
    
    return {"message": f"Store {store_id} has been deactivated"}

# Batch CSV Import
@app.post("/api/admin/stores/import", response_model=ImportReport, tags=["Store Management"])
async def import_stores_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin_or_marketer),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Import stores from CSV file."""
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )
    
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    try:
        report = process_csv_import(csv_content, db, redis_client)
        db.commit()
        return report
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV validation error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV: {str(e)}"
        )
 
# User Management (Admin Only)
@app.post("/api/admin/users", response_model=UserResponse, tags=["User Management"])
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (Admin only)."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_data.email} already exists"
        )
    
    # Map role name to role_id
    role = db.query(Role).filter(Role.name == user_data.role.value).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {user_data.role.value}"
        )
    
    new_user = User(
        user_id=user_data.user_id,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role_id=role.role_id,
        status="active"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        user_id=new_user.user_id,
        email=new_user.email,
        role=role.name,
        status=new_user.status,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
    )

@app.get("/api/admin/users", response_model=UserListResponse, tags=["User Management"])
async def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (Admin only)."""
    users = db.query(User).all()
    
    user_responses = []
    for user in users:
        role = db.query(Role).filter(Role.role_id == user.role_id).first()
        user_responses.append(UserResponse(
            user_id=user.user_id,
            email=user.email,
            role=role.name if role else "unknown",
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at
        ))
    
    return UserListResponse(
        data=user_responses,
        total=len(user_responses)
    )

@app.put("/api/admin/users/{user_id}", response_model=UserResponse, tags=["User Management"])
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user (role, status) (Admin only)."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "role" in update_data:
        role = db.query(Role).filter(Role.name == update_data["role"].value).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {update_data['role'].value}"
            )
        user.role_id = role.role_id
    
    if "status" in update_data:
        user.status = update_data["status"].value
    
    db.commit()
    db.refresh(user)
    
    role = db.query(Role).filter(Role.role_id == user.role_id).first()
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        role=role.name if role else "unknown",
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@app.delete("/api/admin/users/{user_id}", tags=["User Management"])
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate a user (Admin only)."""
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    user.status = "inactive"
    db.commit()
    
    return {"message": f"User {user_id} has been deactivated"}
