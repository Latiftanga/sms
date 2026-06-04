from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import AcademicYear, Class
from app.models.school import School, SchoolConfig
from app.models.student import Guardian, Student, StudentClassEnrollment
from app.schemas.student import EnrollmentResponse, GuardianResponse, StudentResponse


async def _get_student(student_id: UUID, school_id: UUID, session: AsyncSession) -> Student:
    student = await session.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.school_id == school_id,
        )
    )
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return student


async def _get_current_year(school_id: UUID, session: AsyncSession) -> AcademicYear:
    year = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    )
    if not year:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "No active academic year. Set one in Settings → Academic Years.",
        )
    return year


async def _generate_register_number(
    school: School,
    academic_year: AcademicYear,
    session: AsyncSession,
) -> str:
    config = await session.scalar(
        select(SchoolConfig).where(SchoolConfig.school_id == school.id)
    )
    pattern = (config.register_number_pattern if config else None) or "{code}/{year}/{seq:04d}"

    seq = await session.scalar(
        select(func.count(StudentClassEnrollment.id)).where(
            StudentClassEnrollment.academic_year_id == academic_year.id
        )
    ) or 0
    seq += 1

    year_str = academic_year.name[:4]
    return pattern.format(code=school.code, year=year_str, seq=seq)


async def _enrollment_response(
    enrollment: StudentClassEnrollment,
    session: AsyncSession,
) -> EnrollmentResponse:
    cls = await session.get(Class, enrollment.class_id)
    year = await session.get(AcademicYear, enrollment.academic_year_id)
    return EnrollmentResponse(
        id=enrollment.id,
        created_at=enrollment.created_at,
        updated_at=enrollment.updated_at,
        student_id=enrollment.student_id,
        class_id=enrollment.class_id,
        class_name=cls.name if cls else "—",
        academic_year_id=enrollment.academic_year_id,
        year_name=year.name if year else "—",
        student_type=enrollment.student_type,
        register_number=enrollment.register_number,
        status=enrollment.status,
        house_id=enrollment.house_id,
        left_date=enrollment.left_date,
        left_reason=enrollment.left_reason,
    )


async def _to_response(
    student: Student,
    session: AsyncSession,
    *,
    school_id: UUID,
) -> StudentResponse:
    # Current-year enrollment
    current_year = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    )
    current_enrollment = None
    if current_year:
        enrollment = await session.scalar(
            select(StudentClassEnrollment).where(
                StudentClassEnrollment.student_id == student.id,
                StudentClassEnrollment.academic_year_id == current_year.id,
                StudentClassEnrollment.status == "ACTIVE",
            )
        )
        if enrollment:
            current_enrollment = await _enrollment_response(enrollment, session)

    # Guardians
    guardian_rows = await session.scalars(
        select(Guardian).where(Guardian.student_id == student.id)
    )
    guardians = [
        GuardianResponse(
            id=g.id,
            first_name=g.first_name,
            last_name=g.last_name,
            relationship_type=g.relationship_type,
            phone=g.phone,
            email=g.email,
            is_primary_contact=g.is_primary_contact,
        )
        for g in guardian_rows
    ]

    return StudentResponse(
        id=student.id,
        created_at=student.created_at,
        updated_at=student.updated_at,
        school_id=student.school_id,
        first_name=student.first_name,
        middle_name=student.middle_name,
        last_name=student.last_name,
        full_name=student.full_name,
        gender=student.gender,
        date_of_birth=student.date_of_birth,
        place_of_birth=student.place_of_birth,
        nationality=student.nationality,
        religion=student.religion,
        school_issued_id=student.school_issued_id,
        photo_url=student.photo_url,
        is_active=student.is_active,
        admission_date=student.admission_date,
        admission_number=student.admission_number,
        previous_school=student.previous_school,
        current_enrollment=current_enrollment,
        guardians=guardians,
    )
