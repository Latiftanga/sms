"""Public endpoints — no auth required. Used for login page branding."""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import SessionDep
from app.core.config import settings
from app.models.school import School

router = APIRouter(prefix="/public", tags=["public"])

_PLATFORM_BRANDING = {
    "name": settings.APP_NAME,
    "motto": None,
    "logo_url": None,
    "accent_color": "#185FA5",
}


class SchoolBrandingResponse(BaseModel):
    name: str
    motto: str | None
    logo_url: str | None
    accent_color: str


@router.get("/school", response_model=SchoolBrandingResponse)
async def public_school_info(request: Request, session: SessionDep) -> SchoolBrandingResponse:
    """
    Return branding for the login page.

    Resolves school from subdomain or custom domain when present so each
    school's login page shows their own logo and colours.  Falls back to
    generic platform branding when no match is found (development, shared
    domain, or direct IP access).
    """
    host = request.headers.get("host", "").split(":")[0]  # strip port

    school = None

    # 1. Try custom domain first (most specific)
    if host:
        school = await session.scalar(
            select(School).where(School.custom_domain == host, School.is_active.is_(True))
        )

    # 2. Try subdomain (e.g. "demo-basic" from "demo-basic.yourdomain.com")
    if not school and host and "." in host:
        subdomain = host.split(".")[0]
        school = await session.scalar(
            select(School).where(School.subdomain == subdomain, School.is_active.is_(True))
        )

    if not school:
        return SchoolBrandingResponse(**_PLATFORM_BRANDING)

    return SchoolBrandingResponse(
        name=school.name,
        motto=school.motto,
        logo_url=school.logo_url,
        accent_color=school.accent_color,
    )
