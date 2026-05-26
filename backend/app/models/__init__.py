"""
Import all models here so that:
  1. Alembic env.py gets the full metadata for autogenerate.
  2. SQLAlchemy relationship resolution works at startup.
"""
from app.models.base import Base  # noqa: F401
from app.models.reference import GhanaPublicHoliday  # noqa: F401
from app.models.school import School, SchoolConfig, SchoolSchedule  # noqa: F401
from app.models.grading import GradingScale, Grade  # noqa: F401
from app.models.staff import (  # noqa: F401
    StaffPosition,
    PositionPermission,
    StaffPermission,
    StaffMember,
    StaffPromotion,
    StaffQualification,
    StaffLeave,
)
from app.models.user import User  # noqa: F401
from app.models.academic import (  # noqa: F401
    AcademicYear,
    AcademicTerm,
    SchoolCalendar,
    SchoolPeriod,
    House,
    Class,
    ClassSubject,
    ClassTeacher,
    SubjectTeacher,
)
from app.models.student import (  # noqa: F401
    Student,
    Guardian,
    StudentClassEnrollment,
    StudentTermEnrollment,
    StudentBehaviourRecord,
)
from app.models.attendance import AttendanceRecord  # noqa: F401
from app.models.assessment import StudentSubjectRegistration, Score  # noqa: F401
from app.models.fees import FeeStructure, FeePayment  # noqa: F401
from app.models.document import DocumentRecord, ImportBatch  # noqa: F401

__all__ = [
    "Base",
    "GhanaPublicHoliday",
    "School", "SchoolConfig", "SchoolSchedule",
    "GradingScale", "Grade",
    "StaffPosition", "PositionPermission", "StaffPermission",
    "StaffMember", "StaffPromotion", "StaffQualification", "StaffLeave",
    "User",
    "AcademicYear", "AcademicTerm", "SchoolCalendar", "SchoolPeriod",
    "House", "Class", "ClassSubject", "ClassTeacher", "SubjectTeacher",
    "Student", "Guardian",
    "StudentClassEnrollment", "StudentTermEnrollment", "StudentBehaviourRecord",
    "AttendanceRecord",
    "StudentSubjectRegistration", "Score",
    "FeeStructure", "FeePayment",
    "DocumentRecord", "ImportBatch",
]
