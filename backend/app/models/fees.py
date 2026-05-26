import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey,
    Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class FeeStructure(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Defines an amount owed.
    class_id = NULL → applies to all classes.
    student_type = NULL → applies to both DAY and BOARDING.
    academic_term_id = NULL → applies to all terms in the year.

    Balance is NEVER stored — always computed:
        balance = SUM(applicable fee_structures) - SUM(payments)
    """

    __tablename__ = "fee_structure"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_year.id", ondelete="CASCADE"), nullable=False
    )
    academic_term_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_term.id", ondelete="CASCADE"), nullable=True
    )
    class_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class.id", ondelete="SET NULL"), nullable=True
    )
    # DAY | BOARDING | NULL (both)
    student_type: Mapped[str | None] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(150), nullable=False)  # "Tuition Fee", "Feeding"
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GHS")
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )

    payments: Mapped[list["FeePayment"]] = relationship(back_populates="fee_structure")


class FeePayment(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Records a single payment event. Partial payments are allowed.
    After every insert, balance is recomputed and StudentTermEnrollment.fee_status updated.
    """

    __tablename__ = "fee_payment"
    __table_args__ = (UniqueConstraint("receipt_number"),)

    student_class_enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_class_enrollment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_term.id", ondelete="RESTRICT"), nullable=False
    )
    fee_structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_structure.id", ondelete="RESTRICT"), nullable=False
    )
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GHS")
    # CASH | MOBILE_MONEY | BANK | CHEQUE
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))  # cheque no., MoMo transaction
    note: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )

    fee_structure: Mapped["FeeStructure"] = relationship(back_populates="payments")
