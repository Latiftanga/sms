"""
Subject registration API.

A subject teacher registers which students in their assigned class are taking
their subject for the current term. This creates StudentSubjectRegistration
records that gate score entry.

Endpoints:
  GET  /subject-registration/{class_subject_id}   — list students + their status
  POST /subject-registration/{class_subject_id}   — save (upsert) the register
"""
import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, RedisDep, SessionDep, require
from app.core.permissions import Permission
from app.models.academic import (
    AcademicTerm, AcademicYear, Class, ClassSubject, SubjectTeacher,
)
from app.models.assessment import StudentSubjectRegistration
from app.models.student import Student, StudentClassEnrollment, StudentTermEnrollment
from app.schemas.common import OrmBase
from app.services.permissions import resolve_all_permissions

router = APIRouter(prefix="/subject-registration", tags=["subject-registration"])


class SubjectRegisterStudent(OrmBase):
    student_id: str
    full_name: str
    register_number: str | None
    gender: str
    term_enrollment_id: str
    registered: bool


class SubjectRegisterResponse(OrmBase):
    class_subject_id: str
    class_name: str
    subject_name: str
    subject_code: str
    term_name: str
    year_name: str
    students: list[SubjectRegisterStudent]


class SubjectRegisterSave(OrmBase):
    term_enrollment_ids: list[str]   # all enrolled IDs; absent = not taking subject


@router.get("/{class_subject_id}", response_model=SubjectRegisterResponse,
            dependencies=[require(Permission.ENTER_SCORES)])
async def get_register(
    class_subject_id: uuid.UUID,
    user: CurrentUser,
    redis: RedisDep,
    session: SessionDep,
):
    school_id = user.school_id

    # Resolve current year and term
    current_year = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    )
    if not current_year:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No active academic year.")

    current_term = await session.scalar(
        select(AcademicTerm).where(
            AcademicTerm.academic_year_id == current_year.id,
            AcademicTerm.is_current.is_(True),
        )
    )
    if not current_term:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No active term.")

    # Verify the class subject belongs to this school
    cs = await session.scalar(
        select(ClassSubject)
        .join(Class, ClassSubject.class_id == Class.id)
        .where(
            ClassSubject.id == class_subject_id,
            Class.school_id == school_id,
            ClassSubject.is_active.is_(True),
        )
    )
    if not cs:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found.")

    # Verify the user is the assigned subject teacher (unless admin)
    perms = await resolve_all_permissions(user, redis, session)
    is_admin = perms.get(Permission.MANAGE_STAFF) or perms.get(Permission.MANAGE_SCHOOL_CONFIG)
    if not is_admin and user.staff_member_id:
        is_assigned = await session.scalar(
            select(SubjectTeacher).where(
                SubjectTeacher.class_subject_id == class_subject_id,
                SubjectTeacher.staff_member_id == user.staff_member_id,
                SubjectTeacher.academic_year_id == current_year.id,
                SubjectTeacher.is_active.is_(True),
            )
        )
        if not is_assigned:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                "You are not assigned to teach this subject.")

    # Fetch the class with its name
    cls = await session.scalar(
        select(Class)
        .options(selectinload(Class.learning_area))
        .where(Class.id == cs.class_id)
    )

    # Get all students enrolled in this class for the current term
    rows = await session.execute(
        select(Student, StudentClassEnrollment, StudentTermEnrollment)
        .join(StudentClassEnrollment, StudentClassEnrollment.student_id == Student.id)
        .join(
            StudentTermEnrollment,
            and_(
                StudentTermEnrollment.student_class_enrollment_id == StudentClassEnrollment.id,
                StudentTermEnrollment.academic_term_id == current_term.id,
            ),
        )
        .where(
            Student.school_id == school_id,
            Student.is_active.is_(True),
            StudentClassEnrollment.class_id == cs.class_id,
            StudentClassEnrollment.status == "ACTIVE",
            StudentClassEnrollment.academic_year_id == current_year.id,
        )
        .order_by(Student.last_name, Student.first_name)
    )
    student_rows = rows.all()

    # Fetch existing registrations
    term_enrollment_ids = [r[2].id for r in student_rows]
    existing_ids: set[uuid.UUID] = set()
    if term_enrollment_ids:
        regs = await session.scalars(
            select(StudentSubjectRegistration).where(
                StudentSubjectRegistration.class_subject_id == class_subject_id,
                StudentSubjectRegistration.student_term_enrollment_id.in_(term_enrollment_ids),
                StudentSubjectRegistration.is_active.is_(True),
            )
        )
        existing_ids = {r.student_term_enrollment_id for r in regs}

    return SubjectRegisterResponse(
        class_subject_id=str(class_subject_id),
        class_name=cls.name,
        subject_name=cs.subject_name,
        subject_code=cs.subject_code,
        term_name=current_term.name,
        year_name=current_year.name,
        students=[
            SubjectRegisterStudent(
                student_id=str(s.id),
                full_name=s.full_name,
                register_number=sce.register_number,
                gender=s.gender,
                term_enrollment_id=str(ste.id),
                registered=ste.id in existing_ids,
            )
            for s, sce, ste in student_rows
        ],
    )


@router.post("/{class_subject_id}", status_code=204,
             dependencies=[require(Permission.ENTER_SCORES)])
async def save_register(
    class_subject_id: uuid.UUID,
    body: SubjectRegisterSave,
    user: CurrentUser,
    redis: RedisDep,
    session: SessionDep,
):
    """
    Upsert subject registrations. Provided IDs are marked active;
    existing registrations NOT in the list are deactivated (not deleted).
    """
    school_id = user.school_id

    # Verify class subject belongs to this school
    cs = await session.scalar(
        select(ClassSubject)
        .join(Class, ClassSubject.class_id == Class.id)
        .where(ClassSubject.id == class_subject_id, Class.school_id == school_id)
    )
    if not cs:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found.")

    # Verify teacher assignment (unless admin)
    current_year = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    )
    perms = await resolve_all_permissions(user, redis, session)
    is_admin = perms.get(Permission.MANAGE_STAFF) or perms.get(Permission.MANAGE_SCHOOL_CONFIG)
    if not is_admin and user.staff_member_id and current_year:
        is_assigned = await session.scalar(
            select(SubjectTeacher).where(
                SubjectTeacher.class_subject_id == class_subject_id,
                SubjectTeacher.staff_member_id == user.staff_member_id,
                SubjectTeacher.academic_year_id == current_year.id,
                SubjectTeacher.is_active.is_(True),
            )
        )
        if not is_assigned:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                "You are not assigned to teach this subject.")

    enrolled_ids = {uuid.UUID(i) for i in body.term_enrollment_ids}

    # Load all existing registrations for this subject
    existing = await session.scalars(
        select(StudentSubjectRegistration).where(
            StudentSubjectRegistration.class_subject_id == class_subject_id,
        )
    )
    existing_map: dict[uuid.UUID, StudentSubjectRegistration] = {
        r.student_term_enrollment_id: r for r in existing
    }

    # Activate or create for enrolled; deactivate for removed
    for ste_id in enrolled_ids:
        if ste_id in existing_map:
            existing_map[ste_id].is_active = True
        else:
            session.add(StudentSubjectRegistration(
                id=uuid.uuid4(),
                student_term_enrollment_id=ste_id,
                class_subject_id=class_subject_id,
                is_active=True,
            ))

    for ste_id, reg in existing_map.items():
        if ste_id not in enrolled_ids:
            reg.is_active = False

    await session.commit()
