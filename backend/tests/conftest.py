"""
Pytest fixtures for async FastAPI + SQLAlchemy + Redis tests.
Uses a real PostgreSQL test DB (not mocks) — aligns with the production behaviour requirement.
"""
import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.db import get_session
from app.core.redis import get_redis
from app.main import app
from app.models.base import Base


# Use a separate test database — ensure DATABASE_URL points to it in CI
TEST_DATABASE_URL = settings.DATABASE_URL


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Rolls back every test — no leftover data between tests."""
    async with db_engine.begin() as conn:
        session_factory = async_sessionmaker(bind=conn, expire_on_commit=False)
        async with session_factory() as sess:
            yield sess
            await sess.rollback()


@pytest.fixture
def mock_redis() -> AsyncMock:
    """In-memory mock Redis — tests should not depend on a real Redis instance."""
    redis = AsyncMock()
    redis.get.return_value = None
    redis.setex.return_value = True
    redis.delete.return_value = 1
    redis.ping.return_value = True
    redis.incr.return_value = 1
    redis.expire.return_value = True
    return redis


@pytest_asyncio.fixture
async def client(session: AsyncSession, mock_redis: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    """Test client with DB session and Redis overridden."""

    async def override_session():
        yield session

    def override_redis():
        return mock_redis

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ── Test data factories ───────────────────────────────────────────

from app.core.security import hash_password
from app.models.user import User
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
    await session.flush()
    return school


@pytest_asyncio.fixture
async def admin_position(session: AsyncSession) -> StaffPosition:
    pos = StaffPosition(
        school_id=None, name="Admin", code="ADMIN", is_system_template=True
    )
    session.add(pos)
    await session.flush()
    return pos


@pytest_asyncio.fixture
async def admin_user(session: AsyncSession, test_school: School, admin_position: StaffPosition) -> User:
    user = User(
        email="admin@testschool.edu.gh",
        password_hash=hash_password("TestPass123!"),
        system_role="SCHOOL_STAFF",
        school_id=test_school.id,
        position_id=admin_position.id,
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()
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
    await session.flush()
    return user
