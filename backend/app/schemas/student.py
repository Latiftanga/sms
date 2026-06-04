from datetime import date, datetime
from uuid import UUID

from pydantic import field_validator

from app.schemas.common import IDSchema, OrmBase, TimestampSchema

VALID_GENDERS = {"MALE", "FEMALE"}
VALID_RELATIONSHIPS = {"FATHER", "MOTHER", "GUARDIAN"}
VALID_STUDENT_TYPES = {"DAY", "BOARDING"}
VALID_STATUSES = {"ACTIVE", "TRANSFERRED", "DROPPED"}


# ── Guardian ──────────────────────────────────────────────────────────────────

class GuardianCreate(OrmBase):
    first_name: str
    last_name: str
    relationship_type: str
    phone: str | None = None
    email: str | None = None
    is_primary_contact: bool = False

    @field_validator("relationship_type")
    @classmethod
    def validate_relationship(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_RELATIONSHIPS:
            raise ValueError(f"relationship_type must be one of {VALID_RELATIONSHIPS}")
        return v


class GuardianUpdate(OrmBase):
    first_name: str | None = None
    last_name: str | None = None
    relationship_type: str | None = None
    phone: str | None = None
    email: str | None = None
    is_primary_contact: bool | None = None


class GuardianResponse(IDSchema):
    first_name: str
    last_name: str
    relationship_type: str
    phone: str | None
    email: str | None
    is_primary_contact: bool


# ── Student ───────────────────────────────────────────────────────────────────

class StudentCreate(OrmBase):
    first_name: str
    middle_name: str | None = None
    last_name: str
    gender: str
    date_of_birth: date | None = None
    place_of_birth: str | None = None
    nationality: str = "Ghanaian"
    religion: str | None = None
    admission_date: date | None = None
    admission_number: str | None = None
    previous_school: str | None = None
    guardians: list[GuardianCreate] = []

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_GENDERS:
            raise ValueError(f"gender must be one of {VALID_GENDERS}")
        return v


class StudentUpdate(OrmBase):
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    place_of_birth: str | None = None
    nationality: str | None = None
    religion: str | None = None
    admission_date: date | None = None
    admission_number: str | None = None
    previous_school: str | None = None


# ── Enrollment ────────────────────────────────────────────────────────────────

class EnrollmentCreate(OrmBase):
    class_id: UUID
    academic_year_id: UUID | None = None   # defaults to current year
    student_type: str = "DAY"
    house_id: UUID | None = None

    @field_validator("student_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_STUDENT_TYPES:
            raise ValueError(f"student_type must be one of {VALID_STUDENT_TYPES}")
        return v


class EnrollmentUpdate(OrmBase):
    student_type: str | None = None
    house_id: UUID | None = None
    status: str | None = None
    left_date: date | None = None
    left_reason: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.upper()
        if v not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return v


class EnrollmentResponse(IDSchema, TimestampSchema):
    student_id: UUID
    class_id: UUID
    class_name: str
    academic_year_id: UUID
    year_name: str
    student_type: str
    register_number: str | None
    status: str
    house_id: UUID | None
    house_name: str | None
    left_date: date | None
    left_reason: str | None


# ── Responses ─────────────────────────────────────────────────────────────────

class StudentListItem(IDSchema):
    first_name: str
    middle_name: str | None
    last_name: str
    gender: str
    photo_url: str | None
    is_active: bool
    admission_number: str | None
    # Joined from current-year enrollment (null if not enrolled)
    register_number: str | None
    class_name: str | None
    class_id: UUID | None
    year_name: str | None


class StudentResponse(IDSchema, TimestampSchema):
    school_id: UUID
    first_name: str
    middle_name: str | None
    last_name: str
    full_name: str
    gender: str
    date_of_birth: date | None
    place_of_birth: str | None
    nationality: str
    religion: str | None
    school_issued_id: str | None
    photo_url: str | None
    is_active: bool
    admission_date: date | None
    admission_number: str | None
    previous_school: str | None
    current_enrollment: EnrollmentResponse | None
    guardians: list[GuardianResponse]
