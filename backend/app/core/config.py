from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_NAME: str = "School Management System"
    SECRET_KEY: str
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str

    # ── Redis ─────────────────────────────────────────────────────
    REDIS_URL: str

    # ── JWT ───────────────────────────────────────────────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # ── Permissions ───────────────────────────────────────────────
    PERMISSION_CACHE_TTL: int = 900  # 15 minutes

    # ── Rate limiting ─────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 300        # per authenticated user
    RATE_LIMIT_UNAUTH_PER_MINUTE: int = 30  # per IP for unauthenticated

    # ── Sentry ────────────────────────────────────────────────────
    SENTRY_DSN: str | None = None

    # ── File storage ──────────────────────────────────────────────
    STORAGE_BACKEND: str = "local"           # "local" | "r2"
    UPLOADS_DIR: str = "/tmp/uploads"        # local backend root (/tmp is always writable)
    UPLOADS_URL_PREFIX: str = "/uploads"     # public URL prefix for local files

    # ── Cloudflare R2 ─────────────────────────────────────────────
    R2_ACCOUNT_ID: str | None = None
    R2_ACCESS_KEY_ID: str | None = None
    R2_SECRET_ACCESS_KEY: str | None = None
    R2_BUCKET: str = "ttek-sis"
    R2_ENDPOINT: str | None = None

    # ── Africa's Talking ──────────────────────────────────────────
    AT_API_KEY: str | None = None
    AT_USERNAME: str = "sandbox"
    AT_SENDER_ID: str = "TTEK-SIS"

    # ── CORS ──────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_test(self) -> bool:
        return self.APP_ENV == "test"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
