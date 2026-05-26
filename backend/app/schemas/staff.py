from datetime import date, datetime
from uuid import UUID

from pydantic import field_validator

from app.schemas.common import IDSchema, OrmBase, TimestampSchema


class StaffMemberCreate(OrmBase):
    first_name: str
    middle_name: str | None = None
    last_name: str
    category: str  # TEACHING | ADMIN | SUPPORT | HEALTH | TECHNICAL
    employment_type: str = "PERMANENT"
    designation: str | None = None
    date_joined: date | None = None
    ges_staff_id: str | None = None
    registered_no: str | None = None
    licence_no: str | None = None
    ssnit: str | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid = {"TEACHING", "ADMIN", "SUPPORT", "HEALTH", "TECHNICAL"}
        if v not in valid:
            raise ValueError(f"category must be one of {valid}")
        return v


class StaffMemberResponse(IDSchema, TimestampSchema):
    school_id: UUID
    first_name: str
    middle_name: str | None
    last_name: str
    category: str
    employment_type: str
    designation: str | None
    date_joined: date | None
    is_active: bool
    photo_url: str | None
    # Computed from StaffPromotion
    current_rank: str | None = None


class PermissionOverrideCreate(OrmBase):
    permission_key: str
    granted: bool
    note: str | None = None


class PermissionOverrideResponse(OrmBase):
    permission_key: str
    granted: bool
    granted_by: UUID
    granted_at: datetime
    note: str | None


class StaffPermissionsResponse(OrmBase):
    staff_member_id: UUID
    permissions: dict[str, bool]  # full resolved map
    overrides: list[PermissionOverrideResponse]  # personal overrides only
