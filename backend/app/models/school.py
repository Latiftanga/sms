import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.academic import AcademicYear
    from app.models.staff import StaffPosition
    from app.models.grading import GradingScale


class School(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "school"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True)
    country: Mapped[str] = mapped_column(String(60), nullable=False, default="Ghana")
    region: Mapped[str | None] = mapped_column(String(80))
    district: Mapped[str | None] = mapped_column(String(80))
    address: Mapped[str | None] = mapped_column(String(300))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(120))
    logo_url: Mapped[str | None] = mapped_column(String(500))

    # Facility configuration (set once during onboarding, rarely changed)
    education_levels: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    facility_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MIXED"
    )  # DAY | BOARDING | MIXED
    has_houses: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_fees_module: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Tenancy & identity
    subdomain: Mapped[str | None] = mapped_column(String(63), unique=True, nullable=True)
    custom_domain: Mapped[str | None] = mapped_column(String(253), unique=True, nullable=True)
    emis_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    waec_centre_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    ownership_type: Mapped[str] = mapped_column(String(20), nullable=False, default="PRIVATE")
    accent_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#185FA5")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    config: Mapped["SchoolConfig"] = relationship(back_populates="school", uselist=False)
    schedule: Mapped["SchoolSchedule"] = relationship(back_populates="school", uselist=False)
    academic_years: Mapped[list["AcademicYear"]] = relationship(back_populates="school")
    positions: Mapped[list["StaffPosition"]] = relationship(back_populates="school")


class SchoolConfig(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "school_config"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # Grading scales assigned to this school
    grading_scale_id_basic: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grading_scale.id"), nullable=True
    )
    grading_scale_id_shs: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grading_scale.id"), nullable=True
    )
    grading_scale_id_early: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grading_scale.id"), nullable=True
    )
    # Report card template overrides
    report_template_basic: Mapped[str | None] = mapped_column(String(100))
    report_template_shs: Mapped[str | None] = mapped_column(String(100))
    report_template_early: Mapped[str | None] = mapped_column(String(100))
    # Register number pattern: e.g. "{code}/{year}/{seq:04d}"
    register_number_pattern: Mapped[str] = mapped_column(
        String(100), nullable=False, default="{code}/{year}/{seq:04d}"
    )

    school: Mapped["School"] = relationship(back_populates="config")


class SchoolSchedule(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Defines which days of the week this school operates.
    school_days uses ISO weekday numbers: 1=Mon … 7=Sun.
    Standard: [1,2,3,4,5] (Mon–Fri)  or  [1,2,3,4] (Mon–Thu for some private schools).
    """

    __tablename__ = "school_schedule"
    __table_args__ = (UniqueConstraint("school_id"),)

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    school_days: Mapped[list[int]] = mapped_column(
        ARRAY(INTEGER), nullable=False, default=[1, 2, 3, 4, 5]
    )

    school: Mapped["School"] = relationship(back_populates="schedule")
