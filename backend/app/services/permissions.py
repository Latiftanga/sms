"""
Permission resolver — three-layer resolution:
  1. SUPERADMIN → bypass all checks (hardcoded)
  2. StaffPermission (personal override) → explicit grant/deny per user
  3. UserRole → union of PositionPermission across ALL assigned roles
  4. No match → denied

Union semantics: if ANY assigned role grants a permission, it is granted.
A personal override (granted=False) can still explicitly deny it.

Results are cached in Redis for PERMISSION_CACHE_TTL seconds.
Cache is invalidated immediately on any StaffPermission or UserRole write.
"""
import json
import logging
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.permissions import ALL_PERMISSIONS, Permission
from app.models.staff import PositionPermission, StaffPermission
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "perm"


def _cache_key(user_id: str | UUID) -> str:
    return f"{_CACHE_PREFIX}:{user_id}"


async def resolve_all_permissions(
    user: User,
    redis: Redis,
    session: AsyncSession,
) -> dict[str, bool]:
    """
    Return the full permission map for a user.
    Cached in Redis; loads from DB on cache miss.
    SUPERADMIN always returns all True without a DB hit.
    """
    if user.system_role == "SUPERADMIN":
        return {p: True for p in ALL_PERMISSIONS}

    key = _cache_key(user.id)
    cached = await redis.get(key)
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            pass  # stale/corrupt entry — fall through to DB

    perms = await _load_from_db(user, session)
    await redis.setex(key, settings.PERMISSION_CACHE_TTL, json.dumps(perms))
    return perms


async def check_permission(
    user: User,
    permission: Permission | str,
    redis: Redis,
    session: AsyncSession,
) -> bool:
    """Single-permission check. Uses the cached full map."""
    if user.system_role == "SUPERADMIN":
        return True
    if user.system_role in ("STUDENT", "PARENT"):
        return False

    perms = await resolve_all_permissions(user, redis, session)
    return perms.get(str(permission), False)


async def invalidate_cache(user_id: str | UUID, redis: Redis) -> None:
    """Call whenever StaffPermission or UserRole changes."""
    await redis.delete(_cache_key(user_id))


# ─────────────────────────────────────────────────────────────────────────────
# Internal
# ─────────────────────────────────────────────────────────────────────────────

async def _load_from_db(user: User, session: AsyncSession) -> dict[str, bool]:
    """
    Build the full permission map from DB.

    Resolution order (highest priority first):
      1. Personal override (StaffPermission) — explicit grant or deny
      2. Role union (UserRole → PositionPermission) — if ANY role grants it
      3. Default deny
    """
    # 1. Personal overrides — one query
    override_rows = await session.execute(
        select(StaffPermission.permission_key, StaffPermission.granted).where(
            StaffPermission.staff_member_id == user.staff_member_id,
            StaffPermission.school_id == user.school_id,
        )
    )
    overrides: dict[str, bool] = {row.permission_key: row.granted for row in override_rows}

    # 2. Union of all role permissions — one JOIN query across all assigned roles
    role_rows = await session.execute(
        select(PositionPermission.permission_key, PositionPermission.granted)
        .join(UserRole, UserRole.role_id == PositionPermission.position_id)
        .where(UserRole.user_id == user.id)
    )
    # Union: once any role grants a key, it stays granted
    role_grants: dict[str, bool] = {}
    for row in role_rows:
        if row.permission_key not in role_grants or row.granted:
            role_grants[row.permission_key] = row.granted

    # 3. Merge: personal override wins, then role union, then deny
    return {
        perm_key: (
            overrides[perm_key]
            if perm_key in overrides
            else role_grants.get(perm_key, False)
        )
        for perm_key in ALL_PERMISSIONS
    }
