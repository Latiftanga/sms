from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep, require
from app.api.v1.settings._helpers import _school_id, _current_year, _require_shs
from app.core.permissions import Permission
from app.models.academic import (
    AcademicTerm, AcademicYear, Class, ClassSubject, ClassTeacher,
    LearningArea, SchoolSubject, SubjectTeacher,
)
from app.models.staff import StaffMember
from app.models.school import School
from app.models.student import StudentClassEnrollment
from app.schemas.common import OrmBase, PagedResponse
from app.schemas.settings import (
    AcademicTermCreate, AcademicTermResponse, AcademicTermUpdate,
    AcademicYearCreate, AcademicYearResponse, AcademicYearUpdate,
    ClassCreate, ClassDetailResponse, ClassResponse, ClassTeacherAssign,
    ClassTeacherInfo, ClassUpdate,
    SchoolSubjectCreate, SchoolSubjectUpdate, SchoolSubjectResponse,
    ClassSubjectCreate, ClassSubjectUpdate, ClassSubjectResponse,
    SubjectTeacherInfo, SubjectTeacherAssign,
    LearningAreaCreate, LearningAreaResponse, LearningAreaUpdate,
    EDUCATION_LEVEL_MAP,
)

router = APIRouter()


# ── Academic Years ────────────────────────────────────────────────────────────

@router.get("/academic-years", response_model=PagedResponse[AcademicYearResponse],
            dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
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


@router.post("/academic-years", response_model=AcademicYearResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
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


@router.patch("/academic-years/{year_id}", response_model=AcademicYearResponse,
              dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
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
    year = await session.scalar(
        select(AcademicYear)
        .where(AcademicYear.id == year_id)
        .options(selectinload(AcademicYear.terms))
    )
    return AcademicYearResponse.model_validate(year)


@router.post("/academic-years/{year_id}/activate", response_model=AcademicYearResponse,
             dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def activate_academic_year(year_id: UUID, user: CurrentUser, session: SessionDep):
    school_id = _school_id(user)
    all_years = await session.scalars(
        select(AcademicYear).where(AcademicYear.school_id == school_id)
    )
    for y in all_years:
        y.is_current = y.id == year_id
    await session.commit()
    year = await session.scalar(
        select(AcademicYear)
        .where(AcademicYear.id == year_id, AcademicYear.school_id == school_id)
        .options(selectinload(AcademicYear.terms))
    )
    return AcademicYearResponse.model_validate(year)


@router.delete("/academic-years/{year_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
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

@router.post("/academic-years/{year_id}/terms", response_model=AcademicTermResponse,
             status_code=201, dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
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


@router.patch("/terms/{term_id}", response_model=AcademicTermResponse,
              dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def update_term(term_id: UUID, body: AcademicTermUpdate, user: CurrentUser, session: SessionDep):
    term = await session.scalar(
        select(AcademicTerm)
        .join(AcademicYear, AcademicTerm.academic_year_id == AcademicYear.id)
        .where(AcademicTerm.id == term_id, AcademicYear.school_id == _school_id(user))
    )
    if not term:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Term not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(term, field, value)
    await session.commit()
    await session.refresh(term)
    return AcademicTermResponse.model_validate(term)


@router.post("/terms/{term_id}/activate", response_model=AcademicTermResponse,
             dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def activate_term(term_id: UUID, user: CurrentUser, session: SessionDep):
    term = await session.scalar(
        select(AcademicTerm)
        .join(AcademicYear, AcademicTerm.academic_year_id == AcademicYear.id)
        .where(AcademicTerm.id == term_id, AcademicYear.school_id == _school_id(user))
    )
    if not term:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Term not found")
    siblings = await session.scalars(
        select(AcademicTerm).where(AcademicTerm.academic_year_id == term.academic_year_id)
    )
    for t in siblings:
        t.is_current = t.id == term_id
    await session.commit()
    await session.refresh(term)
    return AcademicTermResponse.model_validate(term)


@router.delete("/terms/{term_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def delete_term(term_id: UUID, user: CurrentUser, session: SessionDep):
    term = await session.scalar(
        select(AcademicTerm)
        .join(AcademicYear, AcademicTerm.academic_year_id == AcademicYear.id)
        .where(AcademicTerm.id == term_id, AcademicYear.school_id == _school_id(user))
    )
    if not term:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Term not found")
    if term.is_current:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot delete the current term")
    await session.delete(term)
    await session.commit()


# ── School Subjects ───────────────────────────────────────────────────────────

@router.get("/subjects", response_model=list[SchoolSubjectResponse],
            dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def list_school_subjects(user: CurrentUser, session: SessionDep):
    rows = await session.scalars(
        select(SchoolSubject)
        .where(SchoolSubject.school_id == _school_id(user))
        .order_by(SchoolSubject.name)
    )
    return [SchoolSubjectResponse.model_validate(r) for r in rows]


@router.post("/subjects", response_model=SchoolSubjectResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def create_school_subject(body: SchoolSubjectCreate, user: CurrentUser, session: SessionDep):
    subj = SchoolSubject(school_id=_school_id(user), **body.model_dump())
    session.add(subj)
    try:
        await session.commit()
        await session.refresh(subj)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f'Subject "{body.name}" already exists')
    return SchoolSubjectResponse.model_validate(subj)


@router.patch("/subjects/{subject_id}", response_model=SchoolSubjectResponse,
              dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def update_school_subject(
    subject_id: UUID, body: SchoolSubjectUpdate, user: CurrentUser, session: SessionDep
):
    subj = await session.scalar(
        select(SchoolSubject).where(
            SchoolSubject.id == subject_id, SchoolSubject.school_id == _school_id(user)
        )
    )
    if not subj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(subj, field, value)
    try:
        await session.commit()
        await session.refresh(subj)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A subject with that name already exists")
    return SchoolSubjectResponse.model_validate(subj)


@router.delete("/subjects/{subject_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def delete_school_subject(subject_id: UUID, user: CurrentUser, session: SessionDep):
    subj = await session.scalar(
        select(SchoolSubject).where(
            SchoolSubject.id == subject_id, SchoolSubject.school_id == _school_id(user)
        )
    )
    if not subj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found")
    await session.delete(subj)
    await session.commit()


# ── Learning Areas (SHS only) ─────────────────────────────────────────────────

@router.get("/learning-areas", response_model=PagedResponse[LearningAreaResponse],
            dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
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


@router.post("/learning-areas", response_model=LearningAreaResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
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


@router.patch("/learning-areas/{la_id}", response_model=LearningAreaResponse,
              dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def update_learning_area(
    la_id: UUID, body: LearningAreaUpdate, user: CurrentUser, session: SessionDep
):
    school = await session.get(School, _school_id(user))
    _require_shs(school)
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


@router.delete("/learning-areas/{la_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def delete_learning_area(la_id: UUID, user: CurrentUser, session: SessionDep):
    school = await session.get(School, _school_id(user))
    _require_shs(school)
    la = await session.scalar(
        select(LearningArea)
        .where(LearningArea.id == la_id, LearningArea.school_id == _school_id(user))
    )
    if not la:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning area not found")
    await session.delete(la)
    await session.commit()


# ── Classes ───────────────────────────────────────────────────────────────────

async def _get_class_owned(class_id: UUID, school_id: UUID, session: SessionDep) -> Class:
    cls = await session.scalar(
        select(Class).where(Class.id == class_id, Class.school_id == school_id)
    )
    if not cls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
    return cls


@router.get("/classes", response_model=PagedResponse[ClassResponse],
            dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
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


@router.post("/classes", response_model=ClassResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def create_class(body: ClassCreate, user: CurrentUser, session: SessionDep):
    school_id = _school_id(user)

    if body.learning_area_id:
        la = await session.scalar(
            select(LearningArea)
            .where(LearningArea.id == body.learning_area_id, LearningArea.school_id == school_id)
        )
        if not la:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning area not found")

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


@router.patch("/classes/{class_id}", response_model=ClassResponse,
              dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
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


@router.delete("/classes/{class_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def delete_class(class_id: UUID, user: CurrentUser, session: SessionDep):
    cls = await session.scalar(
        select(Class)
        .where(Class.id == class_id, Class.school_id == _school_id(user))
    )
    if not cls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
    await session.delete(cls)
    await session.commit()


# ── Class detail ──────────────────────────────────────────────────────────────

async def _class_detail(
    class_id: UUID, school_id: UUID, session: SessionDep
) -> ClassDetailResponse:
    cls = await session.scalar(
        select(Class)
        .where(Class.id == class_id, Class.school_id == school_id)
        .options(selectinload(Class.learning_area))
    )
    if not cls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")

    current_year = await _current_year(school_id, session)

    class_teacher: ClassTeacherInfo | None = None
    student_count = 0

    if current_year:
        ct_row = await session.execute(
            select(ClassTeacher, StaffMember)
            .join(StaffMember, StaffMember.id == ClassTeacher.staff_member_id)
            .where(
                ClassTeacher.class_id == class_id,
                ClassTeacher.academic_year_id == current_year.id,
            )
        )
        ct_pair = ct_row.first()
        if ct_pair:
            _, staff = ct_pair
            class_teacher = ClassTeacherInfo(
                staff_member_id=staff.id,
                staff_name=staff.full_name,
            )

        student_count = await session.scalar(
            select(func.count(StudentClassEnrollment.id)).where(
                StudentClassEnrollment.class_id == class_id,
                StudentClassEnrollment.academic_year_id == current_year.id,
                StudentClassEnrollment.status == "ACTIVE",
            )
        ) or 0

    subjects = list(await session.scalars(
        select(ClassSubject)
        .where(ClassSubject.class_id == class_id)
        .order_by(ClassSubject.subject_name)
    ))

    subject_teachers_by_subject: dict[UUID, list[SubjectTeacherInfo]] = {s.id: [] for s in subjects}
    if current_year and subjects:
        subject_ids = [s.id for s in subjects]
        st_rows = await session.execute(
            select(SubjectTeacher, StaffMember)
            .join(StaffMember, StaffMember.id == SubjectTeacher.staff_member_id)
            .where(
                SubjectTeacher.class_subject_id.in_(subject_ids),
                SubjectTeacher.academic_year_id == current_year.id,
                SubjectTeacher.is_active.is_(True),
            )
        )
        for st, staff in st_rows:
            if st.class_subject_id not in subject_teachers_by_subject:
                continue
            subject_teachers_by_subject[st.class_subject_id].append(
                SubjectTeacherInfo(
                    id=st.id,
                    staff_member_id=staff.id,
                    staff_name=staff.full_name,
                )
            )

    def _subject_response(s: ClassSubject) -> ClassSubjectResponse:
        return ClassSubjectResponse(
            id=s.id, created_at=s.created_at, updated_at=s.updated_at,
            subject_name=s.subject_name, subject_code=s.subject_code,
            is_core=s.is_core, is_active=s.is_active,
            teachers=subject_teachers_by_subject.get(s.id, []),
        )

    return ClassDetailResponse(
        id=cls.id,
        created_at=cls.created_at,
        updated_at=cls.updated_at,
        education_level=cls.education_level,
        level=cls.level,
        year=cls.year,
        stream=cls.stream,
        is_active=cls.is_active,
        learning_area=(
            LearningAreaResponse.model_validate(cls.learning_area)
            if cls.learning_area else None
        ),
        name=cls.name,
        class_teacher=class_teacher,
        student_count=student_count,
        current_year_id=current_year.id if current_year else None,
        current_year_name=current_year.name if current_year else None,
        subjects=[_subject_response(s) for s in subjects],
    )


@router.get("/classes/{class_id}/detail", response_model=ClassDetailResponse,
            dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def get_class_detail(class_id: UUID, user: CurrentUser, session: SessionDep):
    return await _class_detail(class_id, _school_id(user), session)


@router.put("/classes/{class_id}/teacher", response_model=ClassDetailResponse,
            dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def assign_class_teacher(
    class_id: UUID, body: ClassTeacherAssign, user: CurrentUser, session: SessionDep
):
    school_id = _school_id(user)

    cls = await session.scalar(
        select(Class).where(Class.id == class_id, Class.school_id == school_id)
    )
    if not cls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")

    staff = await session.scalar(
        select(StaffMember).where(
            StaffMember.id == body.staff_member_id,
            StaffMember.school_id == school_id,
            StaffMember.is_active.is_(True),
        )
    )
    if not staff:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff member not found")

    current_year = await _current_year(school_id, session)
    if not current_year:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No current academic year set. Go to Academic Calendar and mark a year as current.",
        )

    existing = await session.scalar(
        select(ClassTeacher).where(
            ClassTeacher.class_id == class_id,
            ClassTeacher.academic_year_id == current_year.id,
        )
    )
    if existing:
        existing.staff_member_id = body.staff_member_id
    else:
        session.add(ClassTeacher(
            class_id=class_id,
            staff_member_id=body.staff_member_id,
            academic_year_id=current_year.id,
        ))

    await session.commit()
    return await _class_detail(class_id, school_id, session)


@router.delete("/classes/{class_id}/teacher", status_code=204,
               dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def remove_class_teacher(class_id: UUID, user: CurrentUser, session: SessionDep):
    school_id = _school_id(user)
    await _get_class_owned(class_id, school_id, session)

    current_year = await _current_year(school_id, session)
    if not current_year:
        return

    ct = await session.scalar(
        select(ClassTeacher).where(
            ClassTeacher.class_id == class_id,
            ClassTeacher.academic_year_id == current_year.id,
        )
    )
    if ct:
        await session.delete(ct)
        await session.commit()


# ── Class Subjects ────────────────────────────────────────────────────────────

@router.get("/classes/{class_id}/subjects", response_model=list[ClassSubjectResponse],
            dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def list_class_subjects(class_id: UUID, user: CurrentUser, session: SessionDep):
    await _get_class_owned(class_id, _school_id(user), session)
    rows = list(await session.scalars(
        select(ClassSubject)
        .where(ClassSubject.class_id == class_id)
        .order_by(ClassSubject.subject_name)
    ))
    return [ClassSubjectResponse.model_validate(r) for r in rows]


@router.post("/classes/{class_id}/subjects", response_model=ClassSubjectResponse,
             status_code=201, dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def add_class_subject(
    class_id: UUID, body: ClassSubjectCreate, user: CurrentUser, session: SessionDep
):
    await _get_class_owned(class_id, _school_id(user), session)

    existing = await session.scalar(
        select(ClassSubject).where(
            ClassSubject.class_id == class_id,
            ClassSubject.subject_code == body.subject_code,
        )
    )
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Subject with code '{body.subject_code}' already exists in this class",
        )

    subj = ClassSubject(
        class_id=class_id,
        subject_name=body.subject_name,
        subject_code=body.subject_code,
        is_core=body.is_core,
    )
    session.add(subj)
    await session.commit()
    await session.refresh(subj)
    return ClassSubjectResponse.model_validate(subj)


@router.patch("/classes/{class_id}/subjects/{subject_id}",
              response_model=ClassSubjectResponse,
              dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def update_class_subject(
    class_id: UUID, subject_id: UUID, body: ClassSubjectUpdate,
    user: CurrentUser, session: SessionDep,
):
    await _get_class_owned(class_id, _school_id(user), session)

    subj = await session.scalar(
        select(ClassSubject).where(
            ClassSubject.id == subject_id, ClassSubject.class_id == class_id
        )
    )
    if not subj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found")

    if body.subject_name is not None:
        subj.subject_name = body.subject_name
    if body.subject_code is not None and body.subject_code != subj.subject_code:
        conflict = await session.scalar(
            select(ClassSubject).where(
                ClassSubject.class_id == class_id,
                ClassSubject.subject_code == body.subject_code,
                ClassSubject.id != subject_id,
            )
        )
        if conflict:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Subject with code '{body.subject_code}' already exists in this class",
            )
        subj.subject_code = body.subject_code
    if body.is_core is not None:
        subj.is_core = body.is_core
    if body.is_active is not None:
        subj.is_active = body.is_active

    await session.commit()
    await session.refresh(subj)
    return ClassSubjectResponse.model_validate(subj)


@router.delete("/classes/{class_id}/subjects/{subject_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def delete_class_subject(
    class_id: UUID, subject_id: UUID, user: CurrentUser, session: SessionDep
):
    await _get_class_owned(class_id, _school_id(user), session)

    subj = await session.scalar(
        select(ClassSubject).where(
            ClassSubject.id == subject_id, ClassSubject.class_id == class_id
        )
    )
    if not subj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found")

    try:
        await session.delete(subj)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Subject has student registrations and cannot be deleted. Deactivate it instead.",
        )


# ── Subject Teachers ──────────────────────────────────────────────────────────

@router.post(
    "/classes/{class_id}/subjects/{subject_id}/teachers",
    response_model=SubjectTeacherInfo,
    status_code=201,
    dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)],
)
async def assign_subject_teacher(
    class_id: UUID,
    subject_id: UUID,
    body: SubjectTeacherAssign,
    user: CurrentUser,
    session: SessionDep,
):
    school_id = _school_id(user)
    await _get_class_owned(class_id, school_id, session)

    subj = await session.scalar(
        select(ClassSubject).where(
            ClassSubject.id == subject_id, ClassSubject.class_id == class_id
        )
    )
    if not subj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found")

    current_year = await _current_year(school_id, session)
    if not current_year:
        raise HTTPException(status.HTTP_409_CONFLICT, "No active academic year")

    staff = await session.scalar(
        select(StaffMember).where(
            StaffMember.id == body.staff_member_id, StaffMember.school_id == school_id
        )
    )
    if not staff:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff member not found")

    existing = await session.scalar(
        select(SubjectTeacher).where(
            SubjectTeacher.class_subject_id == subject_id,
            SubjectTeacher.staff_member_id == body.staff_member_id,
            SubjectTeacher.academic_year_id == current_year.id,
        )
    )
    if existing:
        existing.is_active = True
        await session.commit()
        return SubjectTeacherInfo(
            id=existing.id,
            staff_member_id=staff.id,
            staff_name=staff.full_name,
        )

    st = SubjectTeacher(
        class_subject_id=subject_id,
        staff_member_id=body.staff_member_id,
        academic_year_id=current_year.id,
    )
    session.add(st)
    await session.commit()
    await session.refresh(st)
    return SubjectTeacherInfo(id=st.id, staff_member_id=staff.id, staff_name=staff.full_name)


@router.delete(
    "/classes/{class_id}/subjects/{subject_id}/teachers/{st_id}",
    status_code=204,
    dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)],
)
async def remove_subject_teacher(
    class_id: UUID, subject_id: UUID, st_id: UUID,
    user: CurrentUser, session: SessionDep,
):
    await _get_class_owned(class_id, _school_id(user), session)

    st = await session.scalar(
        select(SubjectTeacher).where(
            SubjectTeacher.id == st_id,
            SubjectTeacher.class_subject_id == subject_id,
        )
    )
    if not st:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")

    await session.delete(st)
    await session.commit()


# ── Teaching staff list ───────────────────────────────────────────────────────

class TeachingStaffItem(OrmBase):
    id: UUID
    full_name: str
    staff_id: str | None = None


@router.get("/teaching-staff", response_model=list[TeachingStaffItem],
            dependencies=[require(Permission.MANAGE_ACADEMIC_STRUCTURE)])
async def list_teaching_staff(user: CurrentUser, session: SessionDep):
    rows = await session.scalars(
        select(StaffMember)
        .where(
            StaffMember.school_id == _school_id(user),
            StaffMember.category == "TEACHING",
            StaffMember.is_active.is_(True),
        )
        .order_by(StaffMember.last_name, StaffMember.first_name)
    )
    return [
        TeachingStaffItem(id=m.id, full_name=m.full_name, staff_id=m.staff_id)
        for m in rows
    ]
