from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import CurrentUser, RedisDep, SessionDep
from app.core.permissions import Permission
from app.models.academic import AcademicTerm, AcademicYear, Class, ClassTeacher
from app.models.staff import StaffMember
from app.models.student import Student
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


class MyClass(BaseModel):
    id: str
    name: str
    education_level: str
    level: str
    year: int | None
    stream: str | None


class DashboardSummary(BaseModel):
    role: str                           # admin | teacher | staff | student | parent
    current_term: TermSummary | None
    admin: AdminStats | None            # only for admin role
    my_classes: list[MyClass] | None    # only for teacher role


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

    return AdminStats(
        staff_total=staff_total,
        staff_no_account=staff_no_account,
        classes_total=classes_total,
        classes_no_teacher=classes_no_teacher,
        students_total=students_total,
    )


async def _my_classes(staff_member_id: UUID, school_id: UUID, session) -> list[MyClass]:
    current_year = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    )
    if not current_year:
        return []

    rows = await session.execute(
        select(Class)
        .join(ClassTeacher, ClassTeacher.class_id == Class.id)
        .where(
            ClassTeacher.staff_member_id == staff_member_id,
            ClassTeacher.academic_year_id == current_year.id,
            Class.is_active.is_(True),
        )
        .order_by(Class.level, Class.year, Class.stream)
    )
    return [
        MyClass(
            id=str(c.id),
            name=c.name,
            education_level=c.education_level,
            level=c.level,
            year=c.year,
            stream=c.stream,
        )
        for c in rows.scalars()
    ]


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

    role = "admin" if is_admin else "teacher" if is_teacher else "staff"

    current_term = await _current_term(school_id, session)
    admin_stats = await _admin_stats(school_id, session) if is_admin else None
    my_classes = (
        await _my_classes(user.staff_member_id, school_id, session)
        if is_teacher and user.staff_member_id
        else None
    )

    return DashboardSummary(
        role=role,
        current_term=current_term,
        admin=admin_stats,
        my_classes=my_classes,
    )
