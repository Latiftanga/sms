import time
from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter backed by Redis.

    Key strategy:
    - Authenticated requests (Bearer token present): keyed by user_id decoded
      from the JWT — no DB lookup, just a local verify. Each user gets their
      own RATE_LIMIT_PER_MINUTE bucket.
    - Unauthenticated requests: keyed by real client IP resolved from
      X-Forwarded-For / X-Real-IP (covers reverse-proxy and Docker setups).
      Budget is RATE_LIMIT_UNAUTH_PER_MINUTE (stricter, brute-force protection).

    Always exempt: /health, /verify (public doc verification).
    """

    EXEMPT_PREFIXES = ("/api/v1/health", "/api/v1/verify", "/api/v1/public")

    def _resolve_key(self, request: Request) -> tuple[str, int]:
        """Return (redis_key, limit) for this request."""

        # ── Authenticated: key by user_id from JWT ─────────────────
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                from jose import JWTError, jwt as _jwt
                payload = _jwt.decode(
                    auth[7:],
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                user_id = payload.get("sub", "")
                if user_id:
                    return f"ratelimit:u:{user_id}", settings.RATE_LIMIT_PER_MINUTE
            except Exception:
                pass  # invalid/expired token — fall through to IP-based limit

        # ── Unauthenticated: key by real IP ────────────────────────
        # X-Forwarded-For may be a comma-separated list; leftmost is the client.
        forwarded = request.headers.get("X-Forwarded-For", "")
        real_ip = (
            forwarded.split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or (request.client.host if request.client else "unknown")
        )
        return f"ratelimit:ip:{real_ip}", settings.RATE_LIMIT_UNAUTH_PER_MINUTE

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if any(request.url.path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return await call_next(request)

        from app.core.redis import get_redis

        try:
            redis = get_redis()
            key, limit = self._resolve_key(request)
            minute = int(time.time() // 60)
            bucket = f"{key}:{minute}"

            count = await redis.incr(bucket)
            if count == 1:
                await redis.expire(bucket, 60)

            if count > limit:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded. Try again in a minute."},
                    headers={"Retry-After": "60", "X-RateLimit-Limit": str(limit)},
                )
        except Exception:
            # Redis unavailable — fail open rather than blocking traffic
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
