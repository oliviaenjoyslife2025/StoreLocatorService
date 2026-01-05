import pytest
from fastapi import status
from models import Store, Service, User, Role, StoreType, StoreStatus
from auth import hash_password

class TestSearchAPI:
    """API tests for store search functionality."""
    
    def test_search_by_coordinates(self, client, db_session):
        """Test search by latitude and longitude."""
        # Create test store
        store = Store(
            store_id="S0001",
            name="Test Store",
            store_type=StoreType.regular,
            status=StoreStatus.active,
            latitude=42.3601,
            longitude=-71.0589,
            address_street="123 Main St",
            address_city="Boston",
            address_state="MA",
            address_postal_code="02101",
            address_country="USA",
            phone="617-555-0100",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="09:00-21:00",
            hours_sun="10:00-20:00"
        )
        db_session.add(store)
        db_session.commit()
        
        # Search by coordinates
        response = client.post("/api/stores/search", json={
            "location": {
                "latitude": 42.3601,
                "longitude": -71.0589
            },
            "filters": {
                "radius_miles": 10.0
            }
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        assert data["data"][0]["store_id"] == "S0001"
        assert "distance" in data["data"][0]
    
    def test_search_by_address(self, client, db_session, mock_geocoding):
        """Test search by address with geocoding."""
        # Create test store
        store = Store(
            store_id="S0002",
            name="Test Store 2",
            store_type=StoreType.regular,
            status=StoreStatus.active,
            latitude=42.3601,
            longitude=-71.0589,
            address_street="123 Main St",
            address_city="Boston",
            address_state="MA",
            address_postal_code="02101",
            address_country="USA",
            phone="617-555-0100",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="09:00-21:00",
            hours_sun="10:00-20:00"
        )
        db_session.add(store)
        db_session.commit()
        
        # Search by address
        response = client.post("/api/stores/search", json={
            "location": {
                "address": "123 Main St, Boston, MA 02101"
            },
            "filters": {
                "radius_miles": 10.0
            }
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
    
    def test_search_by_postal_code(self, client, db_session, mock_geocoding):
        """Test search by postal code."""
        # Create test store
        store = Store(
            store_id="S0003",
            name="Test Store 3",
            store_type=StoreType.regular,
            status=StoreStatus.active,
            latitude=42.3601,
            longitude=-71.0589,
            address_street="123 Main St",
            address_city="Boston",
            address_state="MA",
            address_postal_code="02101",
            address_country="USA",
            phone="617-555-0100",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="09:00-21:00",
            hours_sun="10:00-20:00"
        )
        db_session.add(store)
        db_session.commit()
        
        # Search by postal code
        response = client.post("/api/stores/search", json={
            "location": {
                "postal_code": "02101"
            },
            "filters": {
                "radius_miles": 10.0
            }
        })
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_search_filter_by_services(self, client, db_session):
        """Test search with service filter."""
        # Create service
        service = Service(service_id="SVC_pharmacy", name="pharmacy")
        db_session.add(service)
        
        # Create store with service
        store = Store(
            store_id="S0004",
            name="Pharmacy Store",
            store_type=StoreType.regular,
            status=StoreStatus.active,
            latitude=42.3601,
            longitude=-71.0589,
            address_street="123 Main St",
            address_city="Boston",
            address_state="MA",
            address_postal_code="02101",
            address_country="USA",
            phone="617-555-0100",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="09:00-21:00",
            hours_sun="10:00-20:00"
        )
        store.services.append(service)
        db_session.add(store)
        db_session.commit()
        
        # Search with service filter
        response = client.post("/api/stores/search", json={
            "location": {
                "latitude": 42.3601,
                "longitude": -71.0589
            },
            "filters": {
                "radius_miles": 10.0,
                "services": ["pharmacy"]
            }
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if len(data["data"]) > 0:
            assert "pharmacy" in data["data"][0]["services"]
    
    def test_search_filter_by_store_type(self, client, db_session):
        """Test search with store type filter."""
        # Create store
        store = Store(
            store_id="S0005",
            name="Flagship Store",
            store_type=StoreType.flagship,
            status=StoreStatus.active,
            latitude=42.3601,
            longitude=-71.0589,
            address_street="123 Main St",
            address_city="Boston",
            address_state="MA",
            address_postal_code="02101",
            address_country="USA",
            phone="617-555-0100",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="09:00-21:00",
            hours_sun="10:00-20:00"
        )
        db_session.add(store)
        db_session.commit()
        
        # Search with store type filter
        response = client.post("/api/stores/search", json={
            "location": {
                "latitude": 42.3601,
                "longitude": -71.0589
            },
            "filters": {
                "radius_miles": 10.0,
                "store_types": ["flagship"]
            }
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if len(data["data"]) > 0:
            assert data["data"][0]["store_type"] == "flagship"

class TestAuthenticationAPI:
    """API tests for authentication."""
    
    def test_login_success(self, client, db_session):
        """Test successful login."""
        # Create role
        role = Role(role_id="R001", name="admin", description="Admin role")
        db_session.add(role)
        db_session.commit()
        
        # Create user
        user = User(
            user_id="U001",
            email="admin@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id="R001",
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        response = client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "TestPassword123!"
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_incorrect_password(self, client, db_session):
        """Test login with incorrect password."""
        # Create role and user
        role = Role(role_id="R001", name="admin", description="Admin role")
        db_session.add(role)
        user = User(
            user_id="U001",
            email="admin@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id="R001",
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        
        # Login with wrong password
        response = client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "WrongPassword"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token(self, client, db_session):
        """Test token refresh."""
        # Create role and user
        role = Role(role_id="R001", name="admin", description="Admin role")
        db_session.add(role)
        user = User(
            user_id="U001",
            email="admin@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id="R001",
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        
        # Login first
        login_response = client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "TestPassword123!"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data

class TestAuthorizationAPI:
    """API tests for role-based authorization."""
    
    def test_admin_can_create_store(self, client, db_session):
        """Test that admin can create store."""
        # Create role
        role = Role(role_id="R001", name="admin", description="Admin role")
        db_session.add(role)
        db_session.commit()
        
        # Create admin user
        user = User(
            user_id="U001",
            email="admin@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id="R001",
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "TestPassword123!"
        })
        access_token = login_response.json()["access_token"]
        
        # Create store
        response = client.post(
            "/api/admin/stores",
            json={
                "store_id": "S0010",
                "name": "New Store",
                "store_type": "regular",
                "status": "active",
                "latitude": 42.3601,
                "longitude": -71.0589,
                "address_street": "123 Main St",
                "address_city": "Boston",
                "address_state": "MA",
                "address_postal_code": "02101",
                "address_country": "USA",
                "phone": "617-555-0100",
                "services": [],
                "hours_mon": "08:00-22:00",
                "hours_tue": "08:00-22:00",
                "hours_wed": "08:00-22:00",
                "hours_thu": "08:00-22:00",
                "hours_fri": "08:00-22:00",
                "hours_sat": "09:00-21:00",
                "hours_sun": "10:00-20:00"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_viewer_cannot_create_store(self, client, db_session):
        """Test that viewer cannot create store."""
        # Create viewer role
        role = Role(role_id="R003", name="viewer", description="Viewer role")
        db_session.add(role)
        db_session.commit()
        
        # Create viewer user
        user = User(
            user_id="U003",
            email="viewer@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id="R003",
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "viewer@test.com",
            "password": "TestPassword123!"
        })
        access_token = login_response.json()["access_token"]
        
        # Try to create store (should fail)
        response = client.post(
            "/api/admin/stores",
            json={
                "store_id": "S0011",
                "name": "New Store",
                "store_type": "regular",
                "status": "active",
                "latitude": 42.3601,
                "longitude": -71.0589,
                "address_street": "123 Main St",
                "address_city": "Boston",
                "address_state": "MA",
                "address_postal_code": "02101",
                "address_country": "USA",
                "phone": "617-555-0100",
                "services": [],
                "hours_mon": "08:00-22:00",
                "hours_tue": "08:00-22:00",
                "hours_wed": "08:00-22:00",
                "hours_thu": "08:00-22:00",
                "hours_fri": "08:00-22:00",
                "hours_sat": "09:00-21:00",
                "hours_sun": "10:00-20:00"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

class TestCRUDOperations:
    """API tests for CRUD operations."""
    
    def test_create_store(self, client, db_session):
        """Test creating a store."""
        # Setup: Create role and admin user
        role = Role(role_id="R001", name="admin", description="Admin role")
        db_session.add(role)
        user = User(
            user_id="U001",
            email="admin@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id="R001",
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "TestPassword123!"
        })
        access_token = login_response.json()["access_token"]
        
        # Create store
        response = client.post(
            "/api/admin/stores",
            json={
                "store_id": "S0020",
                "name": "Test Store CRUD",
                "store_type": "regular",
                "status": "active",
                "latitude": 42.3601,
                "longitude": -71.0589,
                "address_street": "123 Main St",
                "address_city": "Boston",
                "address_state": "MA",
                "address_postal_code": "02101",
                "address_country": "USA",
                "phone": "617-555-0100",
                "services": ["pharmacy"],
                "hours_mon": "08:00-22:00",
                "hours_tue": "08:00-22:00",
                "hours_wed": "08:00-22:00",
                "hours_thu": "08:00-22:00",
                "hours_fri": "08:00-22:00",
                "hours_sat": "09:00-21:00",
                "hours_sun": "10:00-20:00"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["store_id"] == "S0020"
        assert data["name"] == "Test Store CRUD"
    
    def test_get_store(self, client, db_session):
        """Test getting a store by ID."""
        # Create store
        store = Store(
            store_id="S0021",
            name="Test Store Get",
            store_type=StoreType.regular,
            status=StoreStatus.active,
            latitude=42.3601,
            longitude=-71.0589,
            address_street="123 Main St",
            address_city="Boston",
            address_state="MA",
            address_postal_code="02101",
            address_country="USA",
            phone="617-555-0100",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="09:00-21:00",
            hours_sun="10:00-20:00"
        )
        db_session.add(store)
        db_session.commit()
        
        # Setup: Create role and user
        role = Role(role_id="R001", name="admin", description="Admin role")
        db_session.add(role)
        user = User(
            user_id="U001",
            email="admin@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id="R001",
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "TestPassword123!"
        })
        access_token = login_response.json()["access_token"]
        
        # Get store
        response = client.get(
            "/api/admin/stores/S0021",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["store_id"] == "S0021"
    
    def test_update_store(self, client, db_session):
        """Test updating a store."""
        # Create store
        store = Store(
            store_id="S0022",
            name="Test Store Update",
            store_type=StoreType.regular,
            status=StoreStatus.active,
            latitude=42.3601,
            longitude=-71.0589,
            address_street="123 Main St",
            address_city="Boston",
            address_state="MA",
            address_postal_code="02101",
            address_country="USA",
            phone="617-555-0100",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="09:00-21:00",
            hours_sun="10:00-20:00"
        )
        db_session.add(store)
        db_session.commit()
        
        # Setup: Create role and user
        role = Role(role_id="R001", name="admin", description="Admin role")
        db_session.add(role)
        user = User(
            user_id="U001",
            email="admin@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id="R001",
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "TestPassword123!"
        })
        access_token = login_response.json()["access_token"]
        
        # Update store
        response = client.patch(
            "/api/admin/stores/S0022",
            json={
                "name": "Updated Store Name",
                "phone": "617-555-9999"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Store Name"
        assert data["phone"] == "617-555-9999"
    
    def test_delete_store(self, client, db_session):
        """Test deleting (deactivating) a store."""
        # Create store
        store = Store(
            store_id="S0023",
            name="Test Store Delete",
            store_type=StoreType.regular,
            status=StoreStatus.active,
            latitude=42.3601,
            longitude=-71.0589,
            address_street="123 Main St",
            address_city="Boston",
            address_state="MA",
            address_postal_code="02101",
            address_country="USA",
            phone="617-555-0100",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="09:00-21:00",
            hours_sun="10:00-20:00"
        )
        db_session.add(store)
        db_session.commit()
        
        # Setup: Create role and user
        role = Role(role_id="R001", name="admin", description="Admin role")
        db_session.add(role)
        user = User(
            user_id="U001",
            email="admin@test.com",
            password_hash=hash_password("TestPassword123!"),
            role_id="R001",
            status="active"
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "TestPassword123!"
        })
        access_token = login_response.json()["access_token"]
        
        # Delete store
        response = client.delete(
            "/api/admin/stores/S0023",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify store is deactivated
        db_session.refresh(store)
        assert store.status == StoreStatus.inactive

