"""
Attendance API — daily class register.

Endpoints:
  GET  /attendance/register   — fetch register for a class on a date
  POST /attendance/register   — submit/update the register (upsert)
  GET  /attendance/summary    — per-student summary for a term
  GET  /attendance/classes    — classes available to mark for the current user
"""
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, RedisDep, SessionDep, require
from app.core.permissions import Permission
from app.services.permissions import resolve_all_permissions
from app.models.academic import (
    AcademicTerm, AcademicYear, Class, ClassTeacher, SchoolCalendar,
)
from app.models.attendance import AttendanceRecord
from app.models.student import Student, StudentClassEnrollment, StudentTermEnrollment
from app.schemas.common import OrmBase

router = APIRouter(prefix="/attendance", tags=["attendance"])


# ── Response models ───────────────────────────────────────────────────────────

class CalendarDayInfo(OrmBase):
    id: UUID
    date: str
    day_type: str
    label: str | None


class RegisterStudent(OrmBase):
    student_id: UUID
    full_name: str
    register_number: str | None
    gender: str
    term_enrollment_id: UUID
    status: str | None        # PRESENT | ABSENT | LATE | EXCUSED | None (not marked)
    note: str | None


class RegisterResponse(OrmBase):
    calendar: CalendarDayInfo
    class_id: UUID
    class_name: str
    records: list[RegisterStudent]
    is_submitted: bool        # True if at least one record exists for this day


class MarkRequest(OrmBase):
    class_id: UUID
    date: str                 # YYYY-MM-DD
    records: list["MarkEntry"]


class MarkEntry(OrmBase):
    term_enrollment_id: UUID
    status: str               # PRESENT | ABSENT | LATE | EXCUSED
    note: str | None = None


class MarkResponse(OrmBase):
    date: str
    class_id: UUID
    marked: int


class SummaryStudent(OrmBase):
    student_id: UUID
    full_name: str
    register_number: str | None
    total_school_days: int
    present: int
    absent: int
    late: int
    excused: int
    percentage: float


class ClassSummary(OrmBase):
    class_id: UUID
    class_name: str
    term_id: UUID
    term_name: str
    total_school_days: int
    students: list[SummaryStudent]


class AttendableClass(OrmBase):
    class_id: UUID
    class_name: str
    education_level: str
    today_submitted: bool


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _current_term(school_id: UUID, session) -> AcademicTerm:
    term = await session.scalar(
        select(AcademicTerm)
        .join(AcademicYear, AcademicTerm.academic_year_id == AcademicYear.id)
        .where(AcademicYear.school_id == school_id, AcademicTerm.is_current.is_(True))
    )
    if not term:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "No active term. Activate a term in Settings → Academic Years.",
        )
    return term


async def _calendar_entry(
    school_id: UUID, target_date: date, session
) -> SchoolCalendar:
    entry = await session.scalar(
        select(SchoolCalendar)
        .join(AcademicTerm, SchoolCalendar.academic_term_id == AcademicTerm.id)
        .join(AcademicYear, AcademicTerm.academic_year_id == AcademicYear.id)
        .where(
            SchoolCalendar.school_id == school_id,
            SchoolCalendar.date == target_date,
            AcademicYear.school_id == school_id,
        )
        .limit(1)
    )
    if not entry:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"{target_date} has no calendar entry. Ensure a term covers this date and the calendar has been generated.",
        )
    if entry.day_type != "SCHOOL_DAY":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"{target_date} is a {entry.day_type.lower().replace('_', ' ')}"
            + (f" ({entry.label})" if entry.label else "") + " — attendance cannot be marked.",
        )
    return entry


async def _get_class(class_id: UUID, school_id: UUID, session) -> Class:
    cls = await session.scalar(
        select(Class)
        .options(selectinload(Class.learning_area))
        .where(Class.id == class_id, Class.school_id == school_id, Class.is_active.is_(True))
    )
    if not cls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
    return cls


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/classes", response_model=list[AttendableClass],
            dependencies=[require(Permission.MARK_ATTENDANCE)])
async def my_classes(user: CurrentUser, redis: RedisDep, session: SessionDep):
    """
    Classes this user can mark attendance for today.
    Admins/headteachers see all classes; class teachers see only their assigned classes.
    """
    school_id = user.school_id
    today = date.today()

    current_year = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    )
    if not current_year:
        return []

    # Admins and headteachers see all classes; class teachers see only theirs
    perms = await resolve_all_permissions(user, redis, session)
    can_view_all = perms.get(Permission.MANAGE_STAFF) or perms.get(Permission.MANAGE_SCHOOL_CONFIG)

    if can_view_all:
        class_ids_query = (
            select(Class.id).where(Class.school_id == school_id, Class.is_active.is_(True))
        )
    else:
        class_ids_query = (
            select(ClassTeacher.class_id)
            .where(
                ClassTeacher.staff_member_id == user.staff_member_id,
                ClassTeacher.academic_year_id == current_year.id,
            )
        )

    class_rows = await session.execute(
        select(Class)
        .options(selectinload(Class.learning_area))
        .where(Class.id.in_(class_ids_query), Class.is_active.is_(True))
        .order_by(Class.level, Class.year, Class.stream)
    )
    classes = list(class_rows.scalars())

    # Check which classes have attendance submitted today
    today_calendar = await session.scalar(
        select(SchoolCalendar).where(
            SchoolCalendar.school_id == school_id,
            SchoolCalendar.date == today,
        )
    )

    submitted_class_ids: set[UUID] = set()
    if today_calendar and today_calendar.day_type == "SCHOOL_DAY":
        # A class is "submitted" if any attendance record exists for it today
        for cls in classes:
            count = await session.scalar(
                select(func.count(AttendanceRecord.id))
                .join(
                    StudentTermEnrollment,
                    AttendanceRecord.student_term_enrollment_id == StudentTermEnrollment.id,
                )
                .join(
                    StudentClassEnrollment,
                    StudentTermEnrollment.student_class_enrollment_id == StudentClassEnrollment.id,
                )
                .where(
                    StudentClassEnrollment.class_id == cls.id,
                    AttendanceRecord.school_calendar_id == today_calendar.id,
                )
            )
            if count:
                submitted_class_ids.add(cls.id)

    return [
        AttendableClass(
            class_id=cls.id,
            class_name=cls.name,
            education_level=cls.education_level,
            today_submitted=cls.id in submitted_class_ids,
        )
        for cls in classes
    ]


@router.get("/register", response_model=RegisterResponse,
            dependencies=[require(Permission.MARK_ATTENDANCE)])
async def get_register(
    class_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    target_date: str | None = None,
):
    """Get the attendance register for a class on a given date (default: today)."""
    school_id = user.school_id
    d = date.fromisoformat(target_date) if target_date else date.today()

    cal = await _calendar_entry(school_id, d, session)
    cls = await _get_class(class_id, school_id, session)
    term = await _current_term(school_id, session)

    # Get all active students in this class for the current year, with term enrollments
    rows = await session.execute(
        select(Student, StudentClassEnrollment, StudentTermEnrollment)
        .join(StudentClassEnrollment, StudentClassEnrollment.student_id == Student.id)
        .join(
            StudentTermEnrollment,
            and_(
                StudentTermEnrollment.student_class_enrollment_id == StudentClassEnrollment.id,
                StudentTermEnrollment.academic_term_id == term.id,
            ),
        )
        .join(AcademicYear, AcademicYear.id == StudentClassEnrollment.academic_year_id)
        .where(
            Student.school_id == school_id,
            Student.is_active.is_(True),
            StudentClassEnrollment.class_id == class_id,
            StudentClassEnrollment.status == "ACTIVE",
            AcademicYear.is_current.is_(True),
        )
        .order_by(Student.last_name, Student.first_name)
    )
    student_rows = rows.all()

    # Fetch existing attendance records for this calendar day
    term_enrollment_ids = [r[2].id for r in student_rows]
    existing: dict[UUID, AttendanceRecord] = {}
    if term_enrollment_ids:
        att_rows = await session.scalars(
            select(AttendanceRecord).where(
                AttendanceRecord.school_calendar_id == cal.id,
                AttendanceRecord.student_term_enrollment_id.in_(term_enrollment_ids),
                AttendanceRecord.school_period_id.is_(None),
            )
        )
        for att in att_rows:
            existing[att.student_term_enrollment_id] = att

    register = [
        RegisterStudent(
            student_id=s.id,
            full_name=s.full_name,
            register_number=sce.register_number,
            gender=s.gender,
            term_enrollment_id=ste.id,
            status=existing[ste.id].status if ste.id in existing else None,
            note=existing[ste.id].note if ste.id in existing else None,
        )
        for s, sce, ste in student_rows
    ]

    return RegisterResponse(
        calendar=CalendarDayInfo(
            id=cal.id,
            date=cal.date.isoformat(),
            day_type=cal.day_type,
            label=cal.label,
        ),
        class_id=cls.id,
        class_name=cls.name,
        records=register,
        is_submitted=bool(existing),
    )


@router.post("/register", response_model=MarkResponse,
             dependencies=[require(Permission.MARK_ATTENDANCE)])
async def submit_register(
    body: MarkRequest,
    user: CurrentUser,
    session: SessionDep,
):
    """Submit (or update) attendance for a class on a given date."""
    school_id = user.school_id
    target_date = date.fromisoformat(body.date)

    cal = await _calendar_entry(school_id, target_date, session)
    await _get_class(body.class_id, school_id, session)

    now = datetime.now(timezone.utc)
    marked = 0

    for entry in body.records:
        valid = {"PRESENT", "ABSENT", "LATE", "EXCUSED"}
        if entry.status not in valid:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Invalid status '{entry.status}'. Must be one of {valid}",
            )

        # Upsert: update if exists, insert if not
        existing = await session.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.school_calendar_id == cal.id,
                AttendanceRecord.student_term_enrollment_id == entry.term_enrollment_id,
                AttendanceRecord.school_period_id.is_(None),
            )
        )
        if existing:
            existing.status = entry.status
            existing.note = entry.note
            existing.marked_by = user.id
            existing.marked_at = now
        else:
            session.add(AttendanceRecord(
                school_id=school_id,
                student_term_enrollment_id=entry.term_enrollment_id,
                school_calendar_id=cal.id,
                school_period_id=None,
                status=entry.status,
                marked_by=user.id,
                marked_at=now,
                note=entry.note,
            ))
        marked += 1

    await session.commit()
    return MarkResponse(date=body.date, class_id=body.class_id, marked=marked)


@router.get("/summary", response_model=ClassSummary,
            dependencies=[require(Permission.VIEW_ATTENDANCE)])
async def attendance_summary(
    class_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    term_id: UUID | None = None,
):
    """Per-student attendance summary for a class in a term."""
    school_id = user.school_id

    if term_id:
        term = await session.get(AcademicTerm, term_id)
        if not term:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Term not found")
    else:
        term = await _current_term(school_id, session)

    cls = await _get_class(class_id, school_id, session)

    # Count total school days in the term
    total_days = await session.scalar(
        select(func.count(SchoolCalendar.id)).where(
            SchoolCalendar.school_id == school_id,
            SchoolCalendar.academic_term_id == term.id,
            SchoolCalendar.day_type == "SCHOOL_DAY",
        )
    ) or 0

    # Get students in this class for the term
    rows = await session.execute(
        select(Student, StudentClassEnrollment, StudentTermEnrollment)
        .join(StudentClassEnrollment, StudentClassEnrollment.student_id == Student.id)
        .join(
            StudentTermEnrollment,
            and_(
                StudentTermEnrollment.student_class_enrollment_id == StudentClassEnrollment.id,
                StudentTermEnrollment.academic_term_id == term.id,
            ),
        )
        .join(AcademicYear, AcademicYear.id == StudentClassEnrollment.academic_year_id)
        .where(
            Student.school_id == school_id,
            Student.is_active.is_(True),
            StudentClassEnrollment.class_id == class_id,
            StudentClassEnrollment.status == "ACTIVE",
            AcademicYear.is_current.is_(True),
        )
        .order_by(Student.last_name, Student.first_name)
    )
    student_rows = rows.all()

    students = []
    for s, sce, ste in student_rows:
        counts = await session.execute(
            select(AttendanceRecord.status, func.count(AttendanceRecord.id))
            .where(
                AttendanceRecord.student_term_enrollment_id == ste.id,
                AttendanceRecord.school_period_id.is_(None),
            )
            .group_by(AttendanceRecord.status)
        )
        count_map: dict[str, int] = {row[0]: row[1] for row in counts}
        present  = count_map.get("PRESENT", 0)
        absent   = count_map.get("ABSENT", 0)
        late     = count_map.get("LATE", 0)
        excused  = count_map.get("EXCUSED", 0)
        pct = round((present + late) / total_days * 100, 1) if total_days > 0 else 0.0

        students.append(SummaryStudent(
            student_id=s.id,
            full_name=s.full_name,
            register_number=sce.register_number,
            total_school_days=total_days,
            present=present,
            absent=absent,
            late=late,
            excused=excused,
            percentage=pct,
        ))

    return ClassSummary(
        class_id=cls.id,
        class_name=cls.name,
        term_id=term.id,
        term_name=term.name,
        total_school_days=total_days,
        students=students,
    )
