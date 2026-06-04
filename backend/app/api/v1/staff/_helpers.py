from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.staff import StaffMember, StaffPromotion
from app.models.user import User
from app.schemas.staff import StaffMemberResponse


async def _get_member(staff_id: UUID, school_id: UUID, session: AsyncSession) -> StaffMember:
    member = await session.scalar(
        select(StaffMember).where(
            StaffMember.id == staff_id,
            StaffMember.school_id == school_id,
        )
    )
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff member not found")
    return member


async def _linked_user(member: StaffMember, session: AsyncSession) -> User | None:
    return await session.scalar(
        select(User).where(User.staff_member_id == member.id)
    )


def _current_rank(promotions: list[StaffPromotion]) -> str | None:
    if not promotions:
        return None
    return max(promotions, key=lambda p: p.date_promoted).rank


def _to_response(member: StaffMember, has_account: bool = False) -> StaffMemberResponse:
    loaded_promotions = member.__dict__.get("promotions")
    return StaffMemberResponse.model_validate({
        **member.__dict__,
        "current_rank": _current_rank(loaded_promotions) if loaded_promotions else None,
        "has_account": has_account,
    })
