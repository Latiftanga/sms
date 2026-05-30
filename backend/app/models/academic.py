import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey,
    Integer, String, Text, Time, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.attendance import AttendanceRecord


class AcademicYear(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "academic_year"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_academic_year_school_name"),)

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "2024/2025"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    school: Mapped["School"] = relationship(back_populates="academic_years")
    terms: Mapped[list["AcademicTerm"]] = relationship(
        back_populates="academic_year", order_by="AcademicTerm.start_date"
    )


class AcademicTerm(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "academic_term"
    __table_args__ = (UniqueConstraint("academic_year_id", "name", name="uq_academic_term_year_name"),)

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_year.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # "Term 1"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    education_levels: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Fee gate — off by default; admin-toggled per term
    block_owing_students: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    block_owing_students_set_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    block_owing_students_set_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    academic_year: Mapped["AcademicYear"] = relationship(back_populates="terms")
    calendar_entries: Mapped[list["SchoolCalendar"]] = relationship(
        back_populates="academic_term", order_by="SchoolCalendar.date"
    )


class SchoolCalendar(UUIDPrimaryKey, Base):
    """
    One row per date per school per term.
    Auto-generated on term creation from SchoolSchedule + GhanaPublicHoliday.
    Admin can edit individual rows (rain closures, make-up Saturdays).

    Attendance is gated to rows where day_type = 'SCHOOL_DAY'.
    """

    __tablename__ = "school_calendar"
    __table_args__ = (UniqueConstraint("school_id", "academic_term_id", "date"),)

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    academic_term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_term.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    # SCHOOL_DAY | HOLIDAY | CLOSURE | WEEKEND
    day_type: Mapped[str] = mapped_column(String(20), nullable=False)
    label: Mapped[str | None] = mapped_column(String(120))  # "Independence Day", "Closed – rain"
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )

    academic_term: Mapped["AcademicTerm"] = relationship(back_populates="calendar_entries")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="school_calendar"
    )


class SchoolPeriod(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Defines the daily timetable slots.
    Exists now as the FK anchor for AttendanceRecord.school_period_id (nullable).
    NULL school_period_id = daily attendance (Phase 5).
    Populated school_period_id = per-lesson attendance (future phase).
    Zero schema migration needed when per-lesson feature is built.
    """

    __tablename__ = "school_period"
    __table_args__ = (UniqueConstraint("school_id", "position"),)

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # "Period 1", "Break"
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # sort order
    is_lesson: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class LearningArea(UUIDPrimaryKey, TimestampMixin, Base):
    """
    SHS-only. Each school defines its own learning areas (GES programmes)
    and chooses a short_name/code for display in class names.
    e.g. name="General Arts", short_name="ART" → class display "2 ART A"
    Only exists when school.education_levels includes 'SHS'.
    """

    __tablename__ = "learning_area"
    __table_args__ = (UniqueConstraint("school_id", "name"),)

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    classes: Mapped[list["Class"]] = relationship(back_populates="learning_area")


class House(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "house"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(20))
    housemaster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_member.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Class(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Permanent class object — created once, referenced across academic years.
    Name is derived from level + year + learning_area + stream.

    Basic schools:  level ∈ {Creche, Nursery, KG, Basic}
    SHS:            level = SHS, learning_area required
    Name examples:  "Basic 4A", "KG 1 Gold", "Creche", "2 ART A"
    """

    __tablename__ = "class"
    __table_args__ = (
        # Prevents duplicate classes within a school.
        # Note: PostgreSQL treats NULLs as distinct in unique constraints, so the
        # API layer also checks for duplicates to cover NULL column combinations.
        UniqueConstraint(
            "school_id", "level", "year", "learning_area_id", "stream",
            name="uq_class_identity",
        ),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    # EARLY_CHILDHOOD | BASIC | SHS | TECHNICAL  (for filtering/grouping)
    education_level: Mapped[str] = mapped_column(String(30), nullable=False)
    # "Creche" | "Nursery" | "KG" | "Basic" | "SHS"
    level: Mapped[str] = mapped_column(String(30), nullable=False)
    # None only for Creche; 1-2 for Nursery/KG; 1-9 for Basic; 1-3 for SHS
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # SHS only — FK to LearningArea
    learning_area_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_area.id", ondelete="RESTRICT"), nullable=True
    )
    # Free-text: "A", "B", "Gold", "Green" — any string the school uses
    stream: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    learning_area: Mapped["LearningArea | None"] = relationship(back_populates="classes")
    subjects: Mapped[list["ClassSubject"]] = relationship(back_populates="class_")
    enrollments: Mapped[list["StudentClassEnrollment"]] = relationship(back_populates="class_")  # type: ignore[name-defined]

    @property
    def name(self) -> str:
        """Derive display name from stored components."""
        if self.level == "Creche":
            base = "Creche"
        else:
            base = f"{self.level} {self.year}"

        if self.learning_area:
            label = self.learning_area.short_name or self.learning_area.name
            # SHS: drop level prefix — "2 ART A" not "SHS 2 ART A"
            base = f"{self.year} {label}" if self.level == "SHS" else f"{base} {label}"

        if self.stream:
            # single char → no space ("KG 1A"); word → space ("KG 1 Gold")
            sep = "" if len(self.stream) == 1 else " "
            base = f"{base}{sep}{self.stream}"

        return base


class SchoolSubject(UUIDPrimaryKey, TimestampMixin, Base):
    """
    School-wide subject catalogue. Admin defines subjects here first;
    classes then assign from this list.
    """
    __tablename__ = "school_subject"
    __table_args__ = (UniqueConstraint("school_id", "name"),)

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ClassSubject(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "class_subject"
    __table_args__ = (UniqueConstraint("class_id", "subject_code"),)

    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class.id", ondelete="CASCADE"), nullable=False
    )
    subject_name: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_code: Mapped[str] = mapped_column(String(20), nullable=False)
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    class_: Mapped["Class"] = relationship(back_populates="subjects")
    subject_teachers: Mapped[list["SubjectTeacher"]] = relationship(back_populates="class_subject")


class ClassTeacher(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "class_teacher"
    __table_args__ = (UniqueConstraint("class_id", "academic_year_id"),)

    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class.id", ondelete="CASCADE"), nullable=False
    )
    staff_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_member.id", ondelete="RESTRICT"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_year.id", ondelete="CASCADE"), nullable=False
    )


class SubjectTeacher(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Gates score entry: a teacher can only enter scores for (subject, class) pairs
    where a SubjectTeacher record exists for the current academic year.
    """

    __tablename__ = "subject_teacher"
    __table_args__ = (UniqueConstraint("class_subject_id", "staff_member_id", "academic_year_id"),)

    class_subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_subject.id", ondelete="CASCADE"), nullable=False
    )
    staff_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_member.id", ondelete="RESTRICT"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_year.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    class_subject: Mapped["ClassSubject"] = relationship(back_populates="subject_teachers")


# Import here to avoid circular reference at module level
from app.models.student import StudentClassEnrollment  # noqa: E402
