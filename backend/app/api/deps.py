"""
FastAPI dependency injection — auth, DB session, Redis, permission guard.
"""
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

bearer = HTTPBearer(auto_error=True)


# ── Database ──────────────────────────────────────────────────────

SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]


# ── Auth ──────────────────────────────────────────────────────────

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    session: SessionDep,
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
        user_id: str = payload["sub"]
    except (JWTError, KeyError):
        raise credentials_exception

    user = await session.scalar(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    if not user:
        raise credentials_exception

    # Set RLS context so all subsequent queries are school-scoped
    if user.school_id:
        await set_rls_context(session, str(user.school_id))

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
