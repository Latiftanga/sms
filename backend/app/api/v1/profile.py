"""
Self-service profile management for authenticated staff.
All routes require a linked StaffMember (403 otherwise).
"""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep
from app.api.v1.staff._helpers import _current_rank, _to_response
from app.models.staff import StaffMember, StaffPromotion, StaffQualification
from app.models.user import User
from app.schemas.staff import (
    PromotionCreate, PromotionResponse, PromotionUpdate,
    QualificationCreate, QualificationResponse, QualificationUpdate,
    StaffMemberDetail, StaffMemberResponse, StaffSelfUpdate,
)
from app.services.storage import ALLOWED_DOCUMENT_TYPES, ALLOWED_IMAGE_TYPES, MAX_DOCUMENT_BYTES, get_storage

router = APIRouter(prefix="/auth", tags=["profile"])

_STAFF_REQUIRED = HTTPException(status.HTTP_404_NOT_FOUND, "No staff profile linked to this account")
_ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def _my_member(user: User, session) -> StaffMember:
    if not user.staff_member_id:
        raise _STAFF_REQUIRED
    member = await session.get(StaffMember, user.staff_member_id)
    if not member:
        raise _STAFF_REQUIRED
    return member


# ── Staff profile ─────────────────────────────────────────────────────────────

@router.get("/me/staff", response_model=StaffMemberDetail)
async def me_staff(current_user: CurrentUser, session: SessionDep) -> StaffMemberDetail:
    member = await session.scalar(
        select(StaffMember)
        .where(StaffMember.id == current_user.staff_member_id)
        .options(
            selectinload(StaffMember.qualifications),
            selectinload(StaffMember.promotions),
        )
    )
    if not member:
        raise _STAFF_REQUIRED
    return StaffMemberDetail.model_validate({
        **member.__dict__,
        "current_rank": _current_rank(member.promotions),
        "has_account": True,
        "invite_pending": False,
        "qualifications": [QualificationResponse.model_validate(q) for q in member.qualifications],
        "promotions": sorted(
            [PromotionResponse.model_validate(p) for p in member.promotions],
            key=lambda p: p.date_promoted, reverse=True,
        ),
    })


@router.patch("/me/staff", response_model=StaffMemberResponse)
async def update_me_staff(
    body: StaffSelfUpdate,
    current_user: CurrentUser,
    session: SessionDep,
) -> StaffMemberResponse:
    member = await _my_member(current_user, session)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    await session.commit()
    await session.refresh(member)
    return _to_response(member, has_account=True)


@router.post("/me/photo", response_model=StaffMemberResponse)
async def upload_my_photo(
    current_user: CurrentUser,
    session: SessionDep,
    file: UploadFile = File(...),
) -> StaffMemberResponse:
    if file.content_type not in _ALLOWED_PHOTO_TYPES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unsupported image type — use JPEG, PNG or WebP")
    member = await _my_member(current_user, session)
    storage = get_storage()
    if member.photo_url:
        await storage.delete(member.photo_url)
    member.photo_url = await storage.upload(file, folder="staff-photos")
    await session.commit()
    await session.refresh(member)
    return _to_response(member, has_account=True)


# ── Qualifications ────────────────────────────────────────────────────────────

@router.post("/me/qualifications", response_model=QualificationResponse, status_code=201)
async def add_my_qualification(
    body: QualificationCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> QualificationResponse:
    member = await _my_member(current_user, session)
    q = StaffQualification(staff_member_id=member.id, **body.model_dump())
    session.add(q)
    await session.commit()
    await session.refresh(q)
    return QualificationResponse.model_validate(q)


@router.patch("/me/qualifications/{qual_id}", response_model=QualificationResponse)
async def update_my_qualification(
    qual_id: UUID,
    body: QualificationUpdate,
    current_user: CurrentUser,
    session: SessionDep,
) -> QualificationResponse:
    member = await _my_member(current_user, session)
    q = await session.scalar(
        select(StaffQualification).where(
            StaffQualification.id == qual_id,
            StaffQualification.staff_member_id == member.id,
        )
    )
    if not q:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Qualification not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(q, field, value)
    await session.commit()
    await session.refresh(q)
    return QualificationResponse.model_validate(q)


@router.delete("/me/qualifications/{qual_id}", status_code=204)
async def delete_my_qualification(
    qual_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> None:
    member = await _my_member(current_user, session)
    q = await session.scalar(
        select(StaffQualification).where(
            StaffQualification.id == qual_id,
            StaffQualification.staff_member_id == member.id,
        )
    )
    if not q:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Qualification not found")
    await session.delete(q)
    await session.commit()


# ── Promotions ────────────────────────────────────────────────────────────────

@router.post("/me/promotions", response_model=PromotionResponse, status_code=201)
async def add_my_promotion(
    body: PromotionCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> PromotionResponse:
    member = await _my_member(current_user, session)
    row = StaffPromotion(
        staff_member_id=member.id,
        rank=body.rank,
        date_promoted=body.date_promoted,
        date_recorded=date.today(),
        recorded_by=current_user.id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return PromotionResponse.model_validate(row)


@router.patch("/me/promotions/{prom_id}", response_model=PromotionResponse)
async def update_my_promotion(
    prom_id: UUID,
    body: PromotionUpdate,
    current_user: CurrentUser,
    session: SessionDep,
) -> PromotionResponse:
    member = await _my_member(current_user, session)
    row = await session.scalar(
        select(StaffPromotion).where(
            StaffPromotion.id == prom_id,
            StaffPromotion.staff_member_id == member.id,
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Promotion record not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.commit()
    await session.refresh(row)
    return PromotionResponse.model_validate(row)


@router.delete("/me/promotions/{prom_id}", status_code=204)
async def delete_my_promotion(
    prom_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> None:
    member = await _my_member(current_user, session)
    row = await session.scalar(
        select(StaffPromotion).where(
            StaffPromotion.id == prom_id,
            StaffPromotion.staff_member_id == member.id,
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Promotion record not found")
    await session.delete(row)
    await session.commit()


@router.post("/me/promotions/{prom_id}/document", response_model=PromotionResponse)
async def upload_my_promotion_document(
    prom_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
    file: UploadFile = File(...),
) -> PromotionResponse:
    if file.content_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "JPEG, PNG, WebP or PDF only")
    member = await _my_member(current_user, session)
    row = await session.scalar(
        select(StaffPromotion).where(
            StaffPromotion.id == prom_id,
            StaffPromotion.staff_member_id == member.id,
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Promotion record not found")
    storage = get_storage()
    if row.document_url:
        await storage.delete(row.document_url)
    row.document_url = await storage.upload(file, folder="promotion-docs", max_bytes=MAX_DOCUMENT_BYTES)
    await session.commit()
    await session.refresh(row)
    return PromotionResponse.model_validate(row)
