from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import CurrentUser, RedisDep, SessionDep
from app.core.permissions import Permission
from app.models.academic import AcademicTerm, AcademicYear, Class, ClassSubject, ClassTeacher, LearningArea, SchoolCalendar, SubjectTeacher
from sqlalchemy.orm import selectinload
from app.models.attendance import AttendanceRecord
from app.models.staff import StaffMember
from app.models.student import Student, StudentClassEnrollment, StudentTermEnrollment
from app.models.user import User
from app.services.permissions import resolve_all_permissions

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ── Response models ───────────────────────────────────────────────────────────

class TermSummary(BaseModel):
    id: str
    name: str
    year_name: str
    start_date: str
    end_date: str
    is_current: bool


class AdminStats(BaseModel):
    staff_total: int
    staff_no_account: int
    classes_total: int
    classes_no_teacher: int
    students_total: int
    attendance_submitted_today: int   # classes with attendance marked today
    attendance_classes_today: int     # total classes that should have attendance today


class MySubject(BaseModel):
    class_subject_id: str
    subject_name: str
    subject_code: str


class MyClass(BaseModel):
    id: str
    name: str
    education_level: str
    level: str
    year: int | None
    stream: str | None
    subjects: list[MySubject]   # populated for subject teachers; empty for class teachers


class DashboardSummary(BaseModel):
    role: str                           # admin | class_teacher | subject_teacher | staff | student | parent
    current_term: TermSummary | None
    admin: AdminStats | None            # only for admin role
    my_classes: list[MyClass] | None    # class_teacher and subject_teacher roles


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _current_term(school_id: UUID, session) -> TermSummary | None:
    row = await session.execute(
        select(AcademicTerm, AcademicYear)
        .join(AcademicYear, AcademicTerm.academic_year_id == AcademicYear.id)
        .where(
            AcademicYear.school_id == school_id,
            AcademicTerm.is_current.is_(True),
        )
        .limit(1)
    )
    pair = row.first()
    if not pair:
        return None
    term, year = pair
    return TermSummary(
        id=str(term.id),
        name=term.name,
        year_name=year.name,
        start_date=term.start_date.isoformat(),
        end_date=term.end_date.isoformat(),
        is_current=term.is_current,
    )


async def _admin_stats(school_id: UUID, session) -> AdminStats:
    # Active staff
    staff_total = await session.scalar(
        select(func.count(StaffMember.id)).where(
            StaffMember.school_id == school_id,
            StaffMember.is_active.is_(True),
        )
    ) or 0

    # Active staff with no linked active user account
    has_account_ids = select(User.staff_member_id).where(
        User.staff_member_id.is_not(None),
        User.is_active.is_(True),
    )
    staff_no_account = await session.scalar(
        select(func.count(StaffMember.id)).where(
            StaffMember.school_id == school_id,
            StaffMember.is_active.is_(True),
            StaffMember.id.not_in(has_account_ids),
        )
    ) or 0

    # Total active classes
    classes_total = await session.scalar(
        select(func.count(Class.id)).where(
            Class.school_id == school_id,
            Class.is_active.is_(True),
        )
    ) or 0

    # Classes with no teacher assigned in the current academic year
    current_year = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    )
    if current_year:
        assigned_ids = select(ClassTeacher.class_id).where(
            ClassTeacher.academic_year_id == current_year.id
        )
        classes_no_teacher = await session.scalar(
            select(func.count(Class.id)).where(
                Class.school_id == school_id,
                Class.is_active.is_(True),
                Class.id.not_in(assigned_ids),
            )
        ) or 0
    else:
        classes_no_teacher = classes_total

    students_total = await session.scalar(
        select(func.count(Student.id)).where(
            Student.school_id == school_id,
            Student.is_active.is_(True),
        )
    ) or 0

    # Today's attendance coverage
    from datetime import date as _date
    today = _date.today()
    today_cal = await session.scalar(
        select(SchoolCalendar).where(
            SchoolCalendar.school_id == school_id,
            SchoolCalendar.date == today,
            SchoolCalendar.day_type == "SCHOOL_DAY",
        )
    )
    att_submitted = 0
    if today_cal and classes_total:
        # Count distinct classes that have at least one attendance record today
        att_submitted = await session.scalar(
            select(func.count(func.distinct(StudentClassEnrollment.class_id)))
            .join(StudentTermEnrollment,
                  StudentTermEnrollment.student_class_enrollment_id == StudentClassEnrollment.id)
            .join(AttendanceRecord,
                  AttendanceRecord.student_term_enrollment_id == StudentTermEnrollment.id)
            .where(
                StudentClassEnrollment.class_id.in_(
                    select(Class.id).where(Class.school_id == school_id, Class.is_active.is_(True))
                ),
                AttendanceRecord.school_calendar_id == today_cal.id,
            )
        ) or 0

    return AdminStats(
        staff_total=staff_total,
        staff_no_account=staff_no_account,
        classes_total=classes_total,
        classes_no_teacher=classes_no_teacher,
        students_total=students_total,
        attendance_submitted_today=att_submitted,
        attendance_classes_today=classes_total if today_cal else 0,
    )


async def _my_classes(
    staff_member_id: UUID, school_id: UUID, session
) -> tuple[list[MyClass], bool]:
    """
    Returns (classes, is_class_teacher).
    Class teachers get their assigned class(es) with no subject detail.
    Subject teachers get the distinct classes they teach with their subjects listed.
    """
    current_year = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    )
    if not current_year:
        return [], False

    # 1. Check class teacher assignment first
    ct_rows = await session.execute(
        select(Class)
        .options(selectinload(Class.learning_area))
        .join(ClassTeacher, ClassTeacher.class_id == Class.id)
        .where(
            ClassTeacher.staff_member_id == staff_member_id,
            ClassTeacher.academic_year_id == current_year.id,
            Class.is_active.is_(True),
        )
        .order_by(Class.level, Class.year, Class.stream)
    )
    class_teacher_classes = list(ct_rows.scalars())
    if class_teacher_classes:
        return [
            MyClass(
                id=str(c.id), name=c.name,
                education_level=c.education_level,
                level=c.level, year=c.year, stream=c.stream,
                subjects=[],
            )
            for c in class_teacher_classes
        ], True

    # 2. Fall back to subject teacher assignments
    st_rows = await session.execute(
        select(ClassSubject, Class)
        .join(Class, ClassSubject.class_id == Class.id)
        .options(selectinload(Class.learning_area))
        .join(SubjectTeacher, SubjectTeacher.class_subject_id == ClassSubject.id)
        .where(
            SubjectTeacher.staff_member_id == staff_member_id,
            SubjectTeacher.academic_year_id == current_year.id,
            SubjectTeacher.is_active.is_(True),
            ClassSubject.is_active.is_(True),
            Class.is_active.is_(True),
        )
        .order_by(Class.level, Class.year, Class.stream, ClassSubject.subject_name)
    )

    # Group subjects by class
    class_subjects: dict[str, tuple[Class, list[MySubject]]] = {}
    for cs, cls in st_rows:
        key = str(cls.id)
        if key not in class_subjects:
            class_subjects[key] = (cls, [])
        class_subjects[key][1].append(
            MySubject(
                class_subject_id=str(cs.id),
                subject_name=cs.subject_name,
                subject_code=cs.subject_code,
            )
        )

    return [
        MyClass(
            id=key, name=cls.name,
            education_level=cls.education_level,
            level=cls.level, year=cls.year, stream=cls.stream,
            subjects=subjects,
        )
        for key, (cls, subjects) in class_subjects.items()
    ], False


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/summary", response_model=DashboardSummary)
async def summary(user: CurrentUser, redis: RedisDep, session: SessionDep):
    # Students and parents get minimal response
    if user.system_role in ("STUDENT", "PARENT"):
        return DashboardSummary(
            role=user.system_role.lower(),
            current_term=None,
            admin=None,
            my_classes=None,
        )

    school_id = user.school_id
    perms = await resolve_all_permissions(user, redis, session)

    is_admin = perms.get(Permission.MANAGE_STAFF) or perms.get(Permission.MANAGE_SCHOOL_CONFIG)
    is_teacher = perms.get(Permission.MARK_ATTENDANCE) or perms.get(Permission.ENTER_SCORES)

    current_term = await _current_term(school_id, session)
    admin_stats = await _admin_stats(school_id, session) if is_admin else None

    my_classes = None
    role = "staff"

    if is_admin:
        role = "admin"
    elif is_teacher and user.staff_member_id:
        classes, is_class_teacher = await _my_classes(user.staff_member_id, school_id, session)
        my_classes = classes
        role = "class_teacher" if is_class_teacher else "subject_teacher"

    return DashboardSummary(
        role=role,
        current_term=current_term,
        admin=admin_stats,
        my_classes=my_classes,
    )
