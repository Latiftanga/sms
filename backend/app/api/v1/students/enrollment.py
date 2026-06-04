import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep, require
from app.core.permissions import Permission
from app.models.academic import AcademicTerm, AcademicYear, Class
from app.models.school import School
from app.models.student import StudentClassEnrollment, StudentTermEnrollment
from app.schemas.student import EnrollmentCreate, EnrollmentResponse, EnrollmentUpdate

from ._helpers import (
    _enrollment_response, _generate_register_number,
    _get_current_year, _get_student,
)

router = APIRouter()


@router.get("/{student_id}/enrollments", response_model=list[EnrollmentResponse],
            dependencies=[require(Permission.VIEW_STUDENTS)])
async def list_enrollments(
    student_id: uuid.UUID,
    user: CurrentUser,
    session: SessionDep,
):
    await _get_student(student_id, user.school_id, session)
    rows = await session.scalars(
        select(StudentClassEnrollment)
        .where(StudentClassEnrollment.student_id == student_id)
        .order_by(StudentClassEnrollment.created_at.desc())
    )
    result = []
    for e in rows:
        result.append(await _enrollment_response(e, session))
    return result


@router.post("/{student_id}/enroll", response_model=EnrollmentResponse, status_code=201,
             dependencies=[require(Permission.ENROLL_STUDENTS)])
async def enroll_student(
    student_id: uuid.UUID,
    body: EnrollmentCreate,
    user: CurrentUser,
    session: SessionDep,
):
    school_id = user.school_id
    student = await _get_student(student_id, school_id, session)

    # Resolve academic year
    if body.academic_year_id:
        year = await session.scalar(
            select(AcademicYear).where(
                AcademicYear.id == body.academic_year_id,
                AcademicYear.school_id == school_id,
            )
        )
        if not year:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Academic year not found")
    else:
        year = await _get_current_year(school_id, session)

    # Check not already enrolled this year
    existing = await session.scalar(
        select(StudentClassEnrollment).where(
            StudentClassEnrollment.student_id == student_id,
            StudentClassEnrollment.academic_year_id == year.id,
        )
    )
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Student is already enrolled for {year.name}",
        )

    # Verify class belongs to this school
    cls = await session.scalar(
        select(Class).where(
            Class.id == body.class_id,
            Class.school_id == school_id,
            Class.is_active.is_(True),
        )
    )
    if not cls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")

    # Generate register number
    school = await session.get(School, school_id)
    register_number = await _generate_register_number(school, year, session)

    enrollment = StudentClassEnrollment(
        id=uuid.uuid4(),
        student_id=student_id,
        class_id=body.class_id,
        academic_year_id=year.id,
        house_id=body.house_id,
        student_type=body.student_type,
        register_number=register_number,
        status="ACTIVE",
    )
    session.add(enrollment)
    await session.flush()

    # Auto-create term enrollment records for all terms in this year
    terms = await session.scalars(
        select(AcademicTerm).where(AcademicTerm.academic_year_id == year.id)
    )
    for term in terms:
        session.add(StudentTermEnrollment(
            id=uuid.uuid4(),
            student_class_enrollment_id=enrollment.id,
            academic_term_id=term.id,
            enrolled_date=date.today(),
            fee_status="NOT_APPLICABLE",
        ))

    await session.commit()
    await session.refresh(enrollment)
    return await _enrollment_response(enrollment, session)


@router.patch("/{student_id}/enrollments/{enrollment_id}",
              response_model=EnrollmentResponse,
              dependencies=[require(Permission.ENROLL_STUDENTS)])
async def update_enrollment(
    student_id: uuid.UUID,
    enrollment_id: uuid.UUID,
    body: EnrollmentUpdate,
    user: CurrentUser,
    session: SessionDep,
):
    await _get_student(student_id, user.school_id, session)

    enrollment = await session.scalar(
        select(StudentClassEnrollment).where(
            StudentClassEnrollment.id == enrollment_id,
            StudentClassEnrollment.student_id == student_id,
        )
    )
    if not enrollment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enrollment not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(enrollment, field, value)

    await session.commit()
    await session.refresh(enrollment)
    return await _enrollment_response(enrollment, session)
