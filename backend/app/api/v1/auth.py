from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.api.deps import CurrentUser, RedisDep, SessionDep
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.services.permissions import resolve_all_permissions

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"
_COOKIE_OPTS = {
    "httponly": True,
    "secure": True,
    "samesite": "lax",
    "max_age": 60 * 60 * 24 * 7,  # 7 days
    "path": "/api/v1/auth/refresh",
}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: str
    email: str
    system_role: str
    school_id: str | None
    permissions: dict[str, bool]


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, session: SessionDep) -> TokenResponse:
    user = await session.scalar(
        select(User).where(User.email == body.email, User.is_active.is_(True))
    )
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    if not user.is_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account not verified — check your email")

    access_token = create_access_token(
        str(user.id), str(user.school_id) if user.school_id else None, user.system_role
    )
    refresh_token = create_refresh_token(str(user.id))

    # Update last_login_at
    user.last_login_at = datetime.now(UTC)
    await session.commit()

    response.set_cookie(_REFRESH_COOKIE, refresh_token, **_COOKIE_OPTS)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, session: SessionDep) -> TokenResponse:
    token = request.cookies.get(_REFRESH_COOKIE)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token")

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")

    user = await session.get(User, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    access_token = create_access_token(
        str(user.id), str(user.school_id) if user.school_id else None, user.system_role
    )
    new_refresh = create_refresh_token(str(user.id))
    response.set_cookie(_REFRESH_COOKIE, new_refresh, **_COOKIE_OPTS)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie(_REFRESH_COOKIE, path="/api/v1/auth/refresh")
    return {"detail": "Logged out"}


@router.get("/me", response_model=MeResponse)
async def me(current_user: CurrentUser, redis: RedisDep, session: SessionDep) -> MeResponse:
    perms = await resolve_all_permissions(current_user, redis, session)
    return MeResponse(
        id=str(current_user.id),
        email=current_user.email,
        system_role=current_user.system_role,
        school_id=str(current_user.school_id) if current_user.school_id else None,
        permissions=perms,
    )
