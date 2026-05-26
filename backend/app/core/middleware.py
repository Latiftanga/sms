import time
from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter backed by Redis.
    Exempt paths: /api/v1/health, /api/v1/verify (public doc verification).
    """

    EXEMPT_PREFIXES = ("/api/v1/health", "/api/v1/verify", "/api/v1/auth/me", "/api/v1/auth/refresh")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if any(request.url.path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return await call_next(request)

        # Lazy import avoids circular deps; Redis is available after lifespan init
        from app.core.redis import get_redis

        try:
            redis = get_redis()
            client_ip = request.client.host if request.client else "unknown"
            minute = int(time.time() // 60)
            key = f"ratelimit:{client_ip}:{minute}"

            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 60)

            if count > settings.RATE_LIMIT_PER_MINUTE:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded. Try again in a minute."},
                    headers={"Retry-After": "60"},
                )
        except Exception:
            # If Redis is down, fail open rather than blocking all traffic
            pass

        return await call_next(request)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every response for traceability."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import uuid
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
