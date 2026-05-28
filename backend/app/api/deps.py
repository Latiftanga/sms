"""
FastAPI dependency injection — auth, DB session, Redis, permission guard.
"""
import json
import uuid as _uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session, set_rls_context
from app.core.permissions import Permission
from app.core.redis import get_redis
from app.core.security import decode_token
from app.models.user import User

_USER_CACHE_TTL = 300  # 5 minutes

bearer = HTTPBearer(auto_error=True)


# ── Database ──────────────────────────────────────────────────────

SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]


# ── Auth ──────────────────────────────────────────────────────────

def _user_from_cache(d: dict) -> User:
    """Reconstruct a detached User instance from cached dict (no DB needed)."""
    u = User.__new__(User)
    u.id = _uuid.UUID(d["id"])
    u.email = d["email"]
    u.system_role = d["system_role"]
    u.is_active = d["is_active"]
    u.must_change_password = d.get("must_change_password", False)
    u.school_id = _uuid.UUID(d["school_id"]) if d.get("school_id") else None
    u.staff_member_id = _uuid.UUID(d["staff_member_id"]) if d.get("staff_member_id") else None
    u.position_id = _uuid.UUID(d["position_id"]) if d.get("position_id") else None
    return u


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    session: SessionDep,
    redis: RedisDep,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except (JWTError, KeyError, ValueError):
        raise credentials_exception

    # ── Try Redis cache first — skip the DB round-trip on cache hit ───
    user: User | None = None
    cache_key = f"auth:user:{user_id}"
    try:
        raw = await redis.get(cache_key)
        if raw:
            user = _user_from_cache(json.loads(raw))
    except Exception:
        pass  # Redis unavailable — fall through to DB

    if user is None:
        user = await session.scalar(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        )
        if not user:
            raise credentials_exception
        # Populate cache for subsequent requests
        try:
            await redis.setex(cache_key, _USER_CACHE_TTL, json.dumps({
                "id": str(user.id),
                "email": user.email,
                "system_role": user.system_role,
                "is_active": user.is_active,
                "must_change_password": user.must_change_password,
                "school_id": str(user.school_id) if user.school_id else None,
                "staff_member_id": str(user.staff_member_id) if user.staff_member_id else None,
                "position_id": str(user.position_id) if user.position_id else None,
            }))
        except Exception:
            pass  # Cache write failure is non-fatal

    # SUPERADMIN has no school scope — RLS intentionally skipped
    if user.system_role == "SUPERADMIN":
        pass
    elif user.school_id:
        await set_rls_context(session, str(user.school_id))
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="School context required",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_superadmin(current_user: CurrentUser) -> User:
    if current_user.system_role != "SUPERADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Superadmin access required")
    return current_user


SuperAdmin = Annotated[User, Depends(get_current_superadmin)]


# ── Permission guard factory ──────────────────────────────────────

def require(permission: Permission):
    """
    Usage:  @router.get("/scores", dependencies=[Depends(require(Permission.VIEW_SCORES))])
    """
    async def _check(
        current_user: CurrentUser,
        redis: RedisDep,
        session: SessionDep,
    ) -> None:
        if current_user.system_role == "SUPERADMIN":
            return
        if current_user.system_role in ("STUDENT", "PARENT"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

        from app.services.permissions import check_permission
        allowed = await check_permission(current_user, permission, redis, session)
        if not allowed:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Permission required: {permission}",
            )

    return Depends(_check)
