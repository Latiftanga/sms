from app.schemas.common import IDSchema, OrmBase, PagedResponse, TimestampSchema, MessageResponse
from app.schemas.school import SchoolCreate, SchoolResponse, SchoolScheduleResponse
from app.schemas.staff import (
    StaffMemberCreate, StaffMemberUpdate, StaffMemberResponse, StaffMemberDetail,
    QualificationCreate, QualificationResponse,
    PromotionCreate, PromotionResponse,
    AccountCreateRequest, AccountCreateResponse,
    BulkUploadResponse, BulkRowError,
    PositionCreate, PositionUpdate, PositionResponse,
    StaffPermissionsResponse, PermissionOverrideCreate,
)
from app.schemas.academic import (
    AcademicTermCreate, AcademicTermResponse,
    CalendarDayUpdate, CalendarDayResponse,
    SchoolPeriodCreate, SchoolPeriodResponse,
)
from app.schemas.attendance import (
    AttendanceMarkRequest, AttendanceRecordResponse, AttendanceSummaryResponse,
)

__all__ = [
    "OrmBase", "IDSchema", "TimestampSchema", "PagedResponse", "MessageResponse",
    "SchoolCreate", "SchoolResponse", "SchoolScheduleResponse",
    "StaffMemberCreate", "StaffMemberUpdate", "StaffMemberResponse", "StaffMemberDetail",
    "QualificationCreate", "QualificationResponse",
    "PromotionCreate", "PromotionResponse",
    "AccountCreateRequest", "AccountCreateResponse",
    "BulkUploadResponse", "BulkRowError",
    "PositionCreate", "PositionUpdate", "PositionResponse",
    "StaffPermissionsResponse", "PermissionOverrideCreate",
    "AcademicTermCreate", "AcademicTermResponse",
    "CalendarDayUpdate", "CalendarDayResponse",
    "SchoolPeriodCreate", "SchoolPeriodResponse",
    "AttendanceMarkRequest", "AttendanceRecordResponse", "AttendanceSummaryResponse",
]
