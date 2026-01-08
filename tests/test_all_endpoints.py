#!/usr/bin/env python3

import httpx
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def test_endpoint(name: str, method: str, url: str, headers: Optional[dict] = None, 
                  data: Optional[dict] = None, expected_status: int = 200):
    """Test a single endpoint"""
    try:
        with httpx.Client(timeout=30.0) as client:
            if method.upper() == "GET":
                response = client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = client.post(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = client.patch(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = client.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = client.delete(url, headers=headers)
            else:
                print_error(f"Unsupported HTTP method: {method}")
                return False, None
            
            if response.status_code == expected_status:
                print_success(f"{name} - Status: {response.status_code}")
                return True, response
            else:
                print_error(f"{name} - Expected status code {expected_status}, got {response.status_code}")
                print_error(f"Response: {response.text[:200]}")
                return False, response
    except Exception as e:
        print_error(f"{name} - Error: {str(e)}")
        return False, None

def main():
    print_info("=" * 60)
    print_info("Starting testing of all API endpoints")
    print_info("=" * 60)
    print()
    
    # Store tokens
    access_token = None
    refresh_token = None
    admin_token = None
    
    # ============================================================================
    # 1. Public Endpoints (No authentication required)
    # ============================================================================
    print_info("\n【1. Public Endpoint Testing】")
    print("-" * 60)
    
    # Health check
    success, response = test_endpoint(
        "GET / - Health Check",
        "GET",
        f"{BASE_URL}/"
    )
    
    # Search - By coordinates
    print()
    print_info("Testing search functionality...")
    success, response = test_endpoint(
        "POST /api/stores/search - Search by coordinates",
        "POST",
        f"{BASE_URL}/api/stores/search",
        data={
            "location": {
                "latitude": 42.3601,
                "longitude": -71.0589
            },
            "filters": {
                "radius_miles": 10.0
            }
        }
    )
    
    # ============================================================================
    # 2. Authentication Endpoints
    # ============================================================================
    print_info("\n【2. Authentication Endpoint Testing】")
    print("-" * 60)
    
    # Login - Admin
    print()
    print_info("Testing Admin login...")
    success, response = test_endpoint(
        "POST /api/auth/login - Admin login",
        "POST",
        f"{BASE_URL}/api/auth/login",
        data={
            "email": "admin@test.com",
            "password": "TestPassword123!"
        },
        expected_status=200
    )
    
    if success and response:
        try:
            tokens = response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            print_success(f"Got access_token: {access_token[:20]}...")
            print_success(f"Got refresh_token: {refresh_token[:20]}...")
            admin_token = access_token
        except:
            print_error("Could not parse login response")
    
    # Refresh token
    if refresh_token:
        print()
        print_info("Testing token refresh...")
        success, response = test_endpoint(
            "POST /api/auth/refresh - Refresh token",
            "POST",
            f"{BASE_URL}/api/auth/refresh",
            data={
                "refresh_token": refresh_token
            },
            expected_status=200
        )
        if success and response:
            try:
                new_tokens = response.json()
                new_access_token = new_tokens.get("access_token")
                print_success(f"Got new access_token: {new_access_token[:20]}...")
                access_token = new_access_token  # Use new token
            except:
                print_warning("Could not parse refresh response")
    
    # ============================================================================
    # 3. Store Management Endpoints (Authentication required)
    # ============================================================================
    if not admin_token:
        print_error("\nCould not get auth token, skipping authenticated tests")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print_info("\n【3. Store Management Endpoint Testing】")
    print("-" * 60)
    
    # Create store
    print()
    print_info("Testing store creation...")
    test_store_id = "S9999"
    success, response = test_endpoint(
        "POST /api/admin/stores - Create store",
        "POST",
        f"{BASE_URL}/api/admin/stores",
        headers=headers,
        data={
            "store_id": test_store_id,
            "name": "Test Store",
            "store_type": "regular",
            "status": "active",
            "latitude": 42.3601,
            "longitude": -71.0589,
            "address_street": "123 Test St",
            "address_city": "Boston",
            "address_state": "MA",
            "address_postal_code": "02101",
            "address_country": "USA",
            "phone": "617-555-9999",
            "services": ["pharmacy"],
            "hours_mon": "08:00-22:00",
            "hours_tue": "08:00-22:00",
            "hours_wed": "08:00-22:00",
            "hours_thu": "08:00-22:00",
            "hours_fri": "08:00-22:00",
            "hours_sat": "09:00-21:00",
            "hours_sun": "10:00-20:00"
        },
        expected_status=200
    )
    
    # List stores
    print()
    print_info("Testing list stores...")
    success, response = test_endpoint(
        "GET /api/admin/stores - List stores (paginated)",
        "GET",
        f"{BASE_URL}/api/admin/stores?page=1&page_size=10",
        headers=headers
    )
    
    # Get store details
    print()
    print_info("Testing get store details...")
    success, response = test_endpoint(
        f"GET /api/admin/stores/{test_store_id} - Get store details",
        "GET",
        f"{BASE_URL}/api/admin/stores/{test_store_id}",
        headers=headers
    )
    
    # Update store
    print()
    print_info("Testing update store...")
    success, response = test_endpoint(
        f"PATCH /api/admin/stores/{test_store_id} - Partially update store",
        "PATCH",
        f"{BASE_URL}/api/admin/stores/{test_store_id}",
        headers=headers,
        data={
            "name": "Updated Test Store",
            "phone": "617-555-8888"
        },
        expected_status=200
    )
    
    # Search stores (Public endpoint, but testing it anyway)
    print()
    print_info("Testing search stores (Public endpoint)...")
    success, response = test_endpoint(
        "POST /api/stores/search - Search stores (with service filter)",
        "POST",
        f"{BASE_URL}/api/stores/search",
        data={
            "location": {
                "latitude": 42.3601,
                "longitude": -71.0589
            },
            "filters": {
                "radius_miles": 10.0,
                "services": ["pharmacy"],
                "store_types": ["regular"]
            }
        }
    )
    
    # ============================================================================
    # 4. CSV Import Testing
    # ============================================================================
    print_info("\n【4. CSV Import Testing】")
    print("-" * 60)
    
    print()
    print_info("Testing CSV import...")
    csv_content = """store_id,name,store_type,status,latitude,longitude,address_street,address_city,address_state,address_postal_code,address_country,phone,services,hours_mon,hours_tue,hours_wed,hours_thu,hours_fri,hours_sat,hours_sun
S8888,CSV Import Test Store,regular,active,42.3601,-71.0589,456 CSV St,Boston,MA,02101,USA,617-555-7777,pharmacy|pickup,08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,09:00-21:00,10:00-20:00"""
    
    try:
        files = {'file': ('test.csv', csv_content.encode(), 'text/csv')}
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{BASE_URL}/api/admin/stores/import",
                headers=headers,
                files=files
            )
        if response.status_code == 200:
            print_success(f"POST /api/admin/stores/import - CSV Import - Status: {response.status_code}")
            result = response.json()
            print_info(f"  Import results: Total {result.get('total_rows')}, Created {result.get('created')}, Updated {result.get('updated')}, Failed {result.get('failed')}")
        else:
            print_error(f"POST /api/admin/stores/import - Expected status code 200, got {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
    except Exception as e:
        print_error(f"CSV Import Testing - Error: {str(e)}")
    
    # ============================================================================
    # 5. User Management Endpoints (Admin only)
    # ============================================================================
    print_info("\n【5. User Management Endpoint Testing】")
    print("-" * 60)
    
    # List users
    print()
    print_info("Testing list users...")
    success, response = test_endpoint(
        "GET /api/admin/users - List all users",
        "GET",
        f"{BASE_URL}/api/admin/users",
        headers=headers
    )
    
    # Create user
    print()
    print_info("Testing create user...")
    test_user_id = "U9999"
    success, response = test_endpoint(
        "POST /api/admin/users - Create user",
        "POST",
        f"{BASE_URL}/api/admin/users",
        headers=headers,
        data={
            "user_id": test_user_id,
            "email": "testuser@test.com",
            "password": "TestPassword123!",
            "role": "viewer"
        },
        expected_status=200
    )
    
    # Update user
    if success:
        print()
        print_info("Testing update user...")
        success, response = test_endpoint(
            f"PUT /api/admin/users/{test_user_id} - Update user",
            "PUT",
            f"{BASE_URL}/api/admin/users/{test_user_id}",
            headers=headers,
            data={
                "role": "marketer",
                "status": "active"
            },
            expected_status=200
        )
    
    # ============================================================================
    # 6. Permissions Testing (Testing different roles' access)
    # ============================================================================
    print_info("\n【6. Permissions Testing】")
    print("-" * 60)
    
    # Test Viewer role (should not be able to create store)
    print()
    print_info("Testing Viewer role permissions (should not be able to create store)...")
    success, viewer_response = test_endpoint(
        "POST /api/auth/login - Viewer login",
        "POST",
        f"{BASE_URL}/api/auth/login",
        data={
            "email": "viewer@test.com",
            "password": "TestPassword123!"
        },
        expected_status=200
    )
    
    if success and viewer_response:
        try:
            viewer_tokens = viewer_response.json()
            viewer_token = viewer_tokens.get("access_token")
            viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
            
            # Viewer should not be able to create store
            print()
            print_info("Testing Viewer trying to create store (should fail)...")
            success, response = test_endpoint(
                "POST /api/admin/stores - Viewer creating store (should be denied)",
                "POST",
                f"{BASE_URL}/api/admin/stores",
                headers=viewer_headers,
                data={
                    "store_id": "S9998",
                    "name": "Viewer Test Store",
                    "store_type": "regular",
                    "status": "active",
                    "latitude": 42.3601,
                    "longitude": -71.0589,
                    "address_street": "123 Test St",
                    "address_city": "Boston",
                    "address_state": "MA",
                    "address_postal_code": "02101",
                    "address_country": "USA",
                    "phone": "617-555-9999",
                    "services": [],
                    "hours_mon": "08:00-22:00",
                    "hours_tue": "08:00-22:00",
                    "hours_wed": "08:00-22:00",
                    "hours_thu": "08:00-22:00",
                    "hours_fri": "08:00-22:00",
                    "hours_sat": "09:00-21:00",
                    "hours_sun": "10:00-20:00"
                },
                expected_status=403  # Should return 403 Forbidden
            )
            if response and response.status_code == 403:
                print_success("Permission control working: Viewer cannot create store")
        except:
            print_warning("Could not test Viewer permissions")
    
    # ============================================================================
    # 7. Cleanup Test Data
    # ============================================================================
    print_info("\n【7. Cleanup Test Data】")
    print("-" * 60)
    
    # Delete test store
    print()
    print_info("Deleting test store...")
    success, response = test_endpoint(
        f"DELETE /api/admin/stores/{test_store_id} - Delete (deactivate) store",
        "DELETE",
        f"{BASE_URL}/api/admin/stores/{test_store_id}",
        headers=headers,
        expected_status=200
    )
    
    # Delete test user
    print()
    print_info("Deleting test user...")
    success, response = test_endpoint(
        f"DELETE /api/admin/users/{test_user_id} - Delete (deactivate) user",
        "DELETE",
        f"{BASE_URL}/api/admin/users/{test_user_id}",
        headers=headers,
        expected_status=200
    )
    
    # ============================================================================
    # 8. Logout
    # ============================================================================
    print_info("\n【8. Logout Testing】")
    print("-" * 60)
    
    if refresh_token:
        print()
        print_info("Testing logout...")
        success, response = test_endpoint(
            "POST /api/auth/logout - Logout",
            "POST",
            f"{BASE_URL}/api/auth/logout",
            headers=headers,
            data={
                "refresh_token": refresh_token
            },
            expected_status=200
        )
    
    # ============================================================================
    # Summary
    # ============================================================================
    print()
    print_info("=" * 60)
    print_info("All endpoint tests completed!")
    print_info("=" * 60)
    print()
    print_info("Visit http://localhost:8000/docs to view full API documentation")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print_error(f"\nError occurred during testing: {str(e)}")
        import traceback
        traceback.print_exc()

