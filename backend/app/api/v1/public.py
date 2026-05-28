"""Public endpoints — no auth required. Used for login page branding."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import SessionDep
from app.models.school import School

router = APIRouter(prefix="/public", tags=["public"])


class SchoolBrandingResponse(BaseModel):
    name: str
    motto: str | None
    logo_url: str | None
    accent_color: str


@router.get("/school", response_model=SchoolBrandingResponse)
async def public_school_info(session: SessionDep) -> SchoolBrandingResponse:
    """Return public branding for the active school — safe to call without auth."""
    school = await session.scalar(
        select(School).where(School.is_active == True).limit(1)
    )
    if not school:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active school found")
    return SchoolBrandingResponse(
        name=school.name,
        motto=school.motto,
        logo_url=school.logo_url,
        accent_color=school.accent_color,
    )
