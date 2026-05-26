from datetime import date
from uuid import UUID

from pydantic import field_validator, model_validator

from app.schemas.common import IDSchema, OrmBase, TimestampSchema

# ── Valid values ──────────────────────────────────────────────────────────────

VALID_LEVELS = {"Creche", "Nursery", "KG", "Basic", "SHS"}
EDUCATION_LEVEL_MAP = {
    "Creche": "EARLY_CHILDHOOD",
    "Nursery": "EARLY_CHILDHOOD",
    "KG": "EARLY_CHILDHOOD",
    "Basic": "BASIC",
    "SHS": "SHS",
}
GES_LEARNING_AREAS = {
    "General Science", "General Arts", "Business",
    "Visual Arts", "Home Economics", "Technical", "Agriculture",
}

# ── Academic Year ─────────────────────────────────────────────────────────────

class AcademicYearCreate(OrmBase):
    name: str
    start_date: date
    end_date: date

class AcademicYearUpdate(OrmBase):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None

class AcademicYearResponse(IDSchema, TimestampSchema):
    name: str
    start_date: date
    end_date: date
    is_current: bool
    terms: list["AcademicTermResponse"] = []

# ── Academic Term ─────────────────────────────────────────────────────────────

class AcademicTermCreate(OrmBase):
    name: str
    start_date: date
    end_date: date

class AcademicTermUpdate(OrmBase):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None

class AcademicTermResponse(IDSchema, TimestampSchema):
    name: str
    start_date: date
    end_date: date
    is_current: bool
    block_owing_students: bool

# ── Learning Area (SHS only) ──────────────────────────────────────────────────

class LearningAreaCreate(OrmBase):
    name: str
    short_name: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v not in GES_LEARNING_AREAS:
            raise ValueError(
                f"Unknown learning area. Valid: {', '.join(sorted(GES_LEARNING_AREAS))}"
            )
        return v

class LearningAreaUpdate(OrmBase):
    short_name: str | None = None
    is_active: bool | None = None

class LearningAreaResponse(IDSchema, TimestampSchema):
    name: str
    short_name: str | None
    is_active: bool

# ── Class ─────────────────────────────────────────────────────────────────────

class ClassCreate(OrmBase):
    level: str
    year: int | None = None
    learning_area_id: UUID | None = None
    stream: str | None = None

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        if v not in VALID_LEVELS:
            raise ValueError(f"level must be one of: {', '.join(sorted(VALID_LEVELS))}")
        return v

    @model_validator(mode="after")
    def validate_class_rules(self) -> "ClassCreate":
        # Creche has no year
        if self.level == "Creche" and self.year is not None:
            raise ValueError("Creche does not have a year number")
        # All other levels require a year
        if self.level != "Creche" and self.year is None:
            raise ValueError(f"{self.level} requires a year number")
        # Year bounds
        year_bounds = {"Nursery": (1, 2), "KG": (1, 2), "Basic": (1, 9), "SHS": (1, 3)}
        if self.level in year_bounds and self.year is not None:
            lo, hi = year_bounds[self.level]
            if not (lo <= self.year <= hi):
                raise ValueError(f"{self.level} year must be between {lo} and {hi}")
        # SHS needs a learning area; others must not have one
        if self.level == "SHS" and self.learning_area_id is None:
            raise ValueError("SHS classes require a learning_area_id")
        if self.level != "SHS" and self.learning_area_id is not None:
            raise ValueError("learning_area_id is only valid for SHS classes")
        return self

class ClassUpdate(OrmBase):
    stream: str | None = None
    is_active: bool | None = None

class ClassResponse(IDSchema, TimestampSchema):
    education_level: str
    level: str
    year: int | None
    stream: str | None
    is_active: bool
    learning_area: LearningAreaResponse | None = None
    name: str                   # computed on the model

# ── School profile (PATCH) ────────────────────────────────────────────────────

class SchoolProfileUpdate(OrmBase):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    region: str | None = None
    district: str | None = None
    accent_color: str | None = None

    @field_validator("accent_color")
    @classmethod
    def validate_hex(cls, v: str | None) -> str | None:
        if v and (not v.startswith("#") or len(v) not in (4, 7)):
            raise ValueError("accent_color must be a CSS hex colour e.g. #185FA5")
        return v

# Rebuild forward reference
AcademicYearResponse.model_rebuild()
