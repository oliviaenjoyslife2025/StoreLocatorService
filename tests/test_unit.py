import pytest
from datetime import datetime
from distance_calculator import calculate_bounding_box, calculate_distance
from auth import hash_password, verify_password
from csv_import import validate_hours, parse_services

class TestDistanceCalculation:
    """Unit tests for distance calculation functions."""
    
    def test_calculate_distance_same_location(self):
        """Test distance calculation for same location."""
        lat, lon = 42.3601, -71.0589
        distance = calculate_distance(lat, lon, lat, lon)
        assert distance == 0.0
    
    def test_calculate_distance_boston_to_cambridge(self):
        """Test distance between Boston and Cambridge."""
        boston_lat, boston_lon = 42.3601, -71.0589
        cambridge_lat, cambridge_lon = 42.3736, -71.1097
        distance = calculate_distance(boston_lat, boston_lon, cambridge_lat, cambridge_lon)
        # Distance is approximately 2.76 miles
        assert 2.5 <= distance <= 4.5
    
    def test_calculate_distance_known_coordinates(self):
        """Test distance with known coordinates."""
        # New York to Los Angeles (approximately 2445 miles)
        ny_lat, ny_lon = 40.7128, -74.0060
        la_lat, la_lon = 34.0522, -118.2437
        distance = calculate_distance(ny_lat, ny_lon, la_lat, la_lon)
        assert 2400 <= distance <= 2500

class TestBoundingBox:
    """Unit tests for bounding box calculation."""
    
    def test_bounding_box_small_radius(self):
        """Test bounding box with small radius."""
        lat, lon = 42.3601, -71.0589
        radius = 5.0
        bbox = calculate_bounding_box(lat, lon, radius)
        
        assert bbox["min_lat"] < lat < bbox["max_lat"]
        assert bbox["min_lon"] < lon < bbox["max_lon"]
        assert bbox["min_lat"] >= -90
        assert bbox["max_lat"] <= 90
    
    def test_bounding_box_large_radius(self):
        """Test bounding box with large radius."""
        lat, lon = 42.3601, -71.0589
        radius = 100.0
        bbox = calculate_bounding_box(lat, lon, radius)
        
        assert bbox["min_lat"] < lat < bbox["max_lat"]
        assert bbox["min_lon"] < lon < bbox["max_lon"]
    
    def test_bounding_box_equator(self):
        """Test bounding box at equator."""
        lat, lon = 0.0, 0.0
        radius = 10.0
        bbox = calculate_bounding_box(lat, lon, radius)
        
        assert bbox["min_lat"] < 0 < bbox["max_lat"]
        assert bbox["min_lon"] < 0 < bbox["max_lon"]
    
    def test_bounding_box_pole(self):
        """Test bounding box near pole."""
        lat, lon = 89.0, 0.0
        radius = 10.0
        bbox = calculate_bounding_box(lat, lon, radius)
        
        assert bbox["max_lat"] <= 90
        assert bbox["min_lat"] >= -90

class TestHoursValidation:
    """Unit tests for hours parsing and validation."""
    
    def test_validate_hours_closed(self):
        """Test validation of 'closed' hours."""
        assert validate_hours("closed") == True
        assert validate_hours("Closed") == True
        assert validate_hours("CLOSED") == True
    
    def test_validate_hours_valid_format(self):
        """Test validation of valid hours format."""
        assert validate_hours("08:00-22:00") == True
        assert validate_hours("8:00-22:00") == True  # Lenient with leading zero
        assert validate_hours("09:30-17:30") == True
        assert validate_hours("00:00-23:59") == True
    
    def test_validate_hours_invalid_format(self):
        """Test validation of invalid hours format."""
        assert validate_hours("08:00-22:00-23:00") == False  # Too many parts
        assert validate_hours("08:00") == False  # Missing close time
        assert validate_hours("25:00-26:00") == False  # Invalid time
        assert validate_hours("abc-def") == False  # Not a time
    
    def test_validate_hours_overnight(self):
        """Test validation of overnight hours."""
        # Overnight hours (e.g., 22:00-06:00) should be valid
        assert validate_hours("22:00-06:00") == True

class TestPasswordHashing:
    """Unit tests for password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) == True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) == False
    
    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "TestPassword123!"
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)
        # Hashes should be different due to random salt
        assert hashed1 != hashed2
        # But both should verify correctly
        assert verify_password(password, hashed1) == True
        assert verify_password(password, hashed2) == True

class TestServicesParsing:
    """Unit tests for services parsing."""
    
    def test_parse_services_single(self):
        """Test parsing single service."""
        services = parse_services("pharmacy")
        assert services == ["pharmacy"]
    
    def test_parse_services_multiple(self):
        """Test parsing multiple services."""
        services = parse_services("pharmacy|pickup|optical")
        assert services == ["pharmacy", "pickup", "optical"]
    
    def test_parse_services_empty(self):
        """Test parsing empty services string."""
        services = parse_services("")
        assert services == []
    
    def test_parse_services_with_spaces(self):
        """Test parsing services with spaces (should strip)."""
        services = parse_services("pharmacy | pickup | optical")
        assert services == ["pharmacy", "pickup", "optical"]
    
    def test_parse_services_empty_parts(self):
        """Test parsing services with empty parts."""
        services = parse_services("pharmacy||pickup")
        assert services == ["pharmacy", "pickup"]

