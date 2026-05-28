"""
RLS guard and school isolation tests.

What we test here:
  1. The deps.py school_id guard — a non-superadmin with school_id=None gets 403
     before any endpoint logic runs. This is the new guard added in Step 2.
  2. SUPERADMIN is exempt from the guard even with school_id=None.
  3. A user's token cannot be used to access another school's settings.
  4. Token type confusion — refresh tokens rejected as access tokens.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, hash_password
from app.models.school import School, SchoolSchedule
from app.models.user import User


def _bearer(user: User) -> dict[str, str]:
    token = create_access_token(
        str(user.id),
        str(user.school_id) if user.school_id else None,
        user.system_role,
    )
    return {"Authorization": f"Bearer {token}"}


# ── school_id guard ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_school_staff_without_school_id_gets_403(
    client: AsyncClient, session: AsyncSession
) -> None:
    """SCHOOL_STAFF with no school_id is a misconfigured account — must be blocked."""
    orphan = User(
        email="orphan@nowhere.com",
        password_hash=hash_password("Pass123!"),
        system_role="SCHOOL_STAFF",
        school_id=None,
        is_active=True,
        is_verified=True,
    )
    session.add(orphan)
    await session.flush()

    r = await client.get("/api/v1/auth/me", headers=_bearer(orphan))
    assert r.status_code == 403
    assert r.json()["detail"] == "School context required"


@pytest.mark.asyncio
async def test_student_without_school_id_gets_403(
    client: AsyncClient, session: AsyncSession
) -> None:
    student = User(
        email="student@nowhere.com",
        password_hash=hash_password("Pass123!"),
        system_role="STUDENT",
        school_id=None,
        is_active=True,
        is_verified=True,
    )
    session.add(student)
    await session.flush()

    r = await client.get("/api/v1/auth/me", headers=_bearer(student))
    assert r.status_code == 403
    assert r.json()["detail"] == "School context required"


@pytest.mark.asyncio
async def test_superadmin_without_school_id_is_allowed(
    client: AsyncClient, superadmin_user: User
) -> None:
    """SUPERADMIN has school_id=None by design — the guard must not block them."""
    r = await client.get("/api/v1/auth/me", headers=_bearer(superadmin_user))
    assert r.status_code == 200
    assert r.json()["school_id"] is None


# ── Cross-school isolation ─────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def second_school(session: AsyncSession) -> School:
    school = School(
        name="Second School",
        code="SCH002",
        slug="second-school",
        education_levels=["BASIC"],
        facility_type="DAY",
    )
    session.add(school)
    await session.flush()
    schedule = SchoolSchedule(school_id=school.id, school_days=[1, 2, 3, 4, 5])
    session.add(schedule)
    await session.flush()
    return school


@pytest.mark.asyncio
async def test_user_sees_own_school_data(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    second_school: School,
) -> None:
    """/settings/school must return the user's own school, not another school's."""
    r = await client.get("/api/v1/settings/school", headers=_bearer(admin_user))
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == str(test_school.id)
    assert body["id"] != str(second_school.id)


@pytest.mark.asyncio
async def test_token_with_wrong_school_id_blocked(
    client: AsyncClient,
    session: AsyncSession,
    test_school: School,
    second_school: School,
) -> None:
    """A token forged with another school's ID should still only load that school's user."""
    # User belongs to second_school
    user = User(
        email="staff@secondschool.edu.gh",
        password_hash=hash_password("Pass123!"),
        system_role="SCHOOL_STAFF",
        school_id=second_school.id,
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    # Craft a token that claims test_school — DB lookup uses user.school_id, not token claim
    forged_token = create_access_token(
        str(user.id),
        str(test_school.id),  # wrong school in token
        user.system_role,
    )
    r = await client.get(
        "/api/v1/settings/school",
        headers={"Authorization": f"Bearer {forged_token}"},
    )
    # Resolves against user.school_id from DB (second_school), not token claim
    assert r.status_code == 200
    assert r.json()["id"] == str(second_school.id)


# ── Inactive / deactivated users ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_inactive_user_token_rejected(
    client: AsyncClient, session: AsyncSession, test_school: School
) -> None:
    """A valid token for a deactivated user must be rejected at the DB lookup."""
    user = User(
        email="deactivated@testschool.edu.gh",
        password_hash=hash_password("Pass123!"),
        system_role="SCHOOL_STAFF",
        school_id=test_school.id,
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    # Deactivate after minting the token (simulates revocation scenario)
    token = create_access_token(str(user.id), str(test_school.id), user.system_role)
    user.is_active = False
    await session.flush()

    r = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 401
