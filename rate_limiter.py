import time
import redis
from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from functools import wraps
import datetime

from config import settings
from database import get_redis_client

async def rate_limit(request: Request, redis_client: redis.Redis = Depends(get_redis_client)):
    ip_address = request.client.host
    
    # Minute-based rate limit
    current_minute = datetime.datetime.now().strftime("%Y%m%d%H%M")
    minute_key = f"rate_limit:minute:{ip_address}:{current_minute}"
    
    # Using pipeline for atomicity in setting expire if key is new
    pipe = redis_client.pipeline()
    pipe.incr(minute_key)
    pipe.expire(minute_key, 60) # Expire after 60 seconds
    minute_count, _ = pipe.execute()

    if minute_count > settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests from {ip_address}. Please try again after a minute.",
            headers={"Retry-After": str(60 - datetime.datetime.now().second)}
        )

    # Hour-based rate limit
    current_hour = datetime.datetime.now().strftime("%Y%m%d%H")
    hour_key = f"rate_limit:hour:{ip_address}:{current_hour}"

    pipe = redis_client.pipeline()
    pipe.incr(hour_key)
    pipe.expire(hour_key, 3600) # Expire after 3600 seconds (1 hour)
    hour_count, _ = pipe.execute()

    if hour_count > settings.RATE_LIMIT_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests from {ip_address}. Please try again after an hour.",
            headers={"Retry-After": str(3600 - datetime.datetime.now().minute * 60 - datetime.datetime.now().second)}
        )
