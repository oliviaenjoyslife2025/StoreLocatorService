from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from models import Base
import redis

# Database connection URL from settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Create the SQLAlchemy engine
# echo=True will log all SQL statements, useful for debugging
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis connection
redis_kwargs = {
    "host": settings.REDIS_HOST,
    "port": settings.REDIS_PORT,
    "db": 0
}
if settings.REDIS_PASSWORD:
    redis_kwargs["password"] = settings.REDIS_PASSWORD
    # ElastiCache with auth requires SSL
    redis_kwargs["ssl"] = True
    redis_kwargs["ssl_cert_reqs"] = "none"  # ElastiCache uses self-signed certs

redis_client = redis.Redis(**redis_kwargs)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get the Redis client
def get_redis_client():
    yield redis_client

# Function to create all tables (for initial setup, not for migrations)
def create_all_tables():
    Base.metadata.create_all(bind=engine)

