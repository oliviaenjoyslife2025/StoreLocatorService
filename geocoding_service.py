from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import redis
import json
import datetime

from config import settings
from database import get_redis_client
from app_logging import get_logger

geolocator = Nominatim(user_agent="store_locator_service")
logger = get_logger()

def get_coordinates_from_address(address: str, redis_client: redis.Redis):
    cache_key = f"geocoding:{address}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        logger.debug("Geocoding cache hit for address")
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
            logger.info("Geocoded address and cached result")
            return coordinates
        else:
            logger.warning("Could not geocode address")
            return None
    except (GeocoderTimedOut, GeocoderServiceError):
        logger.warning("Geocoding error for address", exc_info=True)
        return None

def get_coordinates_from_postal_code(postal_code: str, redis_client: redis.Redis):
    cache_key = f"geocoding:{postal_code}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        logger.debug("Geocoding cache hit for postal code")
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
            logger.info("Geocoded postal code and cached result")
            return coordinates
        else:
            logger.warning("Could not geocode postal code")
            return None
    except (GeocoderTimedOut, GeocoderServiceError):
        logger.warning("Geocoding error for postal code", exc_info=True)
        return None
