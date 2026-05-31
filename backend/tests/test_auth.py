"""
Auth endpoint integration tests — login, refresh, logout, /me.
Uses the real DB session (rolls back after each test) and mock Redis.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, hash_password
from app.models.user import User


def _bearer(user: User) -> dict[str, str]:
    token = create_access_token(
        str(user.id),
        str(user.school_id) if user.school_id else None,
        user.system_role,
    )
    return {"Authorization": f"Bearer {token}"}


# ── Login ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user: User) -> None:
    r = await client.post("/api/v1/auth/login", json={
        "email": "admin@testschool.edu.gh",
        "password": "TestPass123!",
    })
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "refresh_token" in r.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, admin_user: User) -> None:
    r = await client.post("/api/v1/auth/login", json={
        "email": "admin@testschool.edu.gh",
        "password": "WrongPassword!",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient) -> None:
    r = await client.post("/api/v1/auth/login", json={
        "email": "nobody@nowhere.com",
        "password": "anything",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(
    client: AsyncClient, session: AsyncSession, test_school
) -> None:
    user = User(
        email="inactive@testschool.edu.gh",
        password_hash=hash_password("Pass123!"),
        system_role="SCHOOL_STAFF",
        school_id=test_school.id,
        is_active=False,
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    r = await client.post("/api/v1/auth/login", json={
        "email": "inactive@testschool.edu.gh",
        "password": "Pass123!",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unverified_user(
    client: AsyncClient, session: AsyncSession, test_school
) -> None:
    user = User(
        email="unverified@testschool.edu.gh",
        password_hash=hash_password("Pass123!"),
        system_role="SCHOOL_STAFF",
        school_id=test_school.id,
        is_active=True,
        is_verified=False,
    )
    session.add(user)
    await session.commit()

    r = await client.post("/api/v1/auth/login", json={
        "email": "unverified@testschool.edu.gh",
        "password": "Pass123!",
    })
    assert r.status_code == 403


# ── Refresh ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient, admin_user: User) -> None:
    refresh_token = create_refresh_token(str(admin_user.id))
    r = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_token},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()
    # Rotation: a new refresh cookie should be issued
    assert "refresh_token" in r.cookies


@pytest.mark.asyncio
async def test_refresh_no_cookie(client: AsyncClient) -> None:
    r = await client.post("/api/v1/auth/refresh")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": "not.a.valid.token"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_access_token_rejected(
    client: AsyncClient, admin_user: User
) -> None:
    """Passing an access token as the refresh cookie must be rejected."""
    access_token = create_access_token(
        str(admin_user.id),
        str(admin_user.school_id) if admin_user.school_id else None,
        admin_user.system_role,
    )
    r = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": access_token},
    )
    assert r.status_code == 401


# ── Logout ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout(client: AsyncClient, admin_user: User) -> None:
    r = await client.post("/api/v1/auth/logout", headers=_bearer(admin_user))
    assert r.status_code == 200


# ── /me ────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    # Starlette's HTTPBearer(auto_error=True) returns 401 when Authorization header is absent
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token_rejected(client: AsyncClient) -> None:
    r = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.is.garbage"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_refresh_token_rejected(
    client: AsyncClient, admin_user: User
) -> None:
    """A refresh token must not be accepted where an access token is expected."""
    refresh_token = create_refresh_token(str(admin_user.id))
    r = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user_and_permissions(
    client: AsyncClient, admin_user: User
) -> None:
    r = await client.get("/api/v1/auth/me", headers=_bearer(admin_user))
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == admin_user.email
    assert body["system_role"] == "SCHOOL_STAFF"
    assert body["school_id"] == str(admin_user.school_id)
    assert isinstance(body["permissions"], dict)


@pytest.mark.asyncio
async def test_me_superadmin_has_all_permissions_true(
    client: AsyncClient, superadmin_user: User
) -> None:
    r = await client.get("/api/v1/auth/me", headers=_bearer(superadmin_user))
    assert r.status_code == 200
    body = r.json()
    assert body["system_role"] == "SUPERADMIN"
    assert body["school_id"] is None
    assert all(v is True for v in body["permissions"].values()), (
        "Every permission must be True for SUPERADMIN"
    )
