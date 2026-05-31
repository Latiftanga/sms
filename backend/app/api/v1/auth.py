import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, RedisDep, SessionDep
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.services.permissions import resolve_all_permissions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"
_COOKIE_OPTS = {
    "httponly": True,
    "secure": settings.is_production,   # False in dev (HTTP); True in prod (HTTPS)
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
    full_name: str | None
    system_role: str
    school_id: str | None
    permissions: dict[str, bool]
    must_change_password: bool


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


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
    full_name: str | None = None
    if current_user.staff_member_id:
        user_with_staff = await session.scalar(
            select(User)
            .where(User.id == current_user.id)
            .options(selectinload(User.staff_member))
        )
        if user_with_staff and user_with_staff.staff_member:
            sm = user_with_staff.staff_member
            full_name = f"{sm.first_name} {sm.last_name}".strip()
    return MeResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=full_name,
        system_role=current_user.system_role,
        school_id=str(current_user.school_id) if current_user.school_id else None,
        permissions=perms,
        must_change_password=current_user.must_change_password,
    )


@router.post("/change-password", status_code=204)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> None:
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    if len(body.new_password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters")
    current_user.password_hash = hash_password(body.new_password)
    current_user.must_change_password = False
    await session.commit()


# ── Invite flow ───────────────────────────────────────────────────────────────

class InviteInfoResponse(BaseModel):
    staff_name: str
    email: str


class AcceptInviteRequest(BaseModel):
    password: str


@router.get("/invite/{token}", response_model=InviteInfoResponse)
async def get_invite_info(token: str, session: SessionDep) -> InviteInfoResponse:
    user = await session.scalar(
        select(User)
        .where(User.invite_token == token)
        .options(selectinload(User.staff_member))
    )
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invalid or expired invite link")
    if not user.invite_expires_at or datetime.now(UTC) > user.invite_expires_at:
        raise HTTPException(status.HTTP_410_GONE, "Invite link has expired — ask your admin to resend it")

    name = (
        f"{user.staff_member.first_name} {user.staff_member.last_name}"
        if user.staff_member else ""
    )
    return InviteInfoResponse(staff_name=name, email=user.email)


@router.post("/invite/{token}", status_code=204)
async def accept_invite(token: str, body: AcceptInviteRequest, session: SessionDep) -> None:
    user = await session.scalar(select(User).where(User.invite_token == token))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invalid invite link")
    if not user.invite_expires_at or datetime.now(UTC) > user.invite_expires_at:
        raise HTTPException(status.HTTP_410_GONE, "This invite has expired — ask your admin to resend it")
    if len(body.password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters")

    user.password_hash = hash_password(body.password)
    user.is_active = True
    user.is_verified = True
    user.invite_token = None
    user.invite_expires_at = None
    user.must_change_password = False
    await session.commit()


# ── Self-service password reset ───────────────────────────────────────────────

_RESET_TTL_MINUTES = 30


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    password: str


class ResetTokenInfoResponse(BaseModel):
    email: str


async def _send_reset_sms(phone: str, token: str) -> None:
    reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"
    msg = f"TTEK SIS: Reset your password here: {reset_url} (expires in 30 minutes)"
    async with httpx.AsyncClient(timeout=8) as client:
        resp = await client.post(
            "https://api.africastalking.com/version1/messaging",
            headers={"apiKey": settings.AT_API_KEY or "", "Accept": "application/json"},
            data={
                "username": settings.AT_USERNAME,
                "to": phone,
                "message": msg,
                "from": settings.AT_SENDER_ID,
            },
        )
        resp.raise_for_status()


@router.post("/forgot-password", status_code=200)
async def forgot_password(body: ForgotPasswordRequest, session: SessionDep) -> dict:
    """
    Always returns 200 to prevent user enumeration.
    Sends an SMS reset link if the email is found and has a linked phone number.
    """
    user = await session.scalar(
        select(User)
        .where(User.email == body.email, User.is_active.is_(True))
        .options(selectinload(User.staff_member))
    )
    if user:
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires_at = datetime.now(UTC) + timedelta(minutes=_RESET_TTL_MINUTES)
        await session.commit()

        phone = user.staff_member.phone if user.staff_member else None
        if phone and settings.AT_API_KEY:
            try:
                await _send_reset_sms(phone, token)
            except Exception as e:
                logger.warning("Password reset SMS failed for user %s: %s", user.id, e)

    return {"detail": "If an account exists for that email, a reset link has been sent."}


@router.get("/reset-password/{token}", response_model=ResetTokenInfoResponse)
async def get_reset_info(token: str, session: SessionDep) -> ResetTokenInfoResponse:
    user = await session.scalar(
        select(User).where(User.password_reset_token == token)
    )
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invalid or expired reset link")
    if not user.password_reset_expires_at or datetime.now(UTC) > user.password_reset_expires_at:
        raise HTTPException(status.HTTP_410_GONE, "This reset link has expired — request a new one")
    return ResetTokenInfoResponse(email=user.email)


@router.post("/reset-password/{token}", status_code=204)
async def reset_password(token: str, body: ResetPasswordRequest, session: SessionDep) -> None:
    user = await session.scalar(
        select(User).where(User.password_reset_token == token)
    )
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invalid or expired reset link")
    if not user.password_reset_expires_at or datetime.now(UTC) > user.password_reset_expires_at:
        raise HTTPException(status.HTTP_410_GONE, "This reset link has expired — request a new one")
    if len(body.password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters")

    user.password_hash = hash_password(body.password)
    user.must_change_password = False
    user.password_reset_token = None
    user.password_reset_expires_at = None
    await session.commit()
