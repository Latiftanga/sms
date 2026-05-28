from datetime import date, datetime
from uuid import UUID

from pydantic import EmailStr, field_validator

from app.schemas.common import IDSchema, OrmBase, TimestampSchema

VALID_CATEGORIES = {"TEACHING", "NON-TEACHING"}
VALID_EMPLOYMENT = {"PERMANENT", "CONTRACT", "VOLUNTEER", "GES_POSTED"}
VALID_GENDERS = {"MALE", "FEMALE", "OTHER"}
VALID_DESIGNATIONS = {"TEACHER", "HEADTEACHER", "ASSISTANT_HEAD", "BURSAR"}


# ── Qualifications ────────────────────────────────────────────────────────────

class QualificationCreate(OrmBase):
    degree: str
    institution: str
    year: int | None = None


class QualificationUpdate(OrmBase):
    degree: str | None = None
    institution: str | None = None
    year: int | None = None


class QualificationResponse(IDSchema):
    degree: str
    institution: str
    year: int | None
    document_url: str | None


# ── Promotions / GES rank history ─────────────────────────────────────────────

class PromotionCreate(OrmBase):
    rank: str
    date_promoted: date


class PromotionUpdate(OrmBase):
    rank: str | None = None
    date_promoted: date | None = None


class PromotionResponse(IDSchema):
    rank: str
    date_promoted: date
    date_recorded: date
    recorded_by: UUID


# ── StaffMember ───────────────────────────────────────────────────────────────

class StaffMemberCreate(OrmBase):
    staff_id: str | None = None
    first_name: str
    middle_name: str | None = None
    last_name: str
    gender: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None
    personal_email: EmailStr | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

    category: str
    employment_type: str = "PERMANENT"
    designation: str | None = None
    date_joined: date | None = None

    ges_staff_id: str | None = None
    registered_no: str | None = None
    licence_no: str | None = None
    ssnit_no: str | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {VALID_CATEGORIES}")
        return v

    @field_validator("employment_type")
    @classmethod
    def validate_employment(cls, v: str) -> str:
        if v not in VALID_EMPLOYMENT:
            raise ValueError(f"employment_type must be one of {VALID_EMPLOYMENT}")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_GENDERS:
            raise ValueError(f"gender must be one of {VALID_GENDERS}")
        return v

    @field_validator("designation")
    @classmethod
    def validate_designation(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_DESIGNATIONS:
            raise ValueError(f"designation must be one of {VALID_DESIGNATIONS}")
        return v


class StaffMemberUpdate(OrmBase):
    staff_id: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None
    personal_email: EmailStr | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    category: str | None = None
    employment_type: str | None = None
    designation: str | None = None
    date_joined: date | None = None
    ges_staff_id: str | None = None
    registered_no: str | None = None
    licence_no: str | None = None
    ssnit_no: str | None = None
    is_active: bool | None = None


class StaffMemberResponse(IDSchema, TimestampSchema):
    school_id: UUID
    staff_id: str | None
    first_name: str
    middle_name: str | None
    last_name: str
    gender: str | None
    date_of_birth: date | None
    phone: str | None
    personal_email: str | None
    address: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    category: str
    employment_type: str
    designation: str | None
    date_joined: date | None
    is_active: bool
    photo_url: str | None
    ges_staff_id: str | None
    registered_no: str | None
    licence_no: str | None
    ssnit_no: str | None
    current_rank: str | None = None
    has_account: bool = False


class StaffMemberDetail(StaffMemberResponse):
    qualifications: list[QualificationResponse] = []
    promotions: list[PromotionResponse] = []


# ── Account creation ──────────────────────────────────────────────────────────

class AccountCreateRequest(OrmBase):
    email: EmailStr


class AccountCreateResponse(OrmBase):
    user_id: UUID
    email: str
    temp_password: str  # shown once only


# ── Bulk upload ───────────────────────────────────────────────────────────────

class BulkRowError(OrmBase):
    row: int
    field: str | None
    message: str


class BulkUploadResponse(OrmBase):
    created: int
    skipped: int
    errors: list[BulkRowError]


# ── Positions ─────────────────────────────────────────────────────────────────

class PositionCreate(OrmBase):
    name: str
    code: str
    permissions: list[str] = []  # list of permission_key strings to grant


class PositionUpdate(OrmBase):
    name: str | None = None
    is_active: bool | None = None
    permissions: list[str] | None = None


class PositionResponse(IDSchema):
    name: str
    code: str
    is_system_template: bool
    is_active: bool
    permissions: list[str]


# ── Permission overrides ──────────────────────────────────────────────────────

class PositionAssignRequest(OrmBase):
    position_id: str | None  # UUID string or null to unassign


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
    permissions: dict[str, bool]
    overrides: list[PermissionOverrideResponse]
