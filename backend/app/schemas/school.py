from uuid import UUID

from pydantic import EmailStr, field_validator

from app.schemas.common import IDSchema, OrmBase, TimestampSchema


class SchoolCreate(OrmBase):
    name: str
    code: str
    subdomain: str | None = None
    region: str | None = None
    district: str | None = None
    address: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    emis_number: str | None = None
    waec_centre_number: str | None = None
    ownership_type: str = "PRIVATE"
    education_levels: list[str]
    facility_type: str = "MIXED"
    has_houses: bool = False
    has_fees_module: bool = True
    accent_color: str = "#185FA5"
    school_days: list[int] = [1, 2, 3, 4, 5]

    @field_validator("school_days")
    @classmethod
    def validate_school_days(cls, v: list[int]) -> list[int]:
        if not v or not all(1 <= d <= 7 for d in v):
            raise ValueError("school_days must be ISO weekday numbers 1–7")
        return sorted(set(v))

    @field_validator("education_levels")
    @classmethod
    def validate_levels(cls, v: list[str]) -> list[str]:
        valid = {"EARLY_CHILDHOOD", "BASIC", "JHS", "SHS", "TECHNICAL"}
        invalid = set(v) - valid
        if invalid:
            raise ValueError(f"Unknown education levels: {invalid}")
        return v


class SchoolResponse(IDSchema, TimestampSchema):
    name: str
    code: str
    slug: str
    subdomain: str | None
    custom_domain: str | None
    address: str | None
    phone: str | None
    email: str | None
    region: str | None
    district: str | None
    emis_number: str | None
    waec_centre_number: str | None
    ownership_type: str
    education_levels: list[str]
    facility_type: str
    has_houses: bool
    has_fees_module: bool
    attendance_mode: str   # DAILY | LESSON
    accent_color: str
    logo_url: str | None
    motto: str | None
    is_active: bool


class SchoolScheduleResponse(OrmBase):
    school_id: UUID
    school_days: list[int]
