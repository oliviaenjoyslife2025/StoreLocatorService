import pytest
from fastapi import status
from models import Store, Service, User, Role, StoreType, StoreStatus
from auth import hash_password
from unittest.mock import patch

class TestEndToEndSearch:
    """Integration tests for end-to-end search flow."""
    
    def test_end_to_end_search_flow(self, client, db_session, mock_geocoding):
        """Test complete search flow from address to results."""
        # Create multiple stores
        stores = [
            Store(
                store_id=f"S{i:04d}",
                name=f"Store {i}",
                store_type=StoreType.regular,
                status=StoreStatus.active,
                latitude=42.3601 + (i * 0.01),
                longitude=-71.0589 + (i * 0.01),
                address_street=f"{i} Main St",
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
            for i in range(1, 6)
        ]
        for store in stores:
            db_session.add(store)
        db_session.commit()
        
        # Search by address (will be geocoded)
        response = client.post("/api/stores/search", json={
            "location": {
                "address": "123 Main St, Boston, MA 02101"
            },
            "filters": {
                "radius_miles": 50.0
            }
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "metadata" in data
        assert len(data["data"]) > 0
        # Results should be sorted by distance
        distances = [store["distance"] for store in data["data"]]
        assert distances == sorted(distances)
    
    def test_search_with_multiple_filters(self, client, db_session):
        """Test search with multiple filters applied."""
        # Create service
        service = Service(service_id="SVC_pharmacy", name="pharmacy")
        db_session.add(service)
        
        # Create stores with different types and services
        store1 = Store(
            store_id="S0101",
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
        store1.services.append(service)
        
        store2 = Store(
            store_id="S0102",
            name="Flagship Store",
            store_type=StoreType.flagship,
            status=StoreStatus.active,
            latitude=42.3601,
            longitude=-71.0589,
            address_street="456 Main St",
            address_city="Boston",
            address_state="MA",
            address_postal_code="02101",
            address_country="USA",
            phone="617-555-0200",
            hours_mon="08:00-22:00",
            hours_tue="08:00-22:00",
            hours_wed="08:00-22:00",
            hours_thu="08:00-22:00",
            hours_fri="08:00-22:00",
            hours_sat="09:00-21:00",
            hours_sun="10:00-20:00"
        )
        
        db_session.add(store1)
        db_session.add(store2)
        db_session.commit()
        
        # Search with multiple filters
        response = client.post("/api/stores/search", json={
            "location": {
                "latitude": 42.3601,
                "longitude": -71.0589
            },
            "filters": {
                "radius_miles": 10.0,
                "services": ["pharmacy"],
                "store_types": ["regular"]
            }
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should only return stores matching all filters
        for store in data["data"]:
            assert store["store_type"] == "regular"
            assert "pharmacy" in store["services"]

class TestAuthenticationFlow:
    """Integration tests for authentication flow."""
    
    def test_authentication_and_protected_endpoint(self, client, db_session):
        """Test complete authentication flow and accessing protected endpoint."""
        # Setup: Create role
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
        
        # Step 1: Login
        login_response = client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "TestPassword123!"
        })
        assert login_response.status_code == status.HTTP_200_OK
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # Step 2: Access protected endpoint with access token
        response = client.get(
            "/api/admin/stores",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Step 3: Refresh access token
        refresh_response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert refresh_response.status_code == status.HTTP_200_OK
        new_access_token = refresh_response.json()["access_token"]
        
        # Step 4: Use new access token
        response2 = client.get(
            "/api/admin/stores",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert response2.status_code == status.HTTP_200_OK
        
        # Step 5: Logout
        logout_response = client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert logout_response.status_code == status.HTTP_200_OK
        
        # Step 6: Try to use refresh token after logout (should fail)
        refresh_after_logout = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert refresh_after_logout.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_unauthorized_access_to_protected_endpoint(self, client, db_session):
        """Test that unauthorized requests are rejected."""
        # Try to access protected endpoint without token
        response = client.get("/api/admin/stores")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Try with invalid token
        response = client.get(
            "/api/admin/stores",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestCSVImportFlow:
    """Integration tests for CSV import with geocoding."""
    
    def test_csv_import_with_geocoding(self, client, db_session, mock_geocoding):
        """Test CSV import that requires geocoding."""
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
        
        # Create CSV content (without coordinates, will need geocoding)
        csv_content = """store_id,name,store_type,status,latitude,longitude,address_street,address_city,address_state,address_postal_code,address_country,phone,services,hours_mon,hours_tue,hours_wed,hours_thu,hours_fri,hours_sat,hours_sun
S1001,Test Import Store,regular,active,,,123 Main St,Boston,MA,02101,USA,617-555-0100,pharmacy|pickup,08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,09:00-21:00,10:00-20:00"""
        
        # Import CSV
        response = client.post(
            "/api/admin/stores/import",
            files={"file": ("test.csv", csv_content, "text/csv")},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_rows"] == 1
        assert data["created"] == 1
        assert data["failed"] == 0
        
        # Verify store was created with geocoded coordinates
        store = db_session.query(Store).filter(Store.store_id == "S1001").first()
        assert store is not None
        assert store.latitude == 42.3601
        assert store.longitude == -71.0589
    
    def test_csv_import_upsert(self, client, db_session):
        """Test CSV import with update (upsert) functionality."""
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
        
        # Create existing store
        existing_store = Store(
            store_id="S1002",
            name="Original Name",
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
        db_session.add(existing_store)
        db_session.commit()
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "TestPassword123!"
        })
        access_token = login_response.json()["access_token"]
        
        # Create CSV content with same store_id but different name
        csv_content = """store_id,name,store_type,status,latitude,longitude,address_street,address_city,address_state,address_postal_code,address_country,phone,services,hours_mon,hours_tue,hours_wed,hours_thu,hours_fri,hours_sat,hours_sun
S1002,Updated Name,regular,active,42.3601,-71.0589,123 Main St,Boston,MA,02101,USA,617-555-0100,pharmacy,08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,09:00-21:00,10:00-20:00"""
        
        # Import CSV
        response = client.post(
            "/api/admin/stores/import",
            files={"file": ("test.csv", csv_content, "text/csv")},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["updated"] == 1
        assert data["created"] == 0
        
        # Verify store was updated
        db_session.refresh(existing_store)
        assert existing_store.name == "Updated Name"

class TestCompleteWorkflow:
    """Integration tests for complete user workflows."""
    
    def test_admin_complete_workflow(self, client, db_session):
        """Test complete workflow for admin user."""
        # Setup: Create role
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
        
        # 1. Create store
        create_response = client.post(
            "/api/admin/stores",
            json={
                "store_id": "S2001",
                "name": "Workflow Store",
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
        assert create_response.status_code == status.HTTP_200_OK
        
        # 2. Get store
        get_response = client.get(
            "/api/admin/stores/S2001",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert get_response.status_code == status.HTTP_200_OK
        
        # 3. Update store
        update_response = client.patch(
            "/api/admin/stores/S2001",
            json={"name": "Updated Workflow Store"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert update_response.status_code == status.HTTP_200_OK
        
        # 4. List stores
        list_response = client.get(
            "/api/admin/stores?page=1&page_size=10",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert list_response.status_code == status.HTTP_200_OK
        
        # 5. Search for store (public endpoint)
        search_response = client.post("/api/stores/search", json={
            "location": {
                "latitude": 42.3601,
                "longitude": -71.0589
            },
            "filters": {
                "radius_miles": 10.0
            }
        })
        assert search_response.status_code == status.HTTP_200_OK
        
        # 6. Delete store
        delete_response = client.delete(
            "/api/admin/stores/S2001",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert delete_response.status_code == status.HTTP_200_OK

