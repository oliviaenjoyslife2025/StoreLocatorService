from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import time, datetime
from enum import Enum

# Enum for StoreType, matching models.py
class StoreTypeEnum(str, Enum):
    flagship = "flagship"
    regular = "regular"
    outlet = "outlet"
    express = "express"

# Enum for StoreStatus, matching models.py
class StoreStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    temporarily_closed = "temporarily_closed"

class StoreBase(BaseModel):
    store_id: str
    name: str
    store_type: StoreTypeEnum
    status: StoreStatusEnum
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address_street: str
    address_city: str
    address_state: str
    address_postal_code: str
    address_country: str
    phone: str
    services: List[str]
    hours_mon: str
    hours_tue: str
    hours_wed: str
    hours_thu: str
    hours_fri: str
    hours_sat: str
    hours_sun: str

class StoreResponse(StoreBase):
    distance: Optional[float] = None
    is_open_now: Optional[bool] = None

    class Config:
        from_attributes = True # Allow ORM models to be converted to Pydantic models

class SearchLocation(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = None
    postal_code: Optional[str] = None

    class Config:
        extra = "forbid" # Forbid extra fields

class SearchFilters(BaseModel):
    radius_miles: float = Field(10.0, gt=0, le=100)
    services: Optional[List[str]] = Field(None)
    store_types: Optional[List[StoreTypeEnum]] = Field(None)
    open_now: Optional[bool] = False

class SearchRequest(BaseModel):
    location: SearchLocation
    filters: Optional[SearchFilters] = Field(default_factory=SearchFilters)

class SearchMetadata(BaseModel):
    searched_location: SearchLocation
    applied_filters: SearchFilters
    total_results: int

class SearchResultsResponse(BaseModel):
    data: List[StoreResponse]
    metadata: SearchMetadata

# Authentication Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Store Management Schemas
class StoreCreate(BaseModel):
    store_id: str
    name: str
    store_type: StoreTypeEnum
    status: StoreStatusEnum = StoreStatusEnum.active
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = "USA"
    phone: str
    services: List[str] = []
    hours_mon: str = "closed"
    hours_tue: str = "closed"
    hours_wed: str = "closed"
    hours_thu: str = "closed"
    hours_fri: str = "closed"
    hours_sat: str = "closed"
    hours_sun: str = "closed"

class StoreUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    services: Optional[List[str]] = None
    status: Optional[StoreStatusEnum] = None
    hours_mon: Optional[str] = None
    hours_tue: Optional[str] = None
    hours_wed: Optional[str] = None
    hours_thu: Optional[str] = None
    hours_fri: Optional[str] = None
    hours_sat: Optional[str] = None
    hours_sun: Optional[str] = None

class StoreListResponse(BaseModel):
    data: List[StoreResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# User Management Schemas
class UserRoleEnum(str, Enum):
    admin = "admin"
    marketer = "marketer"
    viewer = "viewer"

class UserStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"

class UserCreate(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: UserRoleEnum = UserRoleEnum.viewer

class UserUpdate(BaseModel):
    role: Optional[UserRoleEnum] = None
    status: Optional[UserStatusEnum] = None

class UserResponse(BaseModel):
    user_id: str
    email: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    data: List[UserResponse]
    total: int

# CSV Import Schemas
class ImportResult(BaseModel):
    row_number: int
    store_id: str
    status: str
    error: Optional[str] = None

class ImportReport(BaseModel):
    total_rows: int
    created: int
    updated: int
    failed: int
    results: List[ImportResult]
