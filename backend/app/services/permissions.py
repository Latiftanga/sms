"""
Permission resolver — three-layer resolution:
  1. SUPERADMIN → bypass all checks (hardcoded)
  2. StaffPermission (personal override) → explicit grant/deny per user
  3. PositionPermission (template) → default for the assigned position
  4. No match → denied

Results are cached in Redis for PERMISSION_CACHE_TTL seconds.
Cache is invalidated immediately on any StaffPermission write.
"""
import json
import logging
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.permissions import ALL_PERMISSIONS, Permission
from app.models.staff import StaffPermission
from app.models.user import User

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
    """Call whenever StaffPermission or User.position_id changes."""
    await redis.delete(_cache_key(user_id))


# ─────────────────────────────────────────────────────────────────────────────
# Internal
# ─────────────────────────────────────────────────────────────────────────────

async def _load_from_db(user: User, session: AsyncSession) -> dict[str, bool]:
    """
    Build the full permission map from DB.
    StaffPermission (personal override) wins over PositionPermission (template).
    """
    # 1. Load personal overrides in a single query
    override_rows = await session.execute(
        select(StaffPermission.permission_key, StaffPermission.granted).where(
            StaffPermission.staff_member_id == user.staff_member_id,
            StaffPermission.school_id == user.school_id,
        )
    )
    overrides: dict[str, bool] = {row.permission_key: row.granted for row in override_rows}

    # 2. Load position template grants in a single query
    position_grants: dict[str, bool] = {}
    if user.position_id:
        from app.models.staff import PositionPermission
        pos_rows = await session.execute(
            select(PositionPermission.permission_key, PositionPermission.granted).where(
                PositionPermission.position_id == user.position_id
            )
        )
        position_grants = {row.permission_key: row.granted for row in pos_rows}

    # 3. Merge: override wins, then position template, then deny
    result: dict[str, bool] = {}
    for perm_key in ALL_PERMISSIONS:
        if perm_key in overrides:
            result[perm_key] = overrides[perm_key]
        elif perm_key in position_grants:
            result[perm_key] = position_grants[perm_key]
        else:
            result[perm_key] = False

    return result
