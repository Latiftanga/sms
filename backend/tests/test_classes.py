"""
Integration tests for class-management endpoints in /api/v1/settings/.

Coverage:
  - Classes CRUD (Basic/Creche/Nursery/KG), duplicate guard, level validation
  - Class detail (empty state, with current year)
  - Class teacher: assign requires current year, replace, remove
  - Class subjects: list, add, duplicate code guard, update, delete
  - Subject teacher: assign to a subject, remove
  - Permission guard (403 without MANAGE_ACADEMIC_STRUCTURE)

Not tested here (no API endpoints yet):
  - Student enrolment
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User


def _bearer(user: User) -> dict[str, str]:
    token = create_access_token(
        str(user.id),
        str(user.school_id) if user.school_id else None,
        user.system_role,
    )
    return {"Authorization": f"Bearer {token}"}


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _create_class(client, headers, *, level="Basic", year=1, stream=None):
    payload = {"level": level, "year": year}
    if stream:
        payload["stream"] = stream
    r = await client.post("/api/v1/settings/classes", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


async def _create_year_and_activate(client, headers):
    year = (await client.post(
        "/api/v1/settings/academic-years",
        json={"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-06-30"},
        headers=headers,
    )).json()
    await client.post(f"/api/v1/settings/academic-years/{year['id']}/activate", headers=headers)
    return year


async def _create_staff(client, headers):
    return (await client.post(
        "/api/v1/staff",
        json={"first_name": "Kwame", "last_name": "Mensah", "category": "TEACHING"},
        headers=headers,
    )).json()


# ── List & create classes ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_classes_empty(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.get("/api/v1/settings/classes", headers=_bearer(admin_user_all_perms))
    assert r.status_code == 200
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_create_basic_class(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.post(
        "/api/v1/settings/classes",
        json={"level": "Basic", "year": 1},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 201
    body = r.json()
    assert body["level"] == "Basic"
    assert body["year"] == 1
    assert body["name"] == "Basic 1"
    assert body["is_active"] is True


@pytest.mark.asyncio
async def test_create_class_with_stream(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.post(
        "/api/v1/settings/classes",
        json={"level": "Basic", "year": 4, "stream": "A"},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 201
    body = r.json()
    assert body["stream"] == "A"
    assert body["name"] == "Basic 4A"


@pytest.mark.asyncio
async def test_create_creche_class(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.post(
        "/api/v1/settings/classes",
        json={"level": "Creche"},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 201
    assert r.json()["level"] == "Creche"
    assert r.json()["year"] is None


@pytest.mark.asyncio
async def test_create_kg_class(client: AsyncClient, admin_user_all_perms: User) -> None:
    r = await client.post(
        "/api/v1/settings/classes",
        json={"level": "KG", "year": 2},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 201
    assert r.json()["name"] == "KG 2"


@pytest.mark.asyncio
async def test_create_duplicate_class_returns_409(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    payload = {"level": "Basic", "year": 3}
    await client.post("/api/v1/settings/classes", json=payload, headers=headers)
    r = await client.post("/api/v1/settings/classes", json=payload, headers=headers)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_class_invalid_level_returns_422(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    r = await client.post(
        "/api/v1/settings/classes",
        json={"level": "Form", "year": 1},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_basic_class_year_out_of_bounds_returns_422(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    """Basic only allows years 1–9."""
    r = await client.post(
        "/api/v1/settings/classes",
        json={"level": "Basic", "year": 10},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_creche_with_year_returns_422(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    r = await client.post(
        "/api/v1/settings/classes",
        json={"level": "Creche", "year": 1},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_basic_without_year_returns_422(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    r = await client.post(
        "/api/v1/settings/classes",
        json={"level": "Basic"},
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_classes_after_creation(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    await _create_class(client, headers, level="Basic", year=1)
    await _create_class(client, headers, level="Basic", year=2)
    r = await client.get("/api/v1/settings/classes", headers=headers)
    assert r.json()["total"] == 2


# ── Update & delete ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_class_stream(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    r = await client.patch(
        f"/api/v1/settings/classes/{cls['id']}",
        json={"stream": "Gold"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["stream"] == "Gold"


@pytest.mark.asyncio
async def test_deactivate_class(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    r = await client.patch(
        f"/api/v1/settings/classes/{cls['id']}",
        json={"is_active": False},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_class(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    r = await client.delete(f"/api/v1/settings/classes/{cls['id']}", headers=headers)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_delete_class_not_found_returns_404(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    r = await client.delete(
        "/api/v1/settings/classes/00000000-0000-0000-0000-000000000000",
        headers=_bearer(admin_user_all_perms),
    )
    assert r.status_code == 404


# ── Class detail ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_class_detail_no_year(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    """Without a current year, detail returns no teacher, no student count, no year context."""
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    r = await client.get(f"/api/v1/settings/classes/{cls['id']}/detail", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["class_teacher"] is None
    assert body["student_count"] == 0
    assert body["current_year_id"] is None
    assert body["subjects"] == []


# ── Class teacher ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_assign_class_teacher_without_current_year_returns_400(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    staff = await _create_staff(client, headers)
    r = await client.put(
        f"/api/v1/settings/classes/{cls['id']}/teacher",
        json={"staff_member_id": staff["id"]},
        headers=headers,
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_assign_class_teacher_with_current_year(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    staff = await _create_staff(client, headers)
    await _create_year_and_activate(client, headers)

    r = await client.put(
        f"/api/v1/settings/classes/{cls['id']}/teacher",
        json={"staff_member_id": staff["id"]},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["class_teacher"] is not None
    assert body["class_teacher"]["staff_member_id"] == staff["id"]


@pytest.mark.asyncio
async def test_replace_class_teacher(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    staff1 = await _create_staff(client, headers)
    staff2 = (await client.post(
        "/api/v1/staff",
        json={"first_name": "Ama", "last_name": "Boateng", "category": "TEACHING"},
        headers=headers,
    )).json()
    await _create_year_and_activate(client, headers)

    await client.put(
        f"/api/v1/settings/classes/{cls['id']}/teacher",
        json={"staff_member_id": staff1["id"]},
        headers=headers,
    )
    r = await client.put(
        f"/api/v1/settings/classes/{cls['id']}/teacher",
        json={"staff_member_id": staff2["id"]},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["class_teacher"]["staff_member_id"] == staff2["id"]


@pytest.mark.asyncio
async def test_remove_class_teacher(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    staff = await _create_staff(client, headers)
    await _create_year_and_activate(client, headers)

    await client.put(
        f"/api/v1/settings/classes/{cls['id']}/teacher",
        json={"staff_member_id": staff["id"]},
        headers=headers,
    )
    r = await client.delete(f"/api/v1/settings/classes/{cls['id']}/teacher", headers=headers)
    assert r.status_code == 204

    detail = (await client.get(
        f"/api/v1/settings/classes/{cls['id']}/detail", headers=headers
    )).json()
    assert detail["class_teacher"] is None


# ── Class subjects ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_class_subjects_empty(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    r = await client.get(f"/api/v1/settings/classes/{cls['id']}/subjects", headers=headers)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_add_class_subject(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    r = await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects",
        json={"subject_name": "Mathematics", "subject_code": "MATH", "is_core": True},
        headers=headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["subject_name"] == "Mathematics"
    assert body["subject_code"] == "MATH"
    assert body["is_core"] is True
    assert body["teachers"] == []


@pytest.mark.asyncio
async def test_add_duplicate_subject_code_returns_409(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    payload = {"subject_name": "Mathematics", "subject_code": "MATH", "is_core": True}
    await client.post(f"/api/v1/settings/classes/{cls['id']}/subjects", json=payload, headers=headers)
    r = await client.post(f"/api/v1/settings/classes/{cls['id']}/subjects", json=payload, headers=headers)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_add_subjects_appear_in_list(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects",
        json={"subject_name": "Mathematics", "subject_code": "MATH", "is_core": True},
        headers=headers,
    )
    await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects",
        json={"subject_name": "English", "subject_code": "ENG", "is_core": True},
        headers=headers,
    )
    r = await client.get(f"/api/v1/settings/classes/{cls['id']}/subjects", headers=headers)
    assert len(r.json()) == 2


@pytest.mark.asyncio
async def test_update_class_subject(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    subj = (await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects",
        json={"subject_name": "Maths", "subject_code": "MTH", "is_core": True},
        headers=headers,
    )).json()
    r = await client.patch(
        f"/api/v1/settings/classes/{cls['id']}/subjects/{subj['id']}",
        json={"subject_name": "Mathematics", "is_core": False},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["subject_name"] == "Mathematics"
    assert r.json()["is_core"] is False


@pytest.mark.asyncio
async def test_delete_class_subject(client: AsyncClient, admin_user_all_perms: User) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    subj = (await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects",
        json={"subject_name": "Science", "subject_code": "SCI", "is_core": True},
        headers=headers,
    )).json()
    r = await client.delete(
        f"/api/v1/settings/classes/{cls['id']}/subjects/{subj['id']}",
        headers=headers,
    )
    assert r.status_code == 204
    assert (await client.get(
        f"/api/v1/settings/classes/{cls['id']}/subjects", headers=headers
    )).json() == []


# ── Subject teachers ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_assign_subject_teacher(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    subj = (await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects",
        json={"subject_name": "Mathematics", "subject_code": "MATH", "is_core": True},
        headers=headers,
    )).json()
    staff = await _create_staff(client, headers)
    await _create_year_and_activate(client, headers)

    r = await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects/{subj['id']}/teachers",
        json={"staff_member_id": staff["id"]},
        headers=headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["staff_member_id"] == staff["id"]


@pytest.mark.asyncio
async def test_assign_subject_teacher_no_year_returns_409(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    subj = (await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects",
        json={"subject_name": "Mathematics", "subject_code": "MATH", "is_core": True},
        headers=headers,
    )).json()
    staff = await _create_staff(client, headers)
    r = await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects/{subj['id']}/teachers",
        json={"staff_member_id": staff["id"]},
        headers=headers,
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_remove_subject_teacher(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    subj = (await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects",
        json={"subject_name": "Mathematics", "subject_code": "MATH", "is_core": True},
        headers=headers,
    )).json()
    staff = await _create_staff(client, headers)
    await _create_year_and_activate(client, headers)

    st = (await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects/{subj['id']}/teachers",
        json={"staff_member_id": staff["id"]},
        headers=headers,
    )).json()

    r = await client.delete(
        f"/api/v1/settings/classes/{cls['id']}/subjects/{subj['id']}/teachers/{st['id']}",
        headers=headers,
    )
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_assign_subject_teacher_appears_in_class_detail(
    client: AsyncClient, admin_user_all_perms: User
) -> None:
    headers = _bearer(admin_user_all_perms)
    cls = await _create_class(client, headers)
    subj = (await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects",
        json={"subject_name": "Mathematics", "subject_code": "MATH", "is_core": True},
        headers=headers,
    )).json()
    staff = await _create_staff(client, headers)
    await _create_year_and_activate(client, headers)

    await client.post(
        f"/api/v1/settings/classes/{cls['id']}/subjects/{subj['id']}/teachers",
        json={"staff_member_id": staff["id"]},
        headers=headers,
    )

    detail = (await client.get(
        f"/api/v1/settings/classes/{cls['id']}/detail", headers=headers
    )).json()
    subj_in_detail = next(s for s in detail["subjects"] if s["id"] == subj["id"])
    assert len(subj_in_detail["teachers"]) == 1
    assert subj_in_detail["teachers"][0]["staff_member_id"] == staff["id"]


# ── Permission guard ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_classes_require_manage_academic_structure(
    client: AsyncClient, admin_user: User
) -> None:
    """admin_user with no PositionPermissions gets 403."""
    r = await client.get("/api/v1/settings/classes", headers=_bearer(admin_user))
    assert r.status_code == 403
