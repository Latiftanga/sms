from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep
from app.models.academic import AcademicTerm, AcademicYear, Class, LearningArea
from app.models.school import School
from app.schemas.settings import (
    AcademicTermCreate, AcademicTermResponse, AcademicTermUpdate,
    AcademicYearCreate, AcademicYearResponse, AcademicYearUpdate,
    ClassCreate, ClassResponse, ClassUpdate,
    LearningAreaCreate, LearningAreaResponse, LearningAreaUpdate,
    SchoolProfileUpdate, EDUCATION_LEVEL_MAP,
)
from app.schemas.school import SchoolResponse

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


# ── Academic Years ────────────────────────────────────────────────────────────

@router.get("/academic-years", response_model=list[AcademicYearResponse])
async def list_academic_years(user: CurrentUser, session: SessionDep):
    rows = await session.scalars(
        select(AcademicYear)
        .where(AcademicYear.school_id == _school_id(user))
        .options(selectinload(AcademicYear.terms))
        .order_by(AcademicYear.start_date.desc())
    )
    return [AcademicYearResponse.model_validate(r) for r in rows]


@router.post("/academic-years", response_model=AcademicYearResponse, status_code=201)
async def create_academic_year(
    body: AcademicYearCreate, user: CurrentUser, session: SessionDep
):
    year = AcademicYear(school_id=_school_id(user), **body.model_dump())
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

@router.get("/learning-areas", response_model=list[LearningAreaResponse])
async def list_learning_areas(user: CurrentUser, session: SessionDep):
    school = await session.get(School, _school_id(user))
    _require_shs(school)
    rows = await session.scalars(
        select(LearningArea)
        .where(LearningArea.school_id == _school_id(user))
        .order_by(LearningArea.name)
    )
    return [LearningAreaResponse.model_validate(r) for r in rows]


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

@router.get("/classes", response_model=list[ClassResponse])
async def list_classes(user: CurrentUser, session: SessionDep):
    rows = await session.scalars(
        select(Class)
        .where(Class.school_id == _school_id(user))
        .options(selectinload(Class.learning_area))
        .order_by(Class.education_level, Class.level, Class.year, Class.stream)
    )
    return [
        ClassResponse(
            **{k: getattr(r, k) for k in ClassResponse.model_fields if k != "name"},
            name=r.name,
        )
        for r in rows
    ]


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
