import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.student import StudentTermEnrollment
    from app.models.academic import SchoolCalendar, SchoolPeriod


class AttendanceRecord(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Attendance is anchored to SchoolCalendar (not raw date), making it
    structurally impossible to mark attendance on a holiday or closure.

    school_period_id = NULL  → daily attendance (Phase 5 current behaviour).
    school_period_id = set   → per-lesson attendance (future phase, zero migration).

    Attendance % formula:
        present / COUNT(SchoolCalendar WHERE day_type='SCHOOL_DAY' AND period IS NULL)
    """

    __tablename__ = "attendance_record"
    __table_args__ = (
        UniqueConstraint("student_term_enrollment_id", "school_calendar_id", "school_period_id"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_term_enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_term_enrollment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # FK enforces attendance is only on valid calendar rows;
    # API layer additionally checks day_type = 'SCHOOL_DAY'
    school_calendar_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_calendar.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # NULL = daily; populated = per-lesson (future)
    school_period_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("school_period.id", ondelete="RESTRICT"),
        nullable=True,
    )
    # PRESENT | ABSENT | LATE | EXCUSED
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    marked_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    marked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    term_enrollment: Mapped["StudentTermEnrollment"] = relationship(
        back_populates="attendance_records"
    )
    school_calendar: Mapped["SchoolCalendar"] = relationship(
        back_populates="attendance_records"
    )
