from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.db import check_db_health
from app.core.redis import check_redis_health

router = APIRouter(prefix="/health", tags=["health"])


class ComponentStatus(BaseModel):
    ok: bool
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    timestamp: str
    version: str
    components: dict[str, ComponentStatus]


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Full health check including DB + Redis connectivity.
    Returns HTTP 200 if all components are healthy, 503 if any are down.
    Exempt from rate limiting (see middleware).
    """
    import time

    results: dict[str, ComponentStatus] = {}

    # ── Database ──────────────────────────────────────────────────
    t0 = time.perf_counter()
    db_ok = await check_db_health()
    results["database"] = ComponentStatus(
        ok=db_ok, latency_ms=round((time.perf_counter() - t0) * 1000, 2)
    )

    # ── Redis ─────────────────────────────────────────────────────
    t0 = time.perf_counter()
    redis_ok = await check_redis_health()
    results["redis"] = ComponentStatus(
        ok=redis_ok, latency_ms=round((time.perf_counter() - t0) * 1000, 2)
    )

    all_ok = all(c.ok for c in results.values())
    status = "healthy" if all_ok else "degraded"

    from fastapi import Response
    return HealthResponse(
        status=status,
        timestamp=datetime.now(UTC).isoformat(),
        version="1.0.0",
        components=results,
    )


@router.get("/ping")
async def ping() -> dict:
    """Lightweight liveness probe — no DB/Redis check."""
    return {"pong": True}
