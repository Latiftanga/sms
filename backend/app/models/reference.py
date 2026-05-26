"""
Reference / seed-data tables that never change at runtime.
GhanaPublicHoliday is seeded in the baseline migration.
"""
import uuid

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class GhanaPublicHoliday(Base):
    """
    Fixed-date holidays are stored with month+day.
    Variable holidays (Easter, Farmers Day) are stored with holiday_type only
    and computed dynamically by the calendar generator service.
    """

    __tablename__ = "ghana_public_holiday"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # FIXED | EASTER_GOOD_FRIDAY | EASTER_MONDAY | FARMERS_DAY
    holiday_type: Mapped[str] = mapped_column(String(30), nullable=False, default="FIXED")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
