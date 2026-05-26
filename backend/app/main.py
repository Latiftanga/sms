from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings
from app.core.middleware import RateLimitMiddleware, RequestIDMiddleware
from app.core.redis import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────
    await init_redis()
    yield
    # ── Shutdown ──────────────────────────────────────────────────
    await close_redis()


def create_app() -> FastAPI:
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.APP_ENV,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=0.1 if settings.is_production else 1.0,
        )

    app = FastAPI(
        title="TTEK-SIS API",
        version="1.0.0",
        description="Tagnatek Enterprise School Information System",
        lifespan=lifespan,
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
    )

    # ── Middleware (applied in reverse order) ─────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ── Routers ───────────────────────────────────────────────────
    from app.api.v1 import api_router
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
