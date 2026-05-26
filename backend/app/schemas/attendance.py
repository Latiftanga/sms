from datetime import datetime
from uuid import UUID

from pydantic import field_validator, model_validator

from app.schemas.common import IDSchema, OrmBase


class AttendanceMarkRequest(OrmBase):
    """
    POST body for marking attendance for a single class.
    school_calendar_id is validated server-side to be a SCHOOL_DAY row.
    school_period_id = None means daily attendance (Phase 5 default).
    """
    school_calendar_id: UUID
    school_period_id: UUID | None = None
    records: list["AttendanceEntryRequest"]


class AttendanceEntryRequest(OrmBase):
    student_term_enrollment_id: UUID
    status: str
    note: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"PRESENT", "ABSENT", "LATE", "EXCUSED"}
        if v not in valid:
            raise ValueError(f"status must be one of {valid}")
        return v


class AttendanceRecordResponse(IDSchema):
    school_calendar_id: UUID
    school_period_id: UUID | None
    student_term_enrollment_id: UUID
    status: str
    marked_by: UUID
    marked_at: datetime
    note: str | None


class AttendanceSummaryResponse(OrmBase):
    student_term_enrollment_id: UUID
    total_school_days: int
    present_days: int
    absent_days: int
    late_days: int
    excused_days: int
    attendance_percentage: float
