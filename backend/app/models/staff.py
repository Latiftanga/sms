import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey,
    Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.school import School


class StaffPosition(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Position template that defines a default permission set.
    school_id = NULL → system template (seeded, renameable, not deleteable).
    school_id = set  → school-custom position.
    """

    __tablename__ = "staff_position"
    __table_args__ = (
        UniqueConstraint("school_id", "code"),
        Index("ix_staff_position_school_id", "school_id"),
    )

    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    is_system_template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )

    school: Mapped["School | None"] = relationship(back_populates="positions")
    permissions: Mapped[list["PositionPermission"]] = relationship(
        back_populates="position", cascade="all, delete-orphan"
    )


class PositionPermission(Base):
    """Default permission set for a StaffPosition."""

    __tablename__ = "position_permission"
    __table_args__ = (UniqueConstraint("position_id", "permission_key"),)

    position_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff_position.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_key: Mapped[str] = mapped_column(String(60), primary_key=True)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    position: Mapped["StaffPosition"] = relationship(back_populates="permissions")


class StaffPermission(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Personal override — beats PositionPermission in the resolution chain.
    granted=True = explicitly ON; granted=False = explicitly OFF (block inherited grant).
    """

    __tablename__ = "staff_permission"
    __table_args__ = (
        UniqueConstraint("staff_member_id", "school_id", "permission_key"),
        Index("ix_staff_permission_member", "staff_member_id"),
    )

    staff_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    permission_key: Mapped[str] = mapped_column(String(60), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    granted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500))

    staff_member: Mapped["StaffMember"] = relationship(back_populates="permission_overrides")


class StaffMember(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "staff_member"
    __table_args__ = (
        Index("ix_staff_member_school_id", "school_id"),
        # Covers ORDER BY last_name, first_name scoped to school (list endpoint)
        Index("ix_staff_member_school_name", "school_id", "last_name", "first_name"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    # School-assigned staff ID (printed on ID cards etc.)
    staff_id: Mapped[str | None] = mapped_column(String(30), index=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)

    # Personal details
    gender: Mapped[str | None] = mapped_column(String(10))  # MALE | FEMALE | OTHER
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(20))
    personal_email: Mapped[str | None] = mapped_column(String(254))
    address: Mapped[str | None] = mapped_column(String(300))

    # Emergency contact
    emergency_contact_name: Mapped[str | None] = mapped_column(String(160))
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(20))

    # TEACHING | NON-TEACHING
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    # PERMANENT | CONTRACT | VOLUNTEER | GES_POSTED
    employment_type: Mapped[str] = mapped_column(String(20), nullable=False, default="PERMANENT")
    # TEACHER | HEADTEACHER | ASSISTANT_HEAD | BURSAR
    designation: Mapped[str | None] = mapped_column(String(30))
    date_joined: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # GES-specific fields (all nullable — private schools won't have these)
    ges_staff_id: Mapped[str | None] = mapped_column(String(30), index=True)
    registered_no: Mapped[str | None] = mapped_column(String(30))
    licence_no: Mapped[str | None] = mapped_column(String(30))
    ssnit_no: Mapped[str | None] = mapped_column(String(30))

    photo_url: Mapped[str | None] = mapped_column(String(500))

    user: Mapped["User | None"] = relationship(
        back_populates="staff_member", foreign_keys="User.staff_member_id"
    )
    promotions: Mapped[list["StaffPromotion"]] = relationship(
        back_populates="staff_member", order_by="StaffPromotion.date_promoted.desc()"
    )
    qualifications: Mapped[list["StaffQualification"]] = relationship(
        back_populates="staff_member"
    )
    leaves: Mapped[list["StaffLeave"]] = relationship(back_populates="staff_member")
    permission_overrides: Mapped[list["StaffPermission"]] = relationship(
        back_populates="staff_member"
    )

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p)


class StaffPromotion(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Immutable rank history.
    Current rank = latest row by date_obtained.
    Supports backfill: date_obtained may predate date_recorded.
    """

    __tablename__ = "staff_promotion"
    __table_args__ = (
        # Composite covers selectinload + ORDER BY date_promoted DESC
        Index("ix_staff_promotion_member_date", "staff_member_id", "date_promoted"),
    )

    staff_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False
    )
    rank: Mapped[str] = mapped_column(String(120), nullable=False)
    date_promoted: Mapped[date] = mapped_column(Date, nullable=False)
    date_recorded: Mapped[date] = mapped_column(Date, nullable=False)
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )

    staff_member: Mapped["StaffMember"] = relationship(back_populates="promotions")


class StaffQualification(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "staff_qualification"
    __table_args__ = (Index("ix_staff_qualification_member", "staff_member_id"),)

    staff_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False
    )
    degree: Mapped[str] = mapped_column(String(150), nullable=False)
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer)
    document_url: Mapped[str | None] = mapped_column(String(500))

    staff_member: Mapped["StaffMember"] = relationship(back_populates="qualifications")


class StaffLeave(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "staff_leave"
    __table_args__ = (
        Index("ix_staff_leave_member", "staff_member_id"),
        Index("ix_staff_leave_member_dates", "staff_member_id", "start_date", "end_date"),
    )

    staff_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False
    )
    leave_type: Mapped[str] = mapped_column(String(30), nullable=False)  # SICK|ANNUAL|MATERNITY|OTHER
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")  # PENDING|APPROVED|REJECTED
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    staff_member: Mapped["StaffMember"] = relationship(back_populates="leaves")
