import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import redis

from models import Base
from main import app
from database import get_db, get_redis_client
from config import settings

# Test database URL (use SQLite for testing)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")

# Create test engine
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Mock Redis client for testing
class MockRedis:
    def __init__(self):
        self._data = {}
    
    def get(self, key):
        return self._data.get(key)
    
    def setex(self, key, time, value):
        self._data[key] = value
        return True
    
    def incr(self, key):
        if key not in self._data:
            self._data[key] = 0
        self._data[key] += 1
        return self._data[key]
    
    def expire(self, key, time):
        return True
    
    def pipeline(self):
        class MockPipeline:
            def __init__(self, redis):
                self.redis = redis
                self.commands = []
            
            def __enter__(self):
                return self
            
            def __exit__(self, *args):
                pass
            
            def incr(self, key):
                self.commands.append(('incr', key))
                return self
            
            def expire(self, key, time):
                self.commands.append(('expire', key, time))
                return self
            
            def execute(self):
                results = []
                for cmd in self.commands:
                    if cmd[0] == 'incr':
                        results.append(self.redis.incr(cmd[1]))
                    elif cmd[0] == 'expire':
                        results.append(self.redis.expire(cmd[1], cmd[2]))
                return results
        
        return MockPipeline(self)

mock_redis = MockRedis()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    def override_get_redis():
        yield mock_redis
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_geocoding():
    """Mock geocoding service."""
    with patch('geocoding_service.get_coordinates_from_address') as mock_addr, \
         patch('geocoding_service.get_coordinates_from_postal_code') as mock_postal:
        mock_addr.return_value = {"latitude": 42.3601, "longitude": -71.0589}
        mock_postal.return_value = {"latitude": 42.3601, "longitude": -71.0589}
        yield mock_addr, mock_postal

