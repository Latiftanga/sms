import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep, require
from app.core.permissions import Permission
from app.models.academic import AcademicYear, Class
from app.models.student import Guardian, Student, StudentClassEnrollment
from app.schemas.common import PagedResponse
from app.schemas.student import (
    StudentCreate, StudentListItem, StudentResponse, StudentUpdate,
)

from ._helpers import _get_student, _get_current_year, _to_response

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=PagedResponse[StudentListItem],
            dependencies=[require(Permission.VIEW_STUDENTS)])
async def list_students(
    user: CurrentUser,
    session: SessionDep,
    search: str | None = None,
    class_id: str | None = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 25,
):
    school_id = user.school_id

    # Current academic year for enrollment join
    current_year = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    )

    conditions = [Student.school_id == school_id, Student.is_active == is_active]
    if search:
        term = f"%{search.lower()}%"
        conditions.append(
            or_(
                func.lower(Student.first_name).like(term),
                func.lower(Student.last_name).like(term),
                func.lower(Student.middle_name).like(term),
            )
        )

    # Base query with optional current-year enrollment join
    if current_year:
        enrollment_cond = and_(
            StudentClassEnrollment.student_id == Student.id,
            StudentClassEnrollment.academic_year_id == current_year.id,
            StudentClassEnrollment.status == "ACTIVE",
        )
        if class_id:
            conditions.append(StudentClassEnrollment.class_id == uuid.UUID(class_id))

        rows = await session.execute(
            select(
                Student,
                StudentClassEnrollment.register_number,
                StudentClassEnrollment.class_id,
                Class.id.label("cid"),
                AcademicYear.name.label("year_name"),
            )
            .outerjoin(StudentClassEnrollment, enrollment_cond)
            .outerjoin(Class, Class.id == StudentClassEnrollment.class_id)
            .outerjoin(AcademicYear, AcademicYear.id == StudentClassEnrollment.academic_year_id)
            .where(*conditions)
            .order_by(Student.last_name, Student.first_name)
            .offset(skip).limit(limit)
        )
        total = await session.scalar(
            select(func.count(Student.id))
            .outerjoin(StudentClassEnrollment, enrollment_cond)
            .where(*conditions)
        ) or 0

        items = []
        for row in rows:
            s = row[0]
            items.append(StudentListItem(
                id=s.id,
                first_name=s.first_name,
                middle_name=s.middle_name,
                last_name=s.last_name,
                gender=s.gender,
                photo_url=s.photo_url,
                is_active=s.is_active,
                admission_number=s.admission_number,
                register_number=row.register_number,
                class_name=None,   # resolved below
                class_id=row.class_id,
                year_name=row.year_name,
            ))

        # Resolve class names in one query (eager-load learning_area for SHS class names)
        all_class_ids = {i.class_id for i in items if i.class_id}
        if all_class_ids:
            class_rows = await session.scalars(
                select(Class)
                .options(selectinload(Class.learning_area))
                .where(Class.id.in_(all_class_ids))
            )
            class_map = {c.id: c.name for c in class_rows}
            for item in items:
                if item.class_id:
                    item.class_name = class_map.get(item.class_id)

    else:
        # No current year — simple query
        total = await session.scalar(
            select(func.count(Student.id)).where(*conditions)
        ) or 0
        rows = await session.scalars(
            select(Student).where(*conditions)
            .order_by(Student.last_name, Student.first_name)
            .offset(skip).limit(limit)
        )
        items = [
            StudentListItem(
                id=s.id,
                first_name=s.first_name,
                middle_name=s.middle_name,
                last_name=s.last_name,
                gender=s.gender,
                photo_url=s.photo_url,
                is_active=s.is_active,
                admission_number=s.admission_number,
                register_number=None,
                class_name=None,
                class_id=None,
                year_name=None,
            )
            for s in rows
        ]

    return PagedResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("", response_model=StudentResponse, status_code=201,
             dependencies=[require(Permission.ENROLL_STUDENTS)])
async def create_student(
    body: StudentCreate,
    user: CurrentUser,
    session: SessionDep,
):
    school_id = user.school_id

    student = Student(
        id=uuid.uuid4(),
        school_id=school_id,
        first_name=body.first_name,
        middle_name=body.middle_name,
        last_name=body.last_name,
        gender=body.gender,
        date_of_birth=body.date_of_birth,
        place_of_birth=body.place_of_birth,
        nationality=body.nationality,
        religion=body.religion,
        admission_date=body.admission_date,
        admission_number=body.admission_number,
        previous_school=body.previous_school,
        is_active=True,
    )
    session.add(student)
    await session.flush()

    for g in body.guardians:
        session.add(Guardian(
            id=uuid.uuid4(),
            student_id=student.id,
            first_name=g.first_name,
            last_name=g.last_name,
            relationship_type=g.relationship_type,
            phone=g.phone,
            email=g.email,
            is_primary_contact=g.is_primary_contact,
        ))

    await session.commit()
    await session.refresh(student)
    return await _to_response(student, session, school_id=school_id)


@router.get("/{student_id}", response_model=StudentResponse,
            dependencies=[require(Permission.VIEW_STUDENTS)])
async def get_student(
    student_id: uuid.UUID,
    user: CurrentUser,
    session: SessionDep,
):
    student = await _get_student(student_id, user.school_id, session)
    return await _to_response(student, session, school_id=user.school_id)


@router.patch("/{student_id}", response_model=StudentResponse,
              dependencies=[require(Permission.ENROLL_STUDENTS)])
async def update_student(
    student_id: uuid.UUID,
    body: StudentUpdate,
    user: CurrentUser,
    session: SessionDep,
):
    student = await _get_student(student_id, user.school_id, session)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    await session.commit()
    await session.refresh(student)
    return await _to_response(student, session, school_id=user.school_id)


@router.delete("/{student_id}", status_code=204,
               dependencies=[require(Permission.ENROLL_STUDENTS)])
async def deactivate_student(
    student_id: uuid.UUID,
    user: CurrentUser,
    session: SessionDep,
):
    student = await _get_student(student_id, user.school_id, session)
    student.is_active = False
    await session.commit()
