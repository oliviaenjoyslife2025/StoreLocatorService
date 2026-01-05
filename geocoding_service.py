from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import redis
import json
import datetime

from config import settings
from database import get_redis_client

geolocator = Nominatim(user_agent="store_locator_service")

def get_coordinates_from_address(address: str, redis_client: redis.Redis):
    cache_key = f"geocoding:{address}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        print(f"Cache hit for geocoding: {address}")
        return json.loads(cached_result)

    try:
        location = geolocator.geocode(address, timeout=5)
        if location:
            coordinates = {
                "latitude": location.latitude,
                "longitude": location.longitude
            }
            # Cache for 30 days
            redis_client.setex(cache_key, datetime.timedelta(days=settings.GEOCODING_CACHE_TTL_DAYS), json.dumps(coordinates))
            print(f"Geocoding successful and cached for: {address}")
            return coordinates
        else:
            print(f"Could not geocode address: {address}")
            return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding error for {address}: {e}")
        return None

def get_coordinates_from_postal_code(postal_code: str, redis_client: redis.Redis):
    cache_key = f"geocoding:{postal_code}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        print(f"Cache hit for geocoding: {postal_code}")
        return json.loads(cached_result)

    try:
        location = geolocator.geocode(postal_code, timeout=5)
        if location:
            coordinates = {
                "latitude": location.latitude,
                "longitude": location.longitude
            }
            # Cache for 30 days
            redis_client.setex(cache_key, datetime.timedelta(days=settings.GEOCODING_CACHE_TTL_DAYS), json.dumps(coordinates))
            print(f"Geocoding successful and cached for: {postal_code}")
            return coordinates
        else:
            print(f"Could not geocode postal code: {postal_code}")
            return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding error for {postal_code}: {e}")
        return None

