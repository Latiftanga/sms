import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.academic import Class, AcademicYear, AcademicTerm, House
    from app.models.attendance import AttendanceRecord
    from app.models.assessment import Score, StudentSubjectRegistration


class Student(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "student"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)  # MALE | FEMALE
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    place_of_birth: Mapped[str | None] = mapped_column(String(150))
    nationality: Mapped[str] = mapped_column(String(60), nullable=False, default="Ghanaian")
    religion: Mapped[str | None] = mapped_column(String(60))

    # Set by school during admission; unique per school
    school_issued_id: Mapped[str | None] = mapped_column(String(50), index=True)

    photo_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Admission
    admission_date: Mapped[date | None] = mapped_column(Date)
    admission_number: Mapped[str | None] = mapped_column(String(50))
    previous_school: Mapped[str | None] = mapped_column(String(200))

    class_enrollments: Mapped[list["StudentClassEnrollment"]] = relationship(
        back_populates="student"
    )
    guardians: Mapped[list["Guardian"]] = relationship(back_populates="student")

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p)


class Guardian(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "guardian"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student.id", ondelete="CASCADE"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(30), nullable=False)  # FATHER|MOTHER|GUARDIAN
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(120))
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Linked User account (for parent portal)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )

    student: Mapped["Student"] = relationship(back_populates="guardians")


class StudentClassEnrollment(UUIDPrimaryKey, TimestampMixin, Base):
    """Year-level placement: student → class → academic_year."""

    __tablename__ = "student_class_enrollment"
    __table_args__ = (UniqueConstraint("student_id", "academic_year_id"),)

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student.id", ondelete="CASCADE"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class.id", ondelete="RESTRICT"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_year.id", ondelete="RESTRICT"), nullable=False
    )
    house_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("house.id", ondelete="SET NULL"), nullable=True
    )
    # DAY | BOARDING
    student_type: Mapped[str] = mapped_column(String(10), nullable=False, default="DAY")
    register_number: Mapped[str | None] = mapped_column(String(50), index=True)

    # Transfer / dropout tracking
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    left_date: Mapped[date | None] = mapped_column(Date)
    left_reason: Mapped[str | None] = mapped_column(Text)

    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_batch.id", ondelete="SET NULL"), nullable=True
    )

    student: Mapped["Student"] = relationship(back_populates="class_enrollments")
    class_: Mapped["Class"] = relationship(back_populates="enrollments")
    term_enrollments: Mapped[list["StudentTermEnrollment"]] = relationship(
        back_populates="class_enrollment"
    )


class StudentTermEnrollment(UUIDPrimaryKey, TimestampMixin, Base):
    """Per-term record. fee_status gates attendance + score capture when block_owing_students=True."""

    __tablename__ = "student_term_enrollment"
    __table_args__ = (UniqueConstraint("student_class_enrollment_id", "academic_term_id"),)

    student_class_enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_class_enrollment.id", ondelete="CASCADE"),
        nullable=False,
    )
    academic_term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_term.id", ondelete="RESTRICT"), nullable=False
    )
    # Attendance slots only valid from this date onward
    enrolled_date: Mapped[date] = mapped_column(Date, nullable=False)

    # CLEARED | FEE_PENDING | WAIVED | NOT_APPLICABLE
    fee_status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOT_APPLICABLE")
    fee_cleared_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    fee_cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    waiver_reason: Mapped[str | None] = mapped_column(String(500))

    class_enrollment: Mapped["StudentClassEnrollment"] = relationship(
        back_populates="term_enrollments"
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="term_enrollment"
    )
    subject_registrations: Mapped[list["StudentSubjectRegistration"]] = relationship(
        back_populates="term_enrollment"
    )
    behaviour_records: Mapped[list["StudentBehaviourRecord"]] = relationship(
        back_populates="term_enrollment"
    )


class StudentBehaviourRecord(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "student_behaviour_record"

    student_term_enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_term_enrollment.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 1–5 scale or text depending on school config
    conduct: Mapped[str | None] = mapped_column(String(20))
    attitude: Mapped[str | None] = mapped_column(String(20))
    punctuality: Mapped[str | None] = mapped_column(String(20))
    interest: Mapped[str | None] = mapped_column(String(20))
    class_teacher_remark: Mapped[str | None] = mapped_column(Text)
    head_teacher_remark: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )

    term_enrollment: Mapped["StudentTermEnrollment"] = relationship(back_populates="behaviour_records")
