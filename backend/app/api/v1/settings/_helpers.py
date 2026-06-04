from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.models.academic import AcademicYear
from app.models.school import School


def _school_id(user: CurrentUser) -> UUID:
    if not user.school_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No school associated with this account")
    return user.school_id


async def _current_year(school_id: UUID, session: AsyncSession) -> AcademicYear | None:
    return await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id, AcademicYear.is_current.is_(True)
        )
    )


def _require_shs(school: School) -> None:
    if "SHS" not in (school.education_levels or []):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Learning areas are only available for schools with SHS education level",
        )


def _require_houses(school: School) -> None:
    if not school.has_houses:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Houses are not enabled for this school",
        )
