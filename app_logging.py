import logging
import sys
import time
import jwt
from fastapi import Request

from config import settings

LOGGER_NAME = "store_locator"
SKIP_ACCESS_LOG_PATHS = {"/docs", "/redoc", "/openapi.json", "/favicon.ico"}


def setup_logging() -> logging.Logger:
    """Configure application logging once and return the app logger."""
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "-"


def user_id_from_request(request: Request) -> str:
    """Best-effort user id from a Bearer token. Never raises."""
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return "anonymous"

    token = auth.split(" ", 1)[1].strip()
    if not token:
        return "anonymous"

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        return str(payload.get("user_id") or "anonymous")
    except Exception:
        return "anonymous"


def format_access_log(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    ip: str,
    user_id: str,
) -> str:
    return (
        f"{method} {path} {status_code} {duration_ms:.1f}ms "
        f"ip={ip} user={user_id}"
    )


def should_skip_access_log(path: str) -> bool:
    return path in SKIP_ACCESS_LOG_PATHS


async def log_requests(request: Request, call_next):
    """FastAPI middleware that writes one access log line per request."""
    logger = get_logger()
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        if not should_skip_access_log(request.url.path):
            logger.exception(
                format_access_log(
                    request.method,
                    request.url.path,
                    500,
                    duration_ms,
                    client_ip(request),
                    user_id_from_request(request),
                )
            )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    if should_skip_access_log(request.url.path):
        return response

    message = format_access_log(
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        client_ip(request),
        user_id_from_request(request),
    )
    if response.status_code >= 500:
        logger.error(message)
    elif response.status_code >= 400:
        logger.warning(message)
    else:
        logger.info(message)
    return response


setup_logging()
