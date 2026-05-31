"""
Pytest fixtures for async FastAPI + SQLAlchemy + Redis tests.

Isolation strategy:
  - Schema is applied once per session via Alembic (same path as production).
  - The HTTP client uses real DB sessions (same as production) so endpoints
    that call session.commit() work correctly.
  - Fixture data is inserted via a separate session that commits, making it
    visible to the HTTP layer.
  - A session-scoped autouse fixture truncates all non-seeded tables after
    every test so tests start with a clean slate.
"""
import asyncio
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.db import get_session
from app.core.redis import get_redis
from app.main import app


# ── Alembic helpers (sync — run in a thread pool) ─────────────────

def _alembic_cfg() -> Config:
    cfg = Config("alembic.ini")
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    cfg.set_main_option("sqlalchemy.url", sync_url)
    return cfg


def _upgrade() -> None:
    command.upgrade(_alembic_cfg(), "head")


def _downgrade() -> None:
    command.downgrade(_alembic_cfg(), "base")


# ── Tables to truncate between tests (seeded lookup tables are excluded) ──
# Seeded tables (ghana_holiday, grading_scale, staff_position, etc.) are left
# intact — they were inserted by migrations and are needed by tests.
_TRUNCATE_TABLES = [
    "attendance_record",
    "student_term_enrollment",
    "student_class_enrollment",
    "guardian",
    "student",
    "subject_teacher",
    "class_teacher",
    "class_subject",
    "class",
    "learning_area",
    "school_subject",
    "school_period",
    "school_calendar",
    "academic_term",
    "academic_year",
    "staff_leave",
    "staff_qualification",
    "staff_promotion",
    "staff_permission",
    "user_role",
    '"user"',
    "staff_member",
    "school_schedule",
    "school_config",
    "school",
]


# ── Engine ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Apply migrations once; tear down after the full test run."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        await loop.run_in_executor(pool, _upgrade)

    engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
    yield engine

    await engine.dispose()
    with ThreadPoolExecutor(max_workers=1) as pool:
        await loop.run_in_executor(pool, _downgrade)


@pytest_asyncio.fixture(autouse=True)
async def clean_db(db_engine):
    """Truncate test data tables before and after every test for a clean slate.

    CASCADE is required: non-listed tables (grading_scale, staff_position, house,
    student_behaviour_record, etc.) reference listed tables, so PostgreSQL refuses
    RESTRICT. CASCADE also truncates those non-listed tables — that's fine because
    the admin_position fixture re-creates what it needs for each test.
    """
    _truncate_sql = text(f"TRUNCATE {', '.join(_TRUNCATE_TABLES)} RESTART IDENTITY CASCADE")
    async with db_engine.begin() as conn:
        await conn.execute(_truncate_sql)
    yield
    async with db_engine.begin() as conn:
        await conn.execute(_truncate_sql)


# ── Per-test session (for direct service calls / fixture setup) ───

@pytest_asyncio.fixture
async def session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """A real committed session — fixture data is visible to HTTP endpoints."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as sess:
        yield sess


# ── Redis mock ────────────────────────────────────────────────────

@pytest.fixture
def mock_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.get.return_value = None
    redis.setex.return_value = True
    redis.delete.return_value = 1
    redis.ping.return_value = True
    redis.incr.return_value = 1
    redis.expire.return_value = True
    return redis


# ── HTTP test client ──────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(db_engine, mock_redis: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client wired to the test engine (NullPool) + mock Redis.

    Overriding get_session prevents cross-test event-loop contamination: the
    production engine has a connection pool whose asyncpg connections bind to the
    first test's event loop and break on subsequent tests. The test engine uses
    NullPool, so every request gets a brand-new connection on the current loop.
    """
    test_session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_session():
        async with test_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    def override_redis():
        return mock_redis

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ── Test data factories ───────────────────────────────────────────

from datetime import UTC, datetime

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.school import School, SchoolSchedule
from app.models.staff import StaffPosition


@pytest_asyncio.fixture
async def test_school(session: AsyncSession) -> School:
    school = School(
        name="Test School",
        code="TST001",
        slug="test-school",
        education_levels=["BASIC", "JHS"],
        facility_type="DAY",
    )
    session.add(school)
    await session.flush()

    schedule = SchoolSchedule(school_id=school.id, school_days=[1, 2, 3, 4, 5])
    session.add(schedule)
    await session.commit()
    return school


@pytest_asyncio.fixture
async def admin_position(session: AsyncSession) -> StaffPosition:
    # CASCADE in clean_db wipes staff_position between tests, so we create a
    # fresh position each time — no conflict with the migration-seeded ADMIN.
    pos = StaffPosition(
        school_id=None, name="Admin", code="ADMIN", is_system_template=True
    )
    session.add(pos)
    await session.commit()
    return pos


@pytest_asyncio.fixture
async def admin_user(session: AsyncSession, test_school: School, admin_position: StaffPosition) -> User:
    user = User(
        email="admin@testschool.edu.gh",
        password_hash=hash_password("TestPass123!"),
        system_role="SCHOOL_STAFF",
        school_id=test_school.id,
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    role = UserRole(
        user_id=user.id,
        role_id=admin_position.id,
        assigned_at=datetime.now(UTC),
    )
    session.add(role)
    await session.commit()
    return user


@pytest_asyncio.fixture
async def superadmin_user(session: AsyncSession) -> User:
    user = User(
        email="super@ttek.io",
        password_hash=hash_password("SuperPass123!"),
        system_role="SUPERADMIN",
        school_id=None,
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()
    return user
