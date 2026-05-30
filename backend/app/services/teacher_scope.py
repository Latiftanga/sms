"""
Teacher data-scoping service.

Admin-level users (SUPERADMIN, anyone with enroll_students) see all data.
Teaching staff are scoped to the classes/subjects they are assigned to.

Resolution rules
────────────────
SUPERADMIN                       → unrestricted
has enroll_students permission   → unrestricted  (headteacher, admin)
otherwise (CLASS_TEACHER, etc.)  → scoped to:
    • classes where they are the designated class teacher this year
    • classes where they are an active subject teacher this year

Usage in an endpoint
────────────────────
    scope = await TeacherScope.build(user, redis, session)

    if scope.is_restricted:
        if not scope.class_ids:
            return []   # no assignments → no data
        # filter query with: .where(SomeModel.class_id.in_(scope.class_ids))

    # scope.is_restricted is False → run query without extra filtering
"""
from dataclasses import dataclass, field
from uuid import UUID

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import (
    AcademicYear,
    ClassSubject,
    ClassTeacher,
    SubjectTeacher,
)
from app.models.user import User


# ── Current academic year ─────────────────────────────────────────────────────

async def get_current_year(school_id: UUID, session: AsyncSession) -> AcademicYear | None:
    return await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    )


async def require_current_year(school_id: UUID, session: AsyncSession) -> AcademicYear:
    year = await get_current_year(school_id, session)
    if not year:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No active academic year — set one in Settings before recording data.",
        )
    return year


# ── Assignment look-ups ───────────────────────────────────────────────────────

async def get_accessible_class_ids(
    staff_member_id: UUID,
    academic_year_id: UUID,
    session: AsyncSession,
) -> set[UUID]:
    """
    Classes this teacher is responsible for this year:
      • designated class teacher, OR
      • active subject teacher for at least one subject in that class.
    """
    # Designated class teacher
    ct_rows = await session.scalars(
        select(ClassTeacher.class_id).where(
            ClassTeacher.staff_member_id == staff_member_id,
            ClassTeacher.academic_year_id == academic_year_id,
        )
    )
    class_ids: set[UUID] = set(ct_rows.all())

    # Subject teacher → resolve class_id through ClassSubject
    st_rows = await session.execute(
        select(ClassSubject.class_id)
        .join(SubjectTeacher, SubjectTeacher.class_subject_id == ClassSubject.id)
        .where(
            SubjectTeacher.staff_member_id == staff_member_id,
            SubjectTeacher.academic_year_id == academic_year_id,
            SubjectTeacher.is_active.is_(True),
        )
    )
    class_ids.update(row[0] for row in st_rows)
    return class_ids


async def is_class_teacher_of(
    staff_member_id: UUID,
    class_id: UUID,
    academic_year_id: UUID,
    session: AsyncSession,
) -> bool:
    """True if this staff member is the designated class teacher for the class this year."""
    row = await session.scalar(
        select(ClassTeacher.id).where(
            ClassTeacher.staff_member_id == staff_member_id,
            ClassTeacher.class_id == class_id,
            ClassTeacher.academic_year_id == academic_year_id,
        )
    )
    return row is not None


async def is_subject_teacher_of(
    staff_member_id: UUID,
    class_subject_id: UUID,
    academic_year_id: UUID,
    session: AsyncSession,
) -> bool:
    """True if this staff member is assigned to teach this subject this year."""
    row = await session.scalar(
        select(SubjectTeacher.id).where(
            SubjectTeacher.staff_member_id == staff_member_id,
            SubjectTeacher.class_subject_id == class_subject_id,
            SubjectTeacher.academic_year_id == academic_year_id,
            SubjectTeacher.is_active.is_(True),
        )
    )
    return row is not None


# ── Scope object ──────────────────────────────────────────────────────────────

@dataclass
class TeacherScope:
    """
    Holds the result of a scope resolution for the current request.

    is_restricted = False  →  user sees all data (admin-level access)
    is_restricted = True   →  filter queries to class_ids only
                              (empty set = no assignments = no data)
    """
    is_restricted: bool
    class_ids: set[UUID] = field(default_factory=set)

    @classmethod
    async def build(
        cls,
        user: User,
        redis: Redis,
        session: AsyncSession,
    ) -> "TeacherScope":
        if user.system_role == "SUPERADMIN":
            return cls(is_restricted=False)

        from app.services.permissions import resolve_all_permissions
        perms = await resolve_all_permissions(user, redis, session)

        # Users who can enroll students are admin-level — unrestricted view
        if perms.get("enroll_students"):
            return cls(is_restricted=False)

        # Teaching staff — scoped to their assignments this year
        if not user.staff_member_id:
            return cls(is_restricted=True, class_ids=set())

        year = await get_current_year(user.school_id, session)
        if not year:
            return cls(is_restricted=True, class_ids=set())

        class_ids = await get_accessible_class_ids(
            user.staff_member_id, year.id, session
        )
        return cls(is_restricted=True, class_ids=class_ids)
