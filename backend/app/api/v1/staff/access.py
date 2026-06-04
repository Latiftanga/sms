from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, RedisDep, SessionDep, require
from app.api.v1.staff._helpers import _get_member, _linked_user
from app.core.permissions import ALL_PERMISSIONS, Permission
from app.models.staff import StaffPermission, StaffPosition
from app.models.user import User, UserRole
from app.schemas.staff import (
    PermissionOverrideCreate,
    PermissionOverrideResponse,
    RoleAssignRequest,
    RoleResponse,
    StaffPermissionsResponse,
    UserRoleResponse,
)
from app.services.permissions import invalidate_cache, resolve_all_permissions

router = APIRouter()


# ── Permissions ───────────────────────────────────────────────────────────────

@router.get("/{staff_id}/permissions", response_model=StaffPermissionsResponse,
            dependencies=[require(Permission.MANAGE_USERS)])
async def get_staff_permissions(
    staff_id: UUID,
    user: CurrentUser,
    redis: RedisDep,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)

    overrides = list(await session.scalars(
        select(StaffPermission).where(
            StaffPermission.staff_member_id == member.id,
            StaffPermission.school_id == user.school_id,
        )
    ))

    linked = await _linked_user(member, session)
    resolved = await resolve_all_permissions(linked, redis, session) if linked else {}

    role_rows: list[UserRoleResponse] = []
    if linked:
        ur_rows = list(await session.scalars(
            select(UserRole).where(UserRole.user_id == linked.id).options(
                selectinload(UserRole.role)
            )
        ))
        role_rows = [
            UserRoleResponse(
                id=ur.id,
                role=RoleResponse(
                    id=ur.role.id,
                    name=ur.role.name,
                    code=ur.role.code,
                    is_system_template=ur.role.is_system_template,
                ),
                assigned_at=ur.assigned_at,
            )
            for ur in ur_rows
        ]

    return StaffPermissionsResponse(
        staff_member_id=member.id,
        roles=role_rows,
        permissions=resolved,
        overrides=[PermissionOverrideResponse.model_validate(o) for o in overrides],
    )


@router.post("/{staff_id}/permissions", response_model=PermissionOverrideResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_USERS)])
async def set_permission_override(
    staff_id: UUID,
    body: PermissionOverrideCreate,
    user: CurrentUser,
    redis: RedisDep,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)

    if body.permission_key not in ALL_PERMISSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown permission: {body.permission_key}")

    existing = await session.scalar(
        select(StaffPermission).where(
            StaffPermission.staff_member_id == member.id,
            StaffPermission.school_id == user.school_id,
            StaffPermission.permission_key == body.permission_key,
        )
    )

    now = datetime.now(UTC)
    if existing:
        existing.granted = body.granted
        existing.note = body.note
        existing.granted_by = user.id
        existing.granted_at = now
        override = existing
    else:
        override = StaffPermission(
            staff_member_id=member.id,
            school_id=user.school_id,
            permission_key=body.permission_key,
            granted=body.granted,
            granted_by=user.id,
            granted_at=now,
            note=body.note,
        )
        session.add(override)

    await session.commit()
    await session.refresh(override)

    linked = await _linked_user(member, session)
    if linked:
        await invalidate_cache(linked.id, redis)

    return PermissionOverrideResponse.model_validate(override)


@router.delete("/{staff_id}/permissions/{perm_key}", status_code=204,
               dependencies=[require(Permission.MANAGE_USERS)])
async def remove_permission_override(
    staff_id: UUID,
    perm_key: str,
    user: CurrentUser,
    redis: RedisDep,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)

    override = await session.scalar(
        select(StaffPermission).where(
            StaffPermission.staff_member_id == member.id,
            StaffPermission.school_id == user.school_id,
            StaffPermission.permission_key == perm_key,
        )
    )
    if not override:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Permission override not found")

    await session.delete(override)
    await session.commit()

    linked = await _linked_user(member, session)
    if linked:
        await invalidate_cache(linked.id, redis)


# ── Roles ─────────────────────────────────────────────────────────────────────

@router.get("/{staff_id}/roles", response_model=list[UserRoleResponse],
            dependencies=[require(Permission.MANAGE_USERS)])
async def list_roles(staff_id: UUID, user: CurrentUser, session: SessionDep):
    member = await _get_member(staff_id, user.school_id, session)
    linked = await _linked_user(member, session)
    if not linked:
        return []
    rows = list(await session.scalars(
        select(UserRole).where(UserRole.user_id == linked.id)
        .options(selectinload(UserRole.role))
    ))
    return [
        UserRoleResponse(
            id=ur.id,
            role=RoleResponse(
                id=ur.role.id, name=ur.role.name,
                code=ur.role.code, is_system_template=ur.role.is_system_template,
            ),
            assigned_at=ur.assigned_at,
        )
        for ur in rows
    ]


@router.post("/{staff_id}/roles", response_model=UserRoleResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_USERS)])
async def assign_role(
    staff_id: UUID,
    body: RoleAssignRequest,
    user: CurrentUser,
    redis: RedisDep,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    linked = await _linked_user(member, session)
    if not linked:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No user account linked to this staff member")

    role = await session.scalar(
        select(StaffPosition).where(
            StaffPosition.id == body.role_id,
            (StaffPosition.is_system_template.is_(True)) | (StaffPosition.school_id == user.school_id),
        )
    )
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")

    existing = await session.scalar(
        select(UserRole).where(UserRole.user_id == linked.id, UserRole.role_id == body.role_id)
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Role already assigned")

    ur = UserRole(
        user_id=linked.id,
        role_id=body.role_id,
        assigned_by=user.id,
        assigned_at=datetime.now(UTC),
    )
    session.add(ur)
    await session.commit()
    await session.refresh(ur)
    await invalidate_cache(linked.id, redis)

    return UserRoleResponse(
        id=ur.id,
        role=RoleResponse(
            id=role.id, name=role.name,
            code=role.code, is_system_template=role.is_system_template,
        ),
        assigned_at=ur.assigned_at,
    )


@router.delete("/{staff_id}/roles/{user_role_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_USERS)])
async def remove_role(
    staff_id: UUID,
    user_role_id: UUID,
    user: CurrentUser,
    redis: RedisDep,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    linked = await _linked_user(member, session)
    if not linked:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No user account linked to this staff member")

    ur = await session.scalar(
        select(UserRole).where(UserRole.id == user_role_id, UserRole.user_id == linked.id)
    )
    if not ur:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role assignment not found")

    await session.delete(ur)
    await session.commit()
    await invalidate_cache(linked.id, redis)
