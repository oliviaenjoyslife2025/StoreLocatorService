from sqlalchemy import Index
from database import engine
from models import Store, User, RefreshToken

def create_indexes():
    """Create required indexes for database optimization."""
    
    # Composite index for geographic search
    Index('idx_stores_lat_lon', Store.latitude, Store.longitude).create(engine, checkfirst=True)
    
    # Partial index for active stores (PostgreSQL specific)
    # Note: SQLAlchemy doesn't directly support partial indexes, 
    # but we can create a regular index on status
    Index('idx_stores_status', Store.status).create(engine, checkfirst=True)
    
    # Index on store_type (already has index=True in model, but explicit for clarity)
    Index('idx_stores_store_type', Store.store_type).create(engine, checkfirst=True)
    
    # Index on address_postal_code (already has index=True in model)
    # Index('idx_stores_postal_code', Store.address_postal_code).create(engine, checkfirst=True)
    
    # Index on users.email (already has index=True in model)
    # Index('idx_users_email', User.email).create(engine, checkfirst=True)
    
    # Index on refresh_tokens.token_hash (already has index=True in model)
    # Index('idx_refresh_tokens_hash', RefreshToken.token_hash).create(engine, checkfirst=True)
    
    print("Indexes created successfully!")

if __name__ == "__main__":
    create_indexes()

