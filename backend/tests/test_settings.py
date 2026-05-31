"""
Integration tests for /api/v1/settings/* endpoints.
Covers school profile, academic years, academic terms, and school subjects.
"""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.user import User


def _bearer(user: User) -> dict[str, str]:
    token = create_access_token(
        str(user.id),
        str(user.school_id) if user.school_id else None,
        user.system_role,
    )
    return {"Authorization": f"Bearer {token}"}


# ── School profile ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_school_returns_profile(client: AsyncClient, admin_user: User) -> None:
    r = await client.get("/api/v1/settings/school", headers=_bearer(admin_user))
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Test School"
    assert body["code"] == "TST001"


@pytest.mark.asyncio
async def test_patch_school_updates_name(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.patch(
        "/api/v1/settings/school",
        json={"name": "Renamed School"},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed School"


@pytest.mark.asyncio
async def test_patch_school_requires_permission(client: AsyncClient, admin_user: User) -> None:
    """admin_user with no PositionPermissions gets 403."""
    r = await client.patch(
        "/api/v1/settings/school",
        json={"name": "Should Fail"},
        headers=_bearer(admin_user),
    )
    assert r.status_code == 403


# ── Academic years ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_academic_years_empty(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.get("/api/v1/settings/academic-years", headers=_bearer(admin_user_all_perms))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["items"] == []


@pytest.mark.asyncio
async def test_create_academic_year(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "2025/2026"
    assert body["is_current"] is False


@pytest.mark.asyncio
async def test_create_duplicate_academic_year_returns_409(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    payload = {"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"}
    await client.post("/api/v1/settings/academic-years", json=payload, headers=headers)
    r = await client.post("/api/v1/settings/academic-years", json=payload, headers=headers)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_update_academic_year(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    created = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"},
        headers=headers,
    )).json()
    r = await client.patch(
        f"/api/v1/settings/academic-years/{created['id']}",
        json={"name": "2025-2026 Updated"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["name"] == "2025-2026 Updated"


@pytest.mark.asyncio
async def test_activate_academic_year_clears_others(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    year1_id = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2024/2025", "start_date": "2024-09-01", "end_date": "2025-06-30"},
        headers=headers,
    )).json()["id"]
    year2_id = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"},
        headers=headers,
    )).json()["id"]

    await client.post(f"/api/v1/settings/academic-years/{year1_id}/activate", headers=headers)
    r = await client.post(f"/api/v1/settings/academic-years/{year2_id}/activate", headers=headers)
    assert r.status_code == 200
    assert r.json()["is_current"] is True

    items = {i["id"]: i for i in (
        await client.get("/api/v1/settings/academic-years", headers=headers)
    ).json()["items"]}
    assert items[year1_id]["is_current"] is False
    assert items[year2_id]["is_current"] is True


@pytest.mark.asyncio
async def test_delete_inactive_academic_year(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    year_id = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2023/2024", "start_date": "2023-09-01", "end_date": "2024-06-30"},
        headers=headers,
    )).json()["id"]
    r = await client.delete(f"/api/v1/settings/academic-years/{year_id}", headers=headers)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_delete_current_academic_year_returns_400(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    year_id = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"},
        headers=headers,
    )).json()["id"]
    await client.post(f"/api/v1/settings/academic-years/{year_id}/activate", headers=headers)
    r = await client.delete(f"/api/v1/settings/academic-years/{year_id}", headers=headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_academic_years_requires_permission(
    client: AsyncClient, admin_user: User
) -> None:
    r = await client.get("/api/v1/settings/academic-years", headers=_bearer(admin_user))
    assert r.status_code == 403


# ── Academic terms ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_term(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    year_id = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"},
        headers=headers,
    )).json()["id"]
    r = await client.post(
        f"/api/v1/settings/academic-years/{year_id}/terms",
        json={"name": "Term 1", "start_date": "2025-09-01", "end_date": "2025-12-15"},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["name"] == "Term 1"
    assert r.json()["is_current"] is False


@pytest.mark.asyncio
async def test_duplicate_term_returns_409(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    year_id = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"},
        headers=headers,
    )).json()["id"]
    payload = {"name": "Term 1", "start_date": "2025-09-01", "end_date": "2025-12-15"}
    await client.post(f"/api/v1/settings/academic-years/{year_id}/terms", json=payload, headers=headers)
    r = await client.post(f"/api/v1/settings/academic-years/{year_id}/terms", json=payload, headers=headers)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_activate_term_deactivates_siblings(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    year_id = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"},
        headers=headers,
    )).json()["id"]
    t1_id = (await client.post(
        f"/api/v1/settings/academic-years/{year_id}/terms",
        json={"name": "Term 1", "start_date": "2025-09-01", "end_date": "2025-12-15"},
        headers=headers,
    )).json()["id"]
    t2_id = (await client.post(
        f"/api/v1/settings/academic-years/{year_id}/terms",
        json={"name": "Term 2", "start_date": "2026-01-10", "end_date": "2026-04-15"},
        headers=headers,
    )).json()["id"]

    await client.post(f"/api/v1/settings/terms/{t1_id}/activate", headers=headers)
    r = await client.post(f"/api/v1/settings/terms/{t2_id}/activate", headers=headers)
    assert r.status_code == 200
    assert r.json()["is_current"] is True


@pytest.mark.asyncio
async def test_update_term(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    year_id = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"},
        headers=headers,
    )).json()["id"]
    term_id = (await client.post(
        f"/api/v1/settings/academic-years/{year_id}/terms",
        json={"name": "Term 1", "start_date": "2025-09-01", "end_date": "2025-12-15"},
        headers=headers,
    )).json()["id"]
    r = await client.patch(
        f"/api/v1/settings/terms/{term_id}",
        json={"name": "First Term"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["name"] == "First Term"


@pytest.mark.asyncio
async def test_delete_current_term_returns_400(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    year_id = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"},
        headers=headers,
    )).json()["id"]
    term_id = (await client.post(
        f"/api/v1/settings/academic-years/{year_id}/terms",
        json={"name": "Term 1", "start_date": "2025-09-01", "end_date": "2025-12-15"},
        headers=headers,
    )).json()["id"]
    await client.post(f"/api/v1/settings/terms/{term_id}/activate", headers=headers)
    r = await client.delete(f"/api/v1/settings/terms/{term_id}", headers=headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_delete_inactive_term(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    year_id = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"},
        headers=headers,
    )).json()["id"]
    term_id = (await client.post(
        f"/api/v1/settings/academic-years/{year_id}/terms",
        json={"name": "Term 1", "start_date": "2025-09-01", "end_date": "2025-12-15"},
        headers=headers,
    )).json()["id"]
    r = await client.delete(f"/api/v1/settings/terms/{term_id}", headers=headers)
    assert r.status_code == 204


# ── School subjects ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_subjects_empty(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.get("/api/v1/settings/subjects", headers=_bearer(admin_user_all_perms))
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_subject(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.post(
        "/api/v1/settings/subjects",
        json={"name": "Mathematics", "code": "MATH"},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Mathematics"
    assert body["code"] == "MATH"


@pytest.mark.asyncio
async def test_created_subject_appears_in_list(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    await client.post("/api/v1/settings/subjects", json={"name": "Mathematics"}, headers=headers)
    await client.post("/api/v1/settings/subjects", json={"name": "English"}, headers=headers)
    r = await client.get("/api/v1/settings/subjects", headers=headers)
    names = [s["name"] for s in r.json()]
    assert "Mathematics" in names
    assert "English" in names
    assert len(names) == 2


@pytest.mark.asyncio
async def test_duplicate_subject_returns_409(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    await client.post("/api/v1/settings/subjects", json={"name": "Mathematics"}, headers=headers)
    r = await client.post("/api/v1/settings/subjects", json={"name": "Mathematics"}, headers=headers)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_update_subject(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    subject_id = (await client.post(
        "/api/v1/settings/subjects",
        json={"name": "Maths", "code": "MTH"},
        headers=headers,
    )).json()["id"]
    r = await client.patch(
        f"/api/v1/settings/subjects/{subject_id}",
        json={"name": "Mathematics"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Mathematics"


@pytest.mark.asyncio
async def test_delete_subject(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    subject_id = (await client.post(
        "/api/v1/settings/subjects",
        json={"name": "Science"},
        headers=headers,
    )).json()["id"]
    r = await client.delete(f"/api/v1/settings/subjects/{subject_id}", headers=headers)
    assert r.status_code == 204
    assert (await client.get("/api/v1/settings/subjects", headers=headers)).json() == []


@pytest.mark.asyncio
async def test_subjects_require_permission(client: AsyncClient, admin_user: User) -> None:
    r = await client.get("/api/v1/settings/subjects", headers=_bearer(admin_user))
    assert r.status_code == 403
