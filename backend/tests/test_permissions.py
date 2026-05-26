"""
Permission resolver unit tests.
These test the 3-layer resolution logic in isolation — no HTTP calls needed.
"""
import json
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission
from app.models.staff import PositionPermission, StaffPermission, StaffPosition
from app.models.user import User
from app.services.permissions import check_permission, resolve_all_permissions


@pytest.mark.asyncio
async def test_superadmin_bypasses_all(mock_redis: AsyncMock, session: AsyncSession) -> None:
    user = User(system_role="SUPERADMIN", email="s@t.io", password_hash="x")
    result = await resolve_all_permissions(user, mock_redis, session)
    assert all(result.values()), "SUPERADMIN must have all permissions True"
    # Should NOT hit Redis or DB
    mock_redis.get.assert_not_called()


@pytest.mark.asyncio
async def test_student_denied(mock_redis: AsyncMock, session: AsyncSession) -> None:
    user = User(system_role="STUDENT", email="s@t.io", password_hash="x")
    allowed = await check_permission(user, Permission.VIEW_SCORES, mock_redis, session)
    assert allowed is False


@pytest.mark.asyncio
async def test_parent_denied(mock_redis: AsyncMock, session: AsyncSession) -> None:
    user = User(system_role="PARENT", email="p@t.io", password_hash="x")
    allowed = await check_permission(user, Permission.ENTER_SCORES, mock_redis, session)
    assert allowed is False


@pytest.mark.asyncio
async def test_cache_hit(mock_redis: AsyncMock, session: AsyncSession, admin_user: User) -> None:
    # Seed the cache with a pre-built permission map
    cached_perms = {p: True for p in [str(Permission.VIEW_STUDENTS)]}
    mock_redis.get.return_value = json.dumps(cached_perms)

    result = await resolve_all_permissions(admin_user, mock_redis, session)
    assert result.get(str(Permission.VIEW_STUDENTS)) is True
    mock_redis.get.assert_called_once()


@pytest.mark.asyncio
async def test_position_template_grant(
    session: AsyncSession, mock_redis: AsyncMock,
    admin_user: User, admin_position: StaffPosition
) -> None:
    """Staff with a position that has VIEW_STUDENTS = True should get it."""
    perm = PositionPermission(
        position_id=admin_position.id,
        permission_key=str(Permission.VIEW_STUDENTS),
        granted=True,
    )
    session.add(perm)
    await session.flush()

    admin_user.position_id = admin_position.id
    admin_user.staff_member_id = None  # no personal overrides

    mock_redis.get.return_value = None  # cache miss

    result = await resolve_all_permissions(admin_user, mock_redis, session)
    assert result[str(Permission.VIEW_STUDENTS)] is True


@pytest.mark.asyncio
async def test_personal_override_beats_position(
    session: AsyncSession, mock_redis: AsyncMock,
    admin_user: User, admin_position: StaffPosition,
    test_school,
) -> None:
    """StaffPermission override = False should override position = True."""
    from app.models.staff import StaffMember
    from datetime import UTC, datetime

    # Create a staff member
    staff = StaffMember(
        school_id=test_school.id,
        first_name="Kofi", last_name="Mensah",
        category="TEACHING",
    )
    session.add(staff)
    await session.flush()

    # Position says granted
    pos_perm = PositionPermission(
        position_id=admin_position.id,
        permission_key=str(Permission.ENTER_SCORES),
        granted=True,
    )
    session.add(pos_perm)

    # Personal override says denied
    override = StaffPermission(
        staff_member_id=staff.id,
        school_id=test_school.id,
        permission_key=str(Permission.ENTER_SCORES),
        granted=False,
        granted_by=admin_user.id,
        granted_at=datetime.now(UTC),
        note="Suspended from score entry",
    )
    session.add(override)
    await session.flush()

    admin_user.staff_member_id = staff.id
    admin_user.position_id = admin_position.id
    mock_redis.get.return_value = None

    result = await resolve_all_permissions(admin_user, mock_redis, session)
    assert result[str(Permission.ENTER_SCORES)] is False, (
        "Personal override (False) must beat position template (True)"
    )
