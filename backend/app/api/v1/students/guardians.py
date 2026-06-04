import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep, require
from app.core.permissions import Permission
from app.models.student import Guardian
from app.schemas.student import GuardianCreate, GuardianResponse, GuardianUpdate

from ._helpers import _get_student

router = APIRouter()


@router.post("/{student_id}/guardians", response_model=GuardianResponse, status_code=201,
             dependencies=[require(Permission.ENROLL_STUDENTS)])
async def add_guardian(
    student_id: uuid.UUID,
    body: GuardianCreate,
    user: CurrentUser,
    session: SessionDep,
):
    await _get_student(student_id, user.school_id, session)

    guardian = Guardian(
        id=uuid.uuid4(),
        student_id=student_id,
        first_name=body.first_name,
        last_name=body.last_name,
        relationship_type=body.relationship_type,
        phone=body.phone,
        email=body.email,
        is_primary_contact=body.is_primary_contact,
    )
    session.add(guardian)
    await session.commit()
    await session.refresh(guardian)

    return GuardianResponse(
        id=guardian.id,
        first_name=guardian.first_name,
        last_name=guardian.last_name,
        relationship_type=guardian.relationship_type,
        phone=guardian.phone,
        email=guardian.email,
        is_primary_contact=guardian.is_primary_contact,
    )


@router.patch("/{student_id}/guardians/{guardian_id}",
              response_model=GuardianResponse,
              dependencies=[require(Permission.ENROLL_STUDENTS)])
async def update_guardian(
    student_id: uuid.UUID,
    guardian_id: uuid.UUID,
    body: GuardianUpdate,
    user: CurrentUser,
    session: SessionDep,
):
    await _get_student(student_id, user.school_id, session)

    guardian = await session.scalar(
        select(Guardian).where(
            Guardian.id == guardian_id,
            Guardian.student_id == student_id,
        )
    )
    if not guardian:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Guardian not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(guardian, field, value)

    await session.commit()
    await session.refresh(guardian)

    return GuardianResponse(
        id=guardian.id,
        first_name=guardian.first_name,
        last_name=guardian.last_name,
        relationship_type=guardian.relationship_type,
        phone=guardian.phone,
        email=guardian.email,
        is_primary_contact=guardian.is_primary_contact,
    )


@router.delete("/{student_id}/guardians/{guardian_id}", status_code=204,
               dependencies=[require(Permission.ENROLL_STUDENTS)])
async def delete_guardian(
    student_id: uuid.UUID,
    guardian_id: uuid.UUID,
    user: CurrentUser,
    session: SessionDep,
):
    await _get_student(student_id, user.school_id, session)

    guardian = await session.scalar(
        select(Guardian).where(
            Guardian.id == guardian_id,
            Guardian.student_id == student_id,
        )
    )
    if not guardian:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Guardian not found")

    await session.delete(guardian)
    await session.commit()
