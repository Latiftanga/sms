"""
Integration tests for /api/v1/staff/* endpoints.
Covers CRUD, permission guards, and the invite flow.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User
from app.models.school import School


def _bearer(user: User) -> dict[str, str]:
    token = create_access_token(
        str(user.id),
        str(user.school_id) if user.school_id else None,
        user.system_role,
    )
    return {"Authorization": f"Bearer {token}"}


_CREATE_PAYLOAD = {
    "first_name": "Kwame",
    "last_name": "Mensah",
    "category": "TEACHING",
    "employment_type": "PERMANENT",
}


# ── List staff ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_staff_empty(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.get("/api/v1/staff", headers=_bearer(admin_user_all_perms))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["items"] == []


@pytest.mark.asyncio
async def test_list_staff_requires_view_staff(client: AsyncClient, admin_user: User) -> None:
    """admin_user with no PositionPermissions gets 403."""
    r = await client.get("/api/v1/staff", headers=_bearer(admin_user))
    assert r.status_code == 403


# ── Create staff ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_staff_returns_201(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.post("/api/v1/staff", json=_CREATE_PAYLOAD, headers=_bearer(admin_user_all_perms))
    assert r.status_code == 201
    body = r.json()
    assert body["first_name"] == "Kwame"
    assert body["last_name"] == "Mensah"
    assert body["category"] == "TEACHING"
    assert "id" in body


@pytest.mark.asyncio
async def test_create_staff_non_teaching(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.post(
        "/api/v1/staff",
        json={**_CREATE_PAYLOAD, "category": "NON-TEACHING"},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 201
    assert r.json()["category"] == "NON-TEACHING"


@pytest.mark.asyncio
async def test_create_staff_invalid_category_returns_422(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    r = await client.post(
        "/api/v1/staff",
        json={**_CREATE_PAYLOAD, "category": "JANITOR"},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_staff_invalid_employment_type_returns_422(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    r = await client.post(
        "/api/v1/staff",
        json={**_CREATE_PAYLOAD, "employment_type": "FREELANCE"},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_staff_requires_manage_staff(
    client: AsyncClient, admin_user: User
) -> None:
    r = await client.post("/api/v1/staff", json=_CREATE_PAYLOAD, headers=_bearer(admin_user))
    assert r.status_code == 403


# ── Get staff ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_staff_returns_detail(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    created = (await client.post("/api/v1/staff", json=_CREATE_PAYLOAD, headers=headers)).json()
    r = await client.get(f"/api/v1/staff/{created['id']}", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == created["id"]
    assert body["first_name"] == "Kwame"
    assert body["last_name"] == "Mensah"


@pytest.mark.asyncio
async def test_get_staff_not_found_returns_404(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    r = await client.get(
        "/api/v1/staff/00000000-0000-0000-0000-000000000000",
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_staff_requires_view_staff(client: AsyncClient, admin_user: User) -> None:
    r = await client.get(
        "/api/v1/staff/00000000-0000-0000-0000-000000000000",
        headers=_bearer(admin_user),
    )
    assert r.status_code == 403


# ── Update staff ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_staff_name(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    created = (await client.post("/api/v1/staff", json=_CREATE_PAYLOAD, headers=headers)).json()
    r = await client.patch(
        f"/api/v1/staff/{created['id']}",
        json={"first_name": "Kofi"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["first_name"] == "Kofi"
    assert r.json()["last_name"] == "Mensah"


@pytest.mark.asyncio
async def test_update_staff_category(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    created = (await client.post("/api/v1/staff", json=_CREATE_PAYLOAD, headers=headers)).json()
    r = await client.patch(
        f"/api/v1/staff/{created['id']}",
        json={"category": "NON-TEACHING"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["category"] == "NON-TEACHING"


# ── Deactivate / reactivate staff ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deactivate_staff_returns_204(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    created = (await client.post("/api/v1/staff", json=_CREATE_PAYLOAD, headers=headers)).json()
    r = await client.delete(f"/api/v1/staff/{created['id']}", headers=headers)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_deactivate_staff_not_found_returns_404(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    r = await client.delete(
        "/api/v1/staff/00000000-0000-0000-0000-000000000000",
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 404


# ── Staff appears in list ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_created_staff_appears_in_list(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    await client.post("/api/v1/staff", json=_CREATE_PAYLOAD, headers=headers)
    await client.post(
        "/api/v1/staff",
        json={**_CREATE_PAYLOAD, "first_name": "Ama", "last_name": "Boateng"},
        headers=headers,
    )
    r = await client.get("/api/v1/staff", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    names = [m["first_name"] for m in body["items"]]
    assert "Kwame" in names
    assert "Ama" in names


@pytest.mark.asyncio
async def test_deactivated_staff_excluded_from_active_filter(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    created = (await client.post("/api/v1/staff", json=_CREATE_PAYLOAD, headers=headers)).json()
    await client.delete(f"/api/v1/staff/{created['id']}", headers=headers)
    # Default list includes all; filtered by is_active=true excludes deactivated
    assert (await client.get("/api/v1/staff", headers=headers)).json()["total"] == 1
    assert (await client.get("/api/v1/staff?is_active=true", headers=headers)).json()["total"] == 0
    assert (await client.get("/api/v1/staff?is_active=false", headers=headers)).json()["total"] == 1


# ── Invite ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invite_staff_creates_user(
    client: AsyncClient,
    admin_user_all_perms: User,
    session: AsyncSession,
) -> None:
    headers = _bearer(admin_user_all_perms)
    staff_id = (await client.post("/api/v1/staff", json=_CREATE_PAYLOAD, headers=headers)).json()["id"]
    r = await client.post(
        f"/api/v1/staff/{staff_id}/invite",
        json={"email": "kwame.mensah@testschool.edu.gh", "role_codes": []},
        headers=headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert "invite_token" in body or "email" in body


@pytest.mark.asyncio
async def test_invite_staff_resend_returns_201(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    """Re-inviting a pending (inactive) account is a valid resend — returns 201 with a new token."""
    headers = _bearer(admin_user_all_perms)
    staff_id = (await client.post("/api/v1/staff", json=_CREATE_PAYLOAD, headers=headers)).json()["id"]
    invite_payload = {"email": "kwame.mensah@testschool.edu.gh", "role_codes": []}
    r1 = await client.post(f"/api/v1/staff/{staff_id}/invite", json=invite_payload, headers=headers)
    r2 = await client.post(f"/api/v1/staff/{staff_id}/invite", json=invite_payload, headers=headers)
    assert r1.status_code == 201
    assert r2.status_code == 201
    # Each resend issues a fresh token
    assert r1.json()["invite_token"] != r2.json()["invite_token"]


@pytest.mark.asyncio
async def test_invite_email_used_by_different_user_returns_409(
    client: AsyncClient,
    admin_user_all_perms: User,
    session: AsyncSession,
    test_school,
) -> None:
    """An email already in use by a different user should be rejected."""
    from app.core.security import hash_password
    from app.models.user import User as UserModel

    headers = _bearer(admin_user_all_perms)
    # Create an unrelated user with the target email
    existing = UserModel(
        email="taken@testschool.edu.gh",
        password_hash=hash_password("Pass123!"),
        system_role="SCHOOL_STAFF",
        school_id=test_school.id,
        is_active=True,
        is_verified=True,
    )
    session.add(existing)
    await session.commit()

    staff_id = (await client.post("/api/v1/staff", json=_CREATE_PAYLOAD, headers=headers)).json()["id"]
    r = await client.post(
        f"/api/v1/staff/{staff_id}/invite",
        json={"email": "taken@testschool.edu.gh", "role_codes": []},
        headers=headers,
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_invite_requires_manage_users(client: AsyncClient, admin_user: User) -> None:
    r = await client.post(
        "/api/v1/staff/00000000-0000-0000-0000-000000000000/invite",
        json={"email": "someone@school.edu.gh", "role_codes": []},
        headers=_bearer(admin_user),
    )
    assert r.status_code == 403
