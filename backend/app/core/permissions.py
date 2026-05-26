from enum import StrEnum


class Permission(StrEnum):
    # ── Students ──────────────────────────────────────────────────
    VIEW_STUDENTS = "view_students"
    ENROLL_STUDENTS = "enroll_students"
    TRANSFER_STUDENTS = "transfer_students"

    # ── Staff ─────────────────────────────────────────────────────
    VIEW_STAFF = "view_staff"
    MANAGE_STAFF = "manage_staff"
    MANAGE_PROMOTIONS = "manage_promotions"

    # ── Academics ─────────────────────────────────────────────────
    VIEW_SCORES = "view_scores"
    ENTER_SCORES = "enter_scores"
    APPROVE_SCORES = "approve_scores"
    MANAGE_TIMETABLE = "manage_timetable"

    # ── Attendance ────────────────────────────────────────────────
    MARK_ATTENDANCE = "mark_attendance"
    VIEW_ATTENDANCE = "view_attendance"

    # ── Reports ───────────────────────────────────────────────────
    GENERATE_REPORTS = "generate_reports"
    REVOKE_DOCUMENTS = "revoke_documents"

    # ── Fees ──────────────────────────────────────────────────────
    VIEW_FEES = "view_fees"
    RECORD_PAYMENTS = "record_payments"
    MANAGE_FEE_STRUCTURE = "manage_fee_structure"
    WAIVE_FEES = "waive_fees"

    # ── Communication ─────────────────────────────────────────────
    SEND_SMS = "send_sms"
    SEND_ANNOUNCEMENTS = "send_announcements"

    # ── Houses ────────────────────────────────────────────────────
    MANAGE_HOUSES = "manage_houses"
    MANAGE_EXEATS = "manage_exeats"
    NIGHT_ROLL_CALL = "night_roll_call"

    # ── Settings ──────────────────────────────────────────────────
    MANAGE_SCHOOL_CONFIG = "manage_school_config"
    MANAGE_ACADEMIC_STRUCTURE = "manage_academic_structure"
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"


ALL_PERMISSIONS: list[str] = [p.value for p in Permission]

# ── Seeded position permission templates ─────────────────────────
# True = granted, False (or absence) = denied

POSITION_DEFAULTS: dict[str, dict[str, bool]] = {
    "ADMIN": {p: True for p in ALL_PERMISSIONS},

    "HEADTEACHER": {
        Permission.VIEW_STUDENTS: True,
        Permission.ENROLL_STUDENTS: True,
        Permission.TRANSFER_STUDENTS: True,
        Permission.VIEW_STAFF: True,
        Permission.VIEW_SCORES: True,
        Permission.APPROVE_SCORES: True,
        Permission.MANAGE_TIMETABLE: True,
        Permission.VIEW_ATTENDANCE: True,
        Permission.GENERATE_REPORTS: True,
        Permission.REVOKE_DOCUMENTS: True,
        Permission.VIEW_FEES: True,
        Permission.SEND_ANNOUNCEMENTS: True,
        Permission.MANAGE_HOUSES: True,
        Permission.MANAGE_ACADEMIC_STRUCTURE: True,
        Permission.VIEW_ANALYTICS: True,
    },

    "ASSISTANT_HEAD": {
        Permission.VIEW_STUDENTS: True,
        Permission.ENROLL_STUDENTS: True,
        Permission.TRANSFER_STUDENTS: True,
        Permission.VIEW_STAFF: True,
        Permission.VIEW_SCORES: True,
        Permission.APPROVE_SCORES: True,
        Permission.MARK_ATTENDANCE: True,
        Permission.VIEW_ATTENDANCE: True,
        Permission.GENERATE_REPORTS: True,
        Permission.SEND_ANNOUNCEMENTS: True,
        Permission.MANAGE_HOUSES: True,
        Permission.MANAGE_EXEATS: True,
    },

    "SENIOR_HOUSEMASTER": {
        Permission.VIEW_STUDENTS: True,
        Permission.MARK_ATTENDANCE: True,
        Permission.VIEW_ATTENDANCE: True,
        Permission.SEND_ANNOUNCEMENTS: True,
        Permission.MANAGE_HOUSES: True,
        Permission.MANAGE_EXEATS: True,
        Permission.NIGHT_ROLL_CALL: True,
    },

    "BURSAR": {
        Permission.VIEW_STUDENTS: True,
        Permission.GENERATE_REPORTS: True,
        Permission.VIEW_FEES: True,
        Permission.RECORD_PAYMENTS: True,
        Permission.MANAGE_FEE_STRUCTURE: True,
        Permission.WAIVE_FEES: True,
        Permission.SEND_SMS: True,
    },

    "CLASS_TEACHER": {
        Permission.VIEW_STUDENTS: True,
        Permission.VIEW_SCORES: True,
        Permission.ENTER_SCORES: True,
        Permission.MARK_ATTENDANCE: True,
        Permission.VIEW_ATTENDANCE: True,
        Permission.GENERATE_REPORTS: True,
    },
}
