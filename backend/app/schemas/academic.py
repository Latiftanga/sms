from datetime import date, time
from uuid import UUID

from pydantic import model_validator

from app.schemas.common import IDSchema, OrmBase, TimestampSchema


class AcademicTermCreate(OrmBase):
    name: str
    start_date: date
    end_date: date
    education_levels: list[str]

    @model_validator(mode="after")
    def validate_dates(self) -> "AcademicTermCreate":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class AcademicTermResponse(IDSchema, TimestampSchema):
    academic_year_id: UUID
    name: str
    start_date: date
    end_date: date
    education_levels: list[str]
    is_current: bool
    block_owing_students: bool
    total_school_days: int = 0  # populated by query


class CalendarDayUpdate(OrmBase):
    day_type: str  # SCHOOL_DAY | HOLIDAY | CLOSURE | WEEKEND
    label: str | None = None

    @model_validator(mode="after")
    def validate_type(self) -> "CalendarDayUpdate":
        valid = {"SCHOOL_DAY", "HOLIDAY", "CLOSURE", "WEEKEND"}
        if self.day_type not in valid:
            raise ValueError(f"day_type must be one of {valid}")
        return self


class CalendarDayResponse(OrmBase):
    id: UUID
    date: date
    day_type: str
    label: str | None


class SchoolPeriodCreate(OrmBase):
    name: str
    start_time: time
    end_time: time
    position: int
    is_lesson: bool = True

    @model_validator(mode="after")
    def validate_times(self) -> "SchoolPeriodCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class SchoolPeriodResponse(IDSchema, TimestampSchema):
    school_id: UUID
    name: str
    start_time: time
    end_time: time
    position: int
    is_lesson: bool
    is_active: bool
