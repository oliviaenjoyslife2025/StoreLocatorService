import math
from geopy.distance import geodesic

def calculate_bounding_box(latitude: float, longitude: float, radius_miles: float):
    EARTH_RADIUS_MILES = 3959.0

    # Rough conversion factors for latitude and longitude degrees to miles
    # Latitude: 1 degree approx 69 miles
    # Longitude: 1 degree approx (69 * cos(latitude)) miles

    lat_delta = radius_miles / 69.0
    
    # Convert radius to degrees of longitude
    # This conversion factor depends on the latitude
    cos_lat = math.cos(math.radians(latitude))
    if abs(cos_lat) < 1e-6: # Handle poles where cos_lat is zero or very small
        # Approximation for poles
        lon_delta = radius_miles / EARTH_RADIUS_MILES * 360 / (2 * math.pi) 
    else:
        lon_delta = radius_miles / (69.0 * cos_lat)

    min_lat = latitude - lat_delta
    max_lat = latitude + lat_delta
    min_lon = longitude - lon_delta
    max_lon = longitude + lon_delta

    # Clamp latitudes to valid range (-90 to 90)
    min_lat = max(-90.0, min_lat)
    max_lat = min(90.0, max_lat)

    # Longitudes wrap around, so no clamping needed for simple bounding box in SQL

    return {
        "min_lat": min_lat,
        "max_lat": max_lat,
        "min_lon": min_lon,
        "max_lon": max_lon,
    }

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the Haversine distance between two sets of coordinates in miles.
    """
    point1 = (lat1, lon1)
    point2 = (lat2, lon2)
    return geodesic(point1, point2).miles

