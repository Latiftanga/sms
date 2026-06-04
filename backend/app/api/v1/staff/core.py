import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlalchemy import exists, func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, RedisDep, SessionDep, require
from app.api.v1.staff._helpers import _get_member, _linked_user, _current_rank, _to_response
from app.core.config import settings
from app.core.permissions import Permission
from app.core.security import hash_password
from app.models.school import School
from app.models.staff import StaffMember, StaffPosition
from app.models.user import User, UserRole
from app.schemas.staff import (
    AccountCreateRequest,
    InviteResponse,
    PromotionResponse,
    QualificationResponse,
    RoleAssignRequest,
    StaffMemberCreate,
    StaffMemberDetail,
    StaffMemberResponse,
    StaffMemberUpdate,
)
from app.schemas.common import PagedResponse
from app.services.storage import ALLOWED_IMAGE_TYPES, get_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/staff", tags=["staff"])

ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}

_DESIGNATION_TO_ROLE_CODES: dict[str, list[str]] = {
    "HEADTEACHER":         ["HEADTEACHER"],
    "ASSISTANT_HEAD":      ["ASSISTANT_HEAD"],
    "BURSAR":              ["BURSAR"],
    "HOUSEMASTER":         ["HOUSEMASTER"],
    "SENIOR_HOUSEMASTER":  ["SENIOR_HOUSEMASTER"],
}


def _default_role_codes(member: StaffMember) -> list[str]:
    codes = _DESIGNATION_TO_ROLE_CODES.get(member.designation or "")
    if codes:
        return codes
    if member.category == "TEACHING":
        return ["CLASS_TEACHER"]
    return []


async def _assign_roles_by_codes(
    user: User, codes: list[str], assigned_by_id: UUID, session
) -> None:
    if not codes:
        return
    positions = list(await session.scalars(
        select(StaffPosition).where(
            StaffPosition.code.in_(codes),
            StaffPosition.is_system_template.is_(True),
        )
    ))
    now = datetime.now(UTC)
    for pos in positions:
        exists_already = await session.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == pos.id,
            )
        )
        if not exists_already:
            session.add(UserRole(
                user_id=user.id,
                role_id=pos.id,
                assigned_by=assigned_by_id,
                assigned_at=now,
            ))


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=PagedResponse[StaffMemberResponse],
            dependencies=[require(Permission.VIEW_STAFF)])
async def list_staff(
    user: CurrentUser,
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    category: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
):
    school_id = user.school_id

    conditions = [StaffMember.school_id == school_id]
    if category:
        conditions.append(StaffMember.category == category.upper())
    if is_active is not None:
        conditions.append(StaffMember.is_active == is_active)
    if search:
        term = f"%{search}%"
        conditions.append(
            StaffMember.first_name.ilike(term)
            | StaffMember.last_name.ilike(term)
            | StaffMember.staff_id.ilike(term)
            | StaffMember.ges_staff_id.ilike(term)
        )

    total = await session.scalar(
        select(func.count(StaffMember.id)).where(*conditions)
    )

    from app.models.staff import StaffPromotion
    rank_sq = (
        select(StaffPromotion.rank)
        .where(StaffPromotion.staff_member_id == StaffMember.id)
        .order_by(StaffPromotion.date_promoted.desc())
        .limit(1)
        .correlate(StaffMember)
        .scalar_subquery()
    )

    rows = list(await session.execute(
        select(StaffMember, rank_sq.label("current_rank"))
        .where(*conditions)
        .order_by(StaffMember.last_name, StaffMember.first_name)
        .offset(skip)
        .limit(limit)
    ))

    ids = [r[0].id for r in rows]
    linked_ids: set[UUID] = set()
    if ids:
        linked_ids = set(await session.scalars(
            select(User.staff_member_id).where(User.staff_member_id.in_(ids))
        ))

    items = [
        StaffMemberResponse.model_validate({
            **r[0].__dict__,
            "current_rank": r[1],
            "has_account": r[0].id in linked_ids,
        })
        for r in rows
    ]
    return PagedResponse(items=items, total=total or 0, skip=skip, limit=limit)


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_model=StaffMemberResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_STAFF)])
async def create_staff(
    body: StaffMemberCreate,
    user: CurrentUser,
    session: SessionDep,
):
    member = StaffMember(school_id=user.school_id, **body.model_dump())
    session.add(member)
    await session.commit()
    await session.refresh(member)
    return _to_response(member)


# ── Detail ────────────────────────────────────────────────────────────────────

@router.get("/{staff_id}", response_model=StaffMemberDetail,
            dependencies=[require(Permission.VIEW_STAFF)])
async def get_staff(staff_id: UUID, user: CurrentUser, session: SessionDep):
    has_acct_sq = exists().where(User.staff_member_id == staff_id)
    invite_pending_sq = exists().where(
        User.staff_member_id == staff_id,
        User.invite_token.isnot(None),
        User.is_active.is_(False),
    )

    result = await session.execute(
        select(StaffMember, has_acct_sq, invite_pending_sq)
        .where(
            StaffMember.id == staff_id,
            StaffMember.school_id == user.school_id,
        )
        .options(
            selectinload(StaffMember.qualifications),
            selectinload(StaffMember.promotions),
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff member not found")

    member, has_account, invite_pending = row
    return StaffMemberDetail.model_validate({
        **member.__dict__,
        "current_rank": _current_rank(member.promotions),
        "has_account": has_account,
        "invite_pending": invite_pending,
        "qualifications": [QualificationResponse.model_validate(q) for q in member.qualifications],
        "promotions": sorted(
            [PromotionResponse.model_validate(p) for p in member.promotions],
            key=lambda p: p.date_promoted,
            reverse=True,
        ),
    })


# ── Update ────────────────────────────────────────────────────────────────────

@router.patch("/{staff_id}", response_model=StaffMemberResponse,
              dependencies=[require(Permission.MANAGE_STAFF)])
async def update_staff(
    staff_id: UUID,
    body: StaffMemberUpdate,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    await session.commit()
    await session.refresh(member)
    return _to_response(member)


# ── Deactivate ────────────────────────────────────────────────────────────────

@router.delete("/{staff_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_STAFF)])
async def deactivate_staff(
    staff_id: UUID,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    member.is_active = False
    linked = await _linked_user(member, session)
    if linked:
        linked.is_active = False
    await session.commit()


# ── Photo upload ──────────────────────────────────────────────────────────────

@router.post("/{staff_id}/photo", response_model=StaffMemberResponse,
             dependencies=[require(Permission.MANAGE_STAFF)])
async def upload_photo(
    staff_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    file: UploadFile = File(...),
):
    if file.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "JPEG, PNG or WebP only")

    member = await _get_member(staff_id, user.school_id, session)
    storage = get_storage()

    if member.photo_url:
        await storage.delete(member.photo_url)

    member.photo_url = await storage.upload(file, folder="staff-photos")
    await session.commit()
    await session.refresh(member)
    return _to_response(member)


# ── Invite ────────────────────────────────────────────────────────────────────

async def _send_invite_sms(phone: str, invite_token: str, school_name: str) -> None:
    invite_url = f"{settings.FRONTEND_URL}/invite/{invite_token}"
    msg = f"You've been invited to {school_name}. Set up your account: {invite_url}"
    async with httpx.AsyncClient(timeout=8) as client:
        resp = await client.post(
            "https://api.africastalking.com/version1/messaging",
            headers={"apiKey": settings.AT_API_KEY or "", "Accept": "application/json"},
            data={"username": settings.AT_USERNAME, "to": phone, "message": msg, "from": settings.AT_SENDER_ID},
        )
        resp.raise_for_status()


@router.post("/{staff_id}/invite", response_model=InviteResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_USERS)])
async def send_invite(
    staff_id: UUID,
    body: AccountCreateRequest,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    existing = await _linked_user(member, session)

    if existing and existing.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "Staff member already has an active account")

    email_owner = await session.scalar(select(User).where(User.email == body.email))
    if email_owner and (existing is None or email_owner.id != existing.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already in use")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(days=7)

    if existing:
        existing.email = str(body.email)
        existing.invite_token = token
        existing.invite_expires_at = expires_at
        await session.flush()
        codes = _default_role_codes(member)
        await _assign_roles_by_codes(existing, codes, user.id, session)
    else:
        new_user = User(
            email=str(body.email),
            password_hash=hash_password(secrets.token_hex(32)),
            system_role="SCHOOL_STAFF",
            school_id=user.school_id,
            staff_member_id=member.id,
            is_active=False,
            is_verified=False,
            must_change_password=False,
            invite_token=token,
            invite_expires_at=expires_at,
        )
        session.add(new_user)
        await session.flush()
        codes = _default_role_codes(member)
        await _assign_roles_by_codes(new_user, codes, user.id, session)

    await session.commit()

    sms_sent = False
    if member.phone and settings.AT_API_KEY:
        school = await session.get(School, user.school_id)
        school_name = school.name if school else "Your School"
        try:
            await _send_invite_sms(member.phone, token, school_name)
            sms_sent = True
        except Exception as e:
            logger.warning("SMS invite failed for staff %s: %s", member.id, e)

    return InviteResponse(invite_token=token, email=str(body.email), sms_sent=sms_sent)


# ── Admin password reset ──────────────────────────────────────────────────────

@router.post("/{staff_id}/reset-password", response_model=InviteResponse,
             dependencies=[require(Permission.MANAGE_USERS)])
async def reset_password(
    staff_id: UUID,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    linked = await _linked_user(member, session)
    if not linked:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No account found for this staff member")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(days=7)
    linked.is_active = False
    linked.is_verified = False
    linked.invite_token = token
    linked.invite_expires_at = expires_at
    await session.commit()

    sms_sent = False
    if member.phone and settings.AT_API_KEY:
        school = await session.get(School, user.school_id)
        school_name = school.name if school else "Your School"
        try:
            await _send_invite_sms(member.phone, token, school_name)
            sms_sent = True
        except Exception as e:
            logger.warning("SMS invite failed for staff %s: %s", member.id, e)

    return InviteResponse(invite_token=token, email=linked.email, sms_sent=sms_sent)


# ── Reactivate ────────────────────────────────────────────────────────────────

@router.post("/{staff_id}/reactivate", status_code=204,
             dependencies=[require(Permission.MANAGE_STAFF)])
async def reactivate_staff(
    staff_id: UUID,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    member.is_active = True
    linked = await _linked_user(member, session)
    if linked:
        linked.is_active = True
    await session.commit()
