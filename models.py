from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, Table, Boolean, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

class StoreType(str, enum.Enum):
    flagship = "flagship"
    regular = "regular"
    outlet = "outlet"
    express = "express"

class StoreStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    temporarily_closed = "temporarily_closed"

# Association table for many-to-many relationship between Store and Service
store_service_association = Table(
    'store_service_association',
    Base.metadata,
    Column('store_id', String, ForeignKey('stores.store_id')),
    Column('service_id', String, ForeignKey('services.service_id'))
)

class Store(Base):
    __tablename__ = "stores"

    store_id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    store_type = Column(Enum(StoreType), default=StoreType.regular)
    status = Column(Enum(StoreStatus), default=StoreStatus.active)
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)
    address_street = Column(String)
    address_city = Column(String)
    address_state = Column(String)
    address_postal_code = Column(String, index=True)
    address_country = Column(String)
    phone = Column(String)
    hours_mon = Column(String)
    hours_tue = Column(String)
    hours_wed = Column(String)
    hours_thu = Column(String)
    hours_fri = Column(String)
    hours_sat = Column(String)
    hours_sun = Column(String)
    # Many-to-many relationship with Service
    services = relationship("Service", secondary=store_service_association, back_populates="stores")

class Service(Base):
    __tablename__ = "services"

    service_id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    stores = relationship("Store", secondary=store_service_association, back_populates="services")

# Association table for many-to-many relationship between Role and Permission
role_permission_association = Table(
    'role_permission_association',
    Base.metadata,
    Column('role_id', String, ForeignKey('roles.role_id')),
    Column('permission_id', String, ForeignKey('permissions.permission_id'))
)

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role_id = Column(String, ForeignKey('roles.role_id'), nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    role = relationship("Role", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class Role(Base):
    __tablename__ = "roles"
    
    role_id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    
    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary=role_permission_association, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"
    
    permission_id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    resource = Column(String, nullable=False)
    action = Column(String, nullable=False)
    
    roles = relationship("Role", secondary=role_permission_association, back_populates="permissions")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    token_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    revoked = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="refresh_tokens")

