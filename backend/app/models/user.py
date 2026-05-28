import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.staff import StaffMember, StaffPosition


class User(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Authentication identity. One User per human.

    system_role controls top-level access:
      SUPERADMIN   — Tagnatek staff. Bypasses all permission checks. school_id = NULL.
      SCHOOL_STAFF — permission-gated via UserRole + StaffPermission overrides.
      STUDENT      — read-only, scoped to own academic data.
      PARENT       — read-only, scoped to own children's data.
    """

    __tablename__ = "user"
    __table_args__ = (
        UniqueConstraint("email"),
        Index("ix_user_school_id", "school_id"),
        Index("ix_user_staff_member_id", "staff_member_id"),
    )

    email: Mapped[str] = mapped_column(String(254), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    system_role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SCHOOL_STAFF"
    )  # SUPERADMIN | SCHOOL_STAFF | STUDENT | PARENT

    # NULL for SUPERADMIN; set for all school-scoped users
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="SET NULL"), nullable=True
    )

    # Linked staff record (NULL for STUDENT / PARENT)
    staff_member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_member.id", ondelete="SET NULL"), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Invite flow
    invite_token: Mapped[str | None] = mapped_column(String(100), unique=True)
    invite_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    staff_member: Mapped["StaffMember | None"] = relationship(
        foreign_keys=[staff_member_id], back_populates="user"
    )
    user_roles: Mapped[list["UserRole"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UserRole.user_id",
    )


class UserRole(Base):
    """
    Junction table: a user can hold multiple roles (M2M).
    Permission resolution unions all assigned roles, then personal overrides win.
    """

    __tablename__ = "user_role"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id"),
        Index("ix_user_role_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_position.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="user_roles")
    role: Mapped["StaffPosition"] = relationship(foreign_keys=[role_id])
