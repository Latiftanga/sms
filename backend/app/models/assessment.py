import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, DateTime, ForeignKey,
    Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.student import StudentTermEnrollment
    from app.models.academic import ClassSubject


class StudentSubjectRegistration(UUIDPrimaryKey, TimestampMixin, Base):
    """Links a student-term to a specific subject they are studying."""

    __tablename__ = "student_subject_registration"
    __table_args__ = (UniqueConstraint("student_term_enrollment_id", "class_subject_id"),)

    student_term_enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_term_enrollment.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_subject.id", ondelete="RESTRICT"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    term_enrollment: Mapped["StudentTermEnrollment"] = relationship(
        back_populates="subject_registrations"
    )
    class_subject: Mapped["ClassSubject"] = relationship()
    scores: Mapped[list["Score"]] = relationship(
        back_populates="registration",
        primaryjoin="Score.student_subject_registration_id == StudentSubjectRegistration.id",
    )


class Score(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Immutable. No UPDATE ever.
    Corrections create a new row with supersedes_id pointing to the corrected row.
    Grade is NEVER stored here — always resolved at query time from the active GradingScale.
    """

    __tablename__ = "score"

    student_subject_registration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_subject_registration.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # exercise | homework | test | exam | project | practical
    assessment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    assessment_label: Mapped[str | None] = mapped_column(String(80))  # "Mid-term Exam", "Class Test 1"
    raw_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)

    entered_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Correction chain — superseded row is the one being replaced
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("score.id", ondelete="RESTRICT"), nullable=True
    )

    # Approval workflow
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Import audit
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_batch.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text)

    registration: Mapped["StudentSubjectRegistration"] = relationship(
        back_populates="scores",
        foreign_keys=[student_subject_registration_id],
    )

    @property
    def percentage(self) -> float:
        if self.max_score == 0:
            return 0.0
        return round(float(self.raw_score) / float(self.max_score) * 100, 2)
