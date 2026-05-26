import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, ForeignKey, Integer,
    Numeric, String, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class GradingScale(UUIDPrimaryKey, TimestampMixin, Base):
    """
    school_id = NULL → system default (seeded, permanently read-only).
    school_id = set  → custom school scale.

    Grades are resolved at query time — never stored on Score.
    """

    __tablename__ = "grading_scale"

    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    education_levels: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # True for ECM milestone scales — no numeric ranges, text descriptors only
    is_observational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    grades: Mapped[list["Grade"]] = relationship(
        back_populates="grading_scale",
        order_by="Grade.position",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<GradingScale {self.code}>"


class Grade(UUIDPrimaryKey, Base):
    """
    A single grade band within a GradingScale.
    min_score / max_score are null for observational (ECM) scales.
    Ranges must cover 0–100 completely with no overlaps (validated on save).
    """

    __tablename__ = "grade"
    __table_args__ = (UniqueConstraint("grading_scale_id", "label"),)

    grading_scale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grading_scale.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(10), nullable=False)  # "A1", "B2", "1", "Excellent"
    min_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    max_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    remark: Mapped[str | None] = mapped_column(String(60))          # "Excellent", "Credit"
    points: Mapped[float | None] = mapped_column(Numeric(4, 1))     # WASSCE aggregate points
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 = best
    is_pass: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    grading_scale: Mapped["GradingScale"] = relationship(back_populates="grades")
