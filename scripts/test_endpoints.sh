#!/bin/bash

# 测试所有API端点的脚本（使用curl）

BASE_URL="http://localhost:8000"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local auth_token=$4
    local data=$5
    local expected_status=${6:-200}
    
    local curl_cmd="curl -s -w \"\n%{http_code}\""
    
    if [ -n "$auth_token" ]; then
        curl_cmd="$curl_cmd -H \"Authorization: Bearer $auth_token\""
    fi
    
    if [ "$method" = "GET" ]; then
        response=$(eval "$curl_cmd -X GET \"$url\"")
    elif [ "$method" = "POST" ]; then
        response=$(eval "$curl_cmd -X POST \"$url\" -H \"Content-Type: application/json\" -d '$data'")
    elif [ "$method" = "PATCH" ]; then
        response=$(eval "$curl_cmd -X PATCH \"$url\" -H \"Content-Type: application/json\" -d '$data'")
    elif [ "$method" = "PUT" ]; then
        response=$(eval "$curl_cmd -X PUT \"$url\" -H \"Content-Type: application/json\" -d '$data'")
    elif [ "$method" = "DELETE" ]; then
        response=$(eval "$curl_cmd -X DELETE \"$url\"")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        print_success "$name - Status: $http_code"
        return 0
    else
        print_error "$name - Expected status code $expected_status, got $http_code"
        echo "$body" | head -c 200
        echo ""
        return 1
    fi
}

echo ""
print_info "============================================================"
print_info "Starting testing of all API endpoints"
print_info "============================================================"
echo ""

# 1. Public Endpoints
print_info "【1. Public Endpoint Testing】"
echo "------------------------------------------------------------"

test_endpoint "GET / - Health Check" "GET" "$BASE_URL/" "" ""

echo ""
print_info "Testing search functionality..."
test_endpoint "POST /api/stores/search - Search by coordinates" "POST" "$BASE_URL/api/stores/search" "" \
'{"location":{"latitude":42.3601,"longitude":-71.0589},"filters":{"radius_miles":10.0}}'

# 2. Authentication Endpoints
echo ""
print_info "【2. Authentication Endpoint Testing】"
echo "------------------------------------------------------------"

echo ""
print_info "Testing Admin login..."
login_response=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"TestPassword123!"}')

http_code=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"TestPassword123!"}')

if [ "$http_code" = "200" ]; then
    print_success "POST /api/auth/login - Admin login - Status: $http_code"
    access_token=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    refresh_token=$(echo "$login_response" | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)
    if [ -n "$access_token" ]; then
        print_success "Got access_token: ${access_token:0:20}..."
        admin_token="$access_token"
    fi
else
    print_error "Login failed, status code: $http_code"
    exit 1
fi

# Refresh token
if [ -n "$refresh_token" ]; then
    echo ""
    print_info "Testing token refresh..."
    refresh_response=$(curl -s -X POST "$BASE_URL/api/auth/refresh" \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\":\"$refresh_token\"}")
    refresh_code=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/auth/refresh" \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\":\"$refresh_token\"}")
    if [ "$refresh_code" = "200" ]; then
        print_success "POST /api/auth/refresh - Refresh token - Status: $refresh_code"
        new_access_token=$(echo "$refresh_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        if [ -n "$new_access_token" ]; then
            access_token="$new_access_token"
        fi
    fi
fi

if [ -z "$admin_token" ]; then
    print_error "Could not get auth token, skipping authenticated tests"
    exit 1
fi

# 3. Store Management Endpoints
echo ""
print_info "【3. Store Management Endpoint Testing】"
echo "------------------------------------------------------------"

test_store_id="S9999"

echo ""
print_info "Testing store creation..."
test_endpoint "POST /api/admin/stores - Create store" "POST" "$BASE_URL/api/admin/stores" "$admin_token" \
"{\"store_id\":\"$test_store_id\",\"name\":\"Test Store\",\"store_type\":\"regular\",\"status\":\"active\",\"latitude\":42.3601,\"longitude\":-71.0589,\"address_street\":\"123 Test St\",\"address_city\":\"Boston\",\"address_state\":\"MA\",\"address_postal_code\":\"02101\",\"address_country\":\"USA\",\"phone\":\"617-555-9999\",\"services\":[\"pharmacy\"],\"hours_mon\":\"08:00-22:00\",\"hours_tue\":\"08:00-22:00\",\"hours_wed\":\"08:00-22:00\",\"hours_thu\":\"08:00-22:00\",\"hours_fri\":\"08:00-22:00\",\"hours_sat\":\"09:00-21:00\",\"hours_sun\":\"10:00-20:00\"}"

echo ""
print_info "Testing list stores..."
test_endpoint "GET /api/admin/stores - List stores" "GET" "$BASE_URL/api/admin/stores?page=1&page_size=10" "$admin_token" ""

echo ""
print_info "Testing get store details..."
test_endpoint "GET /api/admin/stores/$test_store_id - Get store details" "GET" "$BASE_URL/api/admin/stores/$test_store_id" "$admin_token" ""

echo ""
print_info "Testing update store..."
test_endpoint "PATCH /api/admin/stores/$test_store_id - Partially update store" "PATCH" "$BASE_URL/api/admin/stores/$test_store_id" "$admin_token" \
"{\"name\":\"Updated Test Store\",\"phone\":\"617-555-8888\"}"

# 4. CSV Import
echo ""
print_info "【4. CSV Import Testing】"
echo "------------------------------------------------------------"

echo ""
print_info "Testing CSV import..."
csv_content="store_id,name,store_type,status,latitude,longitude,address_street,address_city,address_state,address_postal_code,address_country,phone,services,hours_mon,hours_tue,hours_wed,hours_thu,hours_fri,hours_sat,hours_sun
S8888,CSV Import Test Store,regular,active,42.3601,-71.0589,456 CSV St,Boston,MA,02101,USA,617-555-7777,pharmacy|pickup,08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,09:00-21:00,10:00-20:00"

import_response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/admin/stores/import" \
  -H "Authorization: Bearer $admin_token" \
  -F "file=@-;filename=test.csv" <<< "$csv_content")

import_code=$(echo "$import_response" | tail -n1)
if [ "$import_code" = "200" ]; then
    print_success "POST /api/admin/stores/import - CSV import - Status: $import_code"
else
    print_error "CSV import failed, status code: $import_code"
fi

# 5. User Management Endpoints
echo ""
print_info "【5. User Management Endpoint Testing】"
echo "------------------------------------------------------------"

echo ""
print_info "Testing list users..."
test_endpoint "GET /api/admin/users - List all users" "GET" "$BASE_URL/api/admin/users" "$admin_token" ""

test_user_id="U9999"

echo ""
print_info "Testing create user..."
test_endpoint "POST /api/admin/users - Create user" "POST" "$BASE_URL/api/admin/users" "$admin_token" \
"{\"user_id\":\"$test_user_id\",\"email\":\"testuser@test.com\",\"password\":\"TestPassword123!\",\"role\":\"viewer\"}"

echo ""
print_info "Testing update user..."
test_endpoint "PUT /api/admin/users/$test_user_id - Update user" "PUT" "$BASE_URL/api/admin/users/$test_user_id" "$admin_token" \
"{\"role\":\"marketer\",\"status\":\"active\"}"

# 6. Permissions Testing
echo ""
print_info "【6. Permissions Testing】"
echo "------------------------------------------------------------"

echo ""
print_info "Testing Viewer role permissions (should not be able to create store)..."
viewer_login=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"viewer@test.com","password":"TestPassword123!"}')

viewer_code=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"viewer@test.com","password":"TestPassword123!"}')

if [ "$viewer_code" = "200" ]; then
    viewer_token=$(echo "$viewer_login" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    if [ -n "$viewer_token" ]; then
        echo ""
        print_info "Testing Viewer trying to create store (should fail)..."
        test_endpoint "POST /api/admin/stores - Viewer creating store (should be denied)" "POST" "$BASE_URL/api/admin/stores" "$viewer_token" \
"{\"store_id\":\"S9998\",\"name\":\"Viewer Test Store\",\"store_type\":\"regular\",\"status\":\"active\",\"latitude\":42.3601,\"longitude\":-71.0589,\"address_street\":\"123 Test St\",\"address_city\":\"Boston\",\"address_state\":\"MA\",\"address_postal_code\":\"02101\",\"address_country\":\"USA\",\"phone\":\"617-555-9999\",\"services\":[],\"hours_mon\":\"08:00-22:00\",\"hours_tue\":\"08:00-22:00\",\"hours_wed\":\"08:00-22:00\",\"hours_thu\":\"08:00-22:00\",\"hours_fri\":\"08:00-22:00\",\"hours_sat\":\"09:00-21:00\",\"hours_sun\":\"10:00-20:00\"}" 403
    fi
fi

# 7. Cleanup Test Data
echo ""
print_info "【7. Cleanup Test Data】"
echo "------------------------------------------------------------"

echo ""
print_info "Deleting test store..."
test_endpoint "DELETE /api/admin/stores/$test_store_id - Deactivate (soft delete) store" "DELETE" "$BASE_URL/api/admin/stores/$test_store_id" "$admin_token" ""

echo ""
print_info "Deleting test user..."
test_endpoint "DELETE /api/admin/users/$test_user_id - Deactivate (soft delete) user" "DELETE" "$BASE_URL/api/admin/users/$test_user_id" "$admin_token" ""

# 8. Logout
echo ""
print_info "【8. Logout Testing】"
echo "------------------------------------------------------------"

if [ -n "$refresh_token" ]; then
    echo ""
    print_info "Testing logout..."
    test_endpoint "POST /api/auth/logout - Logout" "POST" "$BASE_URL/api/auth/logout" "$admin_token" \
"{\"refresh_token\":\"$refresh_token\"}"
fi

# Summary
echo ""
print_info "============================================================"
print_info "All endpoint tests completed!"
print_info "============================================================"
echo ""
print_info "Visit http://localhost:8000/docs to view the full API documentation"

