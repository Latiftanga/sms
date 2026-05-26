from app.schemas.common import IDSchema, OrmBase, PaginatedResponse, TimestampSchema, MessageResponse
from app.schemas.school import SchoolCreate, SchoolResponse, SchoolScheduleResponse
from app.schemas.staff import StaffMemberCreate, StaffMemberResponse, StaffPermissionsResponse
from app.schemas.academic import (
    AcademicTermCreate, AcademicTermResponse,
    CalendarDayUpdate, CalendarDayResponse,
    SchoolPeriodCreate, SchoolPeriodResponse,
)
from app.schemas.attendance import (
    AttendanceMarkRequest, AttendanceRecordResponse, AttendanceSummaryResponse,
)

__all__ = [
    "OrmBase", "IDSchema", "TimestampSchema", "PaginatedResponse", "MessageResponse",
    "SchoolCreate", "SchoolResponse", "SchoolScheduleResponse",
    "StaffMemberCreate", "StaffMemberResponse", "StaffPermissionsResponse",
    "AcademicTermCreate", "AcademicTermResponse",
    "CalendarDayUpdate", "CalendarDayResponse",
    "SchoolPeriodCreate", "SchoolPeriodResponse",
    "AttendanceMarkRequest", "AttendanceRecordResponse", "AttendanceSummaryResponse",
]
