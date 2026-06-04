from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep, require
from app.api.v1.settings._helpers import _school_id, _current_year
from app.core.permissions import Permission
from app.models.academic import AcademicYear, AcademicTerm
from app.models.school import School
from app.schemas.settings import CurrentTermResponse, SchoolProfileUpdate
from app.schemas.school import SchoolResponse
from app.services.storage import ALLOWED_IMAGE_TYPES, get_storage

router = APIRouter()


@router.get("/school", response_model=SchoolResponse)
async def get_school(user: CurrentUser, session: SessionDep) -> SchoolResponse:
    school = await session.get(School, _school_id(user))
    if not school:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    return SchoolResponse.model_validate(school)


@router.get("/current-term", response_model=CurrentTermResponse | None)
async def get_current_term(user: CurrentUser, session: SessionDep):
    school_id = _school_id(user)
    year = await session.scalar(
        select(AcademicYear)
        .where(AcademicYear.school_id == school_id, AcademicYear.is_current.is_(True))
        .options(selectinload(AcademicYear.terms))
    )
    if not year:
        return None
    current = next((t for t in year.terms if t.is_current), None)
    if not current:
        return None
    return CurrentTermResponse(
        term_name=current.name,
        year_name=year.name,
        start_date=current.start_date,
        end_date=current.end_date,
    )


@router.patch("/school", response_model=SchoolResponse,
              dependencies=[require(Permission.MANAGE_SCHOOL_CONFIG)])
async def update_school(
    body: SchoolProfileUpdate, user: CurrentUser, session: SessionDep
) -> SchoolResponse:
    school = await session.get(School, _school_id(user))
    if not school:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(school, field, value)
    await session.commit()
    await session.refresh(school)
    return SchoolResponse.model_validate(school)


@router.post("/school/logo", response_model=SchoolResponse,
             dependencies=[require(Permission.MANAGE_SCHOOL_CONFIG)])
async def upload_school_logo(
    user: CurrentUser,
    session: SessionDep,
    file: UploadFile = File(...),
) -> SchoolResponse:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Unsupported file type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )
    school = await session.get(School, _school_id(user))
    if not school:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")

    storage = get_storage()
    if school.logo_url:
        await storage.delete(school.logo_url)

    try:
        url = await storage.upload(file, folder="logos")
    except ValueError as exc:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, str(exc)) from exc

    school.logo_url = url
    await session.commit()
    await session.refresh(school)
    return SchoolResponse.model_validate(school)
