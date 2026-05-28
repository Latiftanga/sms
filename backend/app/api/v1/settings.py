from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep
from app.models.academic import AcademicTerm, AcademicYear, Class, LearningArea
from app.models.school import School
from app.models.staff import PositionPermission, StaffPosition
from app.schemas.common import PagedResponse
from app.schemas.settings import (
    AcademicTermCreate, AcademicTermResponse, AcademicTermUpdate,
    AcademicYearCreate, AcademicYearResponse, AcademicYearUpdate,
    ClassCreate, ClassResponse, ClassUpdate,
    LearningAreaCreate, LearningAreaResponse, LearningAreaUpdate,
    SchoolProfileUpdate, EDUCATION_LEVEL_MAP,
)
from app.schemas.school import SchoolResponse
from app.schemas.staff import PositionCreate, PositionUpdate, PositionResponse
from app.services.storage import ALLOWED_IMAGE_TYPES, get_storage

router = APIRouter(prefix="/settings", tags=["settings"])


def _school_id(user: CurrentUser) -> UUID:
    if not user.school_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No school associated with this account")
    return user.school_id


def _require_shs(school: School) -> None:
    if "SHS" not in (school.education_levels or []):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Learning areas are only available for schools with SHS education level",
        )


# ── School profile ────────────────────────────────────────────────────────────

@router.get("/school", response_model=SchoolResponse)
async def get_school(user: CurrentUser, session: SessionDep) -> SchoolResponse:
    school = await session.get(School, _school_id(user))
    if not school:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not found")
    return SchoolResponse.model_validate(school)


@router.patch("/school", response_model=SchoolResponse)
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


@router.post("/school/logo", response_model=SchoolResponse)
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

    # Delete old logo if it exists (best-effort)
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


# ── Academic Years ────────────────────────────────────────────────────────────

@router.get("/academic-years", response_model=PagedResponse[AcademicYearResponse])
async def list_academic_years(
    user: CurrentUser,
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    school_id = _school_id(user)
    total = await session.scalar(
        select(func.count(AcademicYear.id)).where(AcademicYear.school_id == school_id)
    )
    rows = await session.scalars(
        select(AcademicYear)
        .where(AcademicYear.school_id == school_id)
        .options(selectinload(AcademicYear.terms))
        .order_by(AcademicYear.start_date.desc())
        .offset(skip)
        .limit(limit)
    )
    return PagedResponse(
        items=[AcademicYearResponse.model_validate(r) for r in rows],
        total=total or 0,
        skip=skip,
        limit=limit,
    )


@router.post("/academic-years", response_model=AcademicYearResponse, status_code=201)
async def create_academic_year(
    body: AcademicYearCreate, user: CurrentUser, session: SessionDep
):
    school_id = _school_id(user)
    duplicate = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.name == body.name,
        )
    )
    if duplicate:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Academic year '{body.name}' already exists")
    year = AcademicYear(school_id=school_id, **body.model_dump())
    session.add(year)
    await session.commit()
    await session.refresh(year, ["terms"])
    return AcademicYearResponse.model_validate(year)


@router.patch("/academic-years/{year_id}", response_model=AcademicYearResponse)
async def update_academic_year(
    year_id: UUID, body: AcademicYearUpdate, user: CurrentUser, session: SessionDep
):
    year = await session.scalar(
        select(AcademicYear)
        .where(AcademicYear.id == year_id, AcademicYear.school_id == _school_id(user))
        .options(selectinload(AcademicYear.terms))
    )
    if not year:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Academic year not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(year, field, value)
    await session.commit()
    await session.refresh(year, ["terms"])
    return AcademicYearResponse.model_validate(year)


@router.post("/academic-years/{year_id}/activate", response_model=AcademicYearResponse)
async def activate_academic_year(year_id: UUID, user: CurrentUser, session: SessionDep):
    school_id = _school_id(user)
    # Clear current flag on all years for this school
    all_years = await session.scalars(
        select(AcademicYear).where(AcademicYear.school_id == school_id)
    )
    for y in all_years:
        y.is_current = y.id == year_id
    await session.commit()
    year = await session.scalar(
        select(AcademicYear)
        .where(AcademicYear.id == year_id)
        .options(selectinload(AcademicYear.terms))
    )
    return AcademicYearResponse.model_validate(year)


@router.delete("/academic-years/{year_id}", status_code=204)
async def delete_academic_year(year_id: UUID, user: CurrentUser, session: SessionDep):
    year = await session.scalar(
        select(AcademicYear)
        .where(AcademicYear.id == year_id, AcademicYear.school_id == _school_id(user))
    )
    if not year:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Academic year not found")
    if year.is_current:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot delete the current academic year")
    await session.delete(year)
    await session.commit()


# ── Terms ─────────────────────────────────────────────────────────────────────

@router.post("/academic-years/{year_id}/terms", response_model=AcademicTermResponse, status_code=201)
async def create_term(
    year_id: UUID, body: AcademicTermCreate, user: CurrentUser, session: SessionDep
):
    year = await session.scalar(
        select(AcademicYear)
        .where(AcademicYear.id == year_id, AcademicYear.school_id == _school_id(user))
    )
    if not year:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Academic year not found")
    existing = await session.scalar(
        select(AcademicTerm).where(
            AcademicTerm.academic_year_id == year_id,
            AcademicTerm.name == body.name,
        )
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Term '{body.name}' already exists in this year")
    term = AcademicTerm(academic_year_id=year_id, **body.model_dump())
    session.add(term)
    await session.commit()
    await session.refresh(term)
    return AcademicTermResponse.model_validate(term)


@router.patch("/terms/{term_id}", response_model=AcademicTermResponse)
async def update_term(term_id: UUID, body: AcademicTermUpdate, user: CurrentUser, session: SessionDep):
    term = await session.get(AcademicTerm, term_id)
    if not term:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Term not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(term, field, value)
    await session.commit()
    await session.refresh(term)
    return AcademicTermResponse.model_validate(term)


@router.post("/terms/{term_id}/activate", response_model=AcademicTermResponse)
async def activate_term(term_id: UUID, user: CurrentUser, session: SessionDep):
    term = await session.get(AcademicTerm, term_id)
    if not term:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Term not found")
    # Clear current on sibling terms in the same year
    siblings = await session.scalars(
        select(AcademicTerm).where(AcademicTerm.academic_year_id == term.academic_year_id)
    )
    for t in siblings:
        t.is_current = t.id == term_id
    await session.commit()
    await session.refresh(term)
    return AcademicTermResponse.model_validate(term)


@router.delete("/terms/{term_id}", status_code=204)
async def delete_term(term_id: UUID, user: CurrentUser, session: SessionDep):
    term = await session.get(AcademicTerm, term_id)
    if not term:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Term not found")
    if term.is_current:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot delete the current term")
    await session.delete(term)
    await session.commit()


# ── Learning Areas (SHS only) ─────────────────────────────────────────────────

@router.get("/learning-areas", response_model=PagedResponse[LearningAreaResponse])
async def list_learning_areas(
    user: CurrentUser,
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    school_id = _school_id(user)
    total = await session.scalar(
        select(func.count(LearningArea.id)).where(LearningArea.school_id == school_id)
    )
    rows = await session.scalars(
        select(LearningArea)
        .where(LearningArea.school_id == school_id)
        .order_by(LearningArea.name)
        .offset(skip)
        .limit(limit)
    )
    return PagedResponse(
        items=[LearningAreaResponse.model_validate(r) for r in rows],
        total=total or 0,
        skip=skip,
        limit=limit,
    )


@router.post("/learning-areas", response_model=LearningAreaResponse, status_code=201)
async def create_learning_area(
    body: LearningAreaCreate, user: CurrentUser, session: SessionDep
):
    school = await session.get(School, _school_id(user))
    _require_shs(school)
    la = LearningArea(school_id=_school_id(user), **body.model_dump())
    session.add(la)
    await session.commit()
    await session.refresh(la)
    return LearningAreaResponse.model_validate(la)


@router.patch("/learning-areas/{la_id}", response_model=LearningAreaResponse)
async def update_learning_area(
    la_id: UUID, body: LearningAreaUpdate, user: CurrentUser, session: SessionDep
):
    la = await session.scalar(
        select(LearningArea)
        .where(LearningArea.id == la_id, LearningArea.school_id == _school_id(user))
    )
    if not la:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning area not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(la, field, value)
    await session.commit()
    await session.refresh(la)
    return LearningAreaResponse.model_validate(la)


@router.delete("/learning-areas/{la_id}", status_code=204)
async def delete_learning_area(la_id: UUID, user: CurrentUser, session: SessionDep):
    la = await session.scalar(
        select(LearningArea)
        .where(LearningArea.id == la_id, LearningArea.school_id == _school_id(user))
    )
    if not la:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning area not found")
    await session.delete(la)
    await session.commit()


# ── Classes ───────────────────────────────────────────────────────────────────

@router.get("/classes", response_model=PagedResponse[ClassResponse])
async def list_classes(
    user: CurrentUser,
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
):
    school_id = _school_id(user)
    total = await session.scalar(
        select(func.count(Class.id)).where(Class.school_id == school_id)
    )
    rows = await session.scalars(
        select(Class)
        .where(Class.school_id == school_id)
        .options(selectinload(Class.learning_area))
        .order_by(Class.education_level, Class.level, Class.year, Class.stream)
        .offset(skip)
        .limit(limit)
    )
    return PagedResponse(
        items=[
            ClassResponse(
                **{k: getattr(r, k) for k in ClassResponse.model_fields if k != "name"},
                name=r.name,
            )
            for r in rows
        ],
        total=total or 0,
        skip=skip,
        limit=limit,
    )


@router.post("/classes", response_model=ClassResponse, status_code=201)
async def create_class(body: ClassCreate, user: CurrentUser, session: SessionDep):
    school_id = _school_id(user)

    # Validate learning_area belongs to this school
    if body.learning_area_id:
        la = await session.scalar(
            select(LearningArea)
            .where(LearningArea.id == body.learning_area_id, LearningArea.school_id == school_id)
        )
        if not la:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning area not found")

    # NULL-safe duplicate check (PostgreSQL UNIQUE ignores NULLs, so we do this in app layer)
    dup_q = select(Class).where(
        Class.school_id == school_id,
        Class.level == body.level,
        Class.year == body.year if body.year is not None else Class.year.is_(None),
        Class.learning_area_id == body.learning_area_id if body.learning_area_id is not None else Class.learning_area_id.is_(None),
        Class.stream == body.stream if body.stream is not None else Class.stream.is_(None),
    )
    existing = await session.scalar(dup_q)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Class '{existing.name}' already exists")

    cls = Class(
        school_id=school_id,
        education_level=EDUCATION_LEVEL_MAP[body.level],
        **body.model_dump(),
    )
    session.add(cls)
    await session.commit()
    await session.refresh(cls, ["learning_area"])
    return ClassResponse(
        **{k: getattr(cls, k) for k in ClassResponse.model_fields if k != "name"},
        name=cls.name,
    )


@router.patch("/classes/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: UUID, body: ClassUpdate, user: CurrentUser, session: SessionDep
):
    cls = await session.scalar(
        select(Class)
        .where(Class.id == class_id, Class.school_id == _school_id(user))
        .options(selectinload(Class.learning_area))
    )
    if not cls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(cls, field, value)
    await session.commit()
    await session.refresh(cls)
    return ClassResponse(
        **{k: getattr(cls, k) for k in ClassResponse.model_fields if k != "name"},
        name=cls.name,
    )


@router.delete("/classes/{class_id}", status_code=204)
async def delete_class(class_id: UUID, user: CurrentUser, session: SessionDep):
    cls = await session.scalar(
        select(Class)
        .where(Class.id == class_id, Class.school_id == _school_id(user))
    )
    if not cls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
    await session.delete(cls)
    await session.commit()


# ── Staff Positions ───────────────────────────────────────────────────────────

def _position_to_response(pos: StaffPosition) -> PositionResponse:
    return PositionResponse(
        id=pos.id,
        name=pos.name,
        code=pos.code,
        is_system_template=pos.is_system_template,
        is_active=pos.is_active,
        permissions=[p.permission_key for p in pos.permissions if p.granted],
    )


@router.get("/positions", response_model=list[PositionResponse])
async def list_positions(user: CurrentUser, session: SessionDep):
    school_id = _school_id(user)
    rows = list(await session.scalars(
        select(StaffPosition)
        .where(
            (StaffPosition.school_id == school_id) | (StaffPosition.school_id.is_(None))
        )
        .options(selectinload(StaffPosition.permissions))
        .order_by(StaffPosition.is_system_template.desc(), StaffPosition.name)
    ))
    return [_position_to_response(p) for p in rows]


@router.post("/positions", response_model=PositionResponse, status_code=201)
async def create_position(body: PositionCreate, user: CurrentUser, session: SessionDep):
    school_id = _school_id(user)

    duplicate = await session.scalar(
        select(StaffPosition).where(
            StaffPosition.school_id == school_id,
            StaffPosition.code == body.code,
        )
    )
    if duplicate:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Position code '{body.code}' already exists")

    pos = StaffPosition(
        school_id=school_id,
        name=body.name,
        code=body.code.upper(),
        is_system_template=False,
        created_by=user.id,
    )
    session.add(pos)
    await session.flush()

    for perm_key in body.permissions:
        session.add(PositionPermission(position_id=pos.id, permission_key=perm_key, granted=True))

    await session.commit()
    await session.refresh(pos, ["permissions"])
    return _position_to_response(pos)


@router.patch("/positions/{pos_id}", response_model=PositionResponse)
async def update_position(
    pos_id: UUID, body: PositionUpdate, user: CurrentUser, session: SessionDep
):
    pos = await session.scalar(
        select(StaffPosition)
        .where(StaffPosition.id == pos_id, StaffPosition.school_id == _school_id(user))
        .options(selectinload(StaffPosition.permissions))
    )
    if not pos:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Position not found")
    if pos.is_system_template:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot modify system positions")

    if body.name is not None:
        pos.name = body.name
    if body.is_active is not None:
        pos.is_active = body.is_active

    if body.permissions is not None:
        # Replace permission set
        for pp in pos.permissions:
            await session.delete(pp)
        await session.flush()
        for perm_key in body.permissions:
            session.add(PositionPermission(position_id=pos.id, permission_key=perm_key, granted=True))

    await session.commit()
    await session.refresh(pos, ["permissions"])
    return _position_to_response(pos)


@router.delete("/positions/{pos_id}", status_code=204)
async def delete_position(pos_id: UUID, user: CurrentUser, session: SessionDep):
    pos = await session.scalar(
        select(StaffPosition)
        .where(StaffPosition.id == pos_id, StaffPosition.school_id == _school_id(user))
    )
    if not pos:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Position not found")
    if pos.is_system_template:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot delete system positions")
    await session.delete(pos)
    await session.commit()
