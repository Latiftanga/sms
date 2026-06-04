from datetime import date
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep, require
from app.api.v1.staff._helpers import _get_member
from app.core.permissions import Permission
from app.models.staff import StaffPromotion, StaffQualification
from app.schemas.staff import (
    PromotionCreate, PromotionResponse, PromotionUpdate,
    QualificationCreate, QualificationResponse, QualificationUpdate,
)
from app.services.storage import ALLOWED_DOCUMENT_TYPES, MAX_DOCUMENT_BYTES, get_storage

router = APIRouter()


# ── Qualifications ────────────────────────────────────────────────────────────

@router.post("/{staff_id}/qualifications", response_model=QualificationResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_STAFF)])
async def add_qualification(
    staff_id: UUID,
    body: QualificationCreate,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    q = StaffQualification(staff_member_id=member.id, **body.model_dump())
    session.add(q)
    await session.commit()
    await session.refresh(q)
    return QualificationResponse.model_validate(q)


@router.patch("/{staff_id}/qualifications/{qual_id}", response_model=QualificationResponse,
              dependencies=[require(Permission.MANAGE_STAFF)])
async def update_qualification(
    staff_id: UUID,
    qual_id: UUID,
    body: QualificationUpdate,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    qual = await session.scalar(
        select(StaffQualification).where(
            StaffQualification.id == qual_id,
            StaffQualification.staff_member_id == member.id,
        )
    )
    if not qual:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Qualification not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(qual, field, value)
    await session.commit()
    await session.refresh(qual)
    return QualificationResponse.model_validate(qual)


@router.delete("/{staff_id}/qualifications/{qual_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_STAFF)])
async def remove_qualification(
    staff_id: UUID,
    qual_id: UUID,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    qual = await session.scalar(
        select(StaffQualification).where(
            StaffQualification.id == qual_id,
            StaffQualification.staff_member_id == member.id,
        )
    )
    if not qual:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Qualification not found")
    await session.delete(qual)
    await session.commit()


# ── Promotions ────────────────────────────────────────────────────────────────

@router.get("/{staff_id}/promotions", response_model=list[PromotionResponse],
            dependencies=[require(Permission.VIEW_STAFF)])
async def list_promotions(
    staff_id: UUID,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    rows = list(await session.scalars(
        select(StaffPromotion)
        .where(StaffPromotion.staff_member_id == member.id)
        .order_by(StaffPromotion.date_promoted.desc())
    ))
    return [PromotionResponse.model_validate(r) for r in rows]


@router.post("/{staff_id}/promotions", response_model=PromotionResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_PROMOTIONS)])
async def record_promotion(
    staff_id: UUID,
    body: PromotionCreate,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
    row = StaffPromotion(
        staff_member_id=member.id,
        rank=body.rank,
        date_promoted=body.date_promoted,
        date_recorded=date.today(),
        recorded_by=user.id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return PromotionResponse.model_validate(row)


@router.patch("/{staff_id}/promotions/{prom_id}", response_model=PromotionResponse,
              dependencies=[require(Permission.MANAGE_PROMOTIONS)])
async def update_promotion(
    staff_id: UUID,
    prom_id: UUID,
    body: PromotionUpdate,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
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


@router.delete("/{staff_id}/promotions/{prom_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_PROMOTIONS)])
async def remove_promotion(
    staff_id: UUID,
    prom_id: UUID,
    user: CurrentUser,
    session: SessionDep,
):
    member = await _get_member(staff_id, user.school_id, session)
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


@router.post("/{staff_id}/promotions/{prom_id}/document", response_model=PromotionResponse,
             dependencies=[require(Permission.MANAGE_PROMOTIONS)])
async def upload_promotion_document(
    staff_id: UUID,
    prom_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    file: UploadFile = File(...),
):
    if file.content_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "JPEG, PNG, WebP or PDF only")
    member = await _get_member(staff_id, user.school_id, session)
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
