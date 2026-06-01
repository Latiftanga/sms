export interface User {
  id: string;
  email: string;
  full_name: string | null;
  system_role: "SUPERADMIN" | "SCHOOL_STAFF" | "STUDENT" | "PARENT";
  school_id: string | null;
  permissions: Record<string, boolean>;
  must_change_password: boolean;
}

export interface School {
  id: string;
  name: string;
  code: string;
  slug: string;
  education_levels: string[];
  facility_type: string;
  has_houses: boolean;
  has_fees_module: boolean;
  is_active: boolean;
}

export interface AcademicTerm {
  id: string;
  academic_year_id: string;
  name: string;
  start_date: string;
  end_date: string;
  education_levels: string[];
  is_current: boolean;
  block_owing_students: boolean;
  total_school_days: number;
}

export interface CalendarDay {
  id: string;
  date: string;
  day_type: "SCHOOL_DAY" | "HOLIDAY" | "CLOSURE" | "WEEKEND";
  label: string | null;
}

export interface AttendanceRecord {
  id: string;
  school_calendar_id: string;
  school_period_id: string | null;
  student_term_enrollment_id: string;
  status: "PRESENT" | "ABSENT" | "LATE" | "EXCUSED";
  marked_at: string;
  note: string | null;
}

export interface AttendanceSummary {
  student_term_enrollment_id: string;
  total_school_days: number;
  present_days: number;
  absent_days: number;
  late_days: number;
  excused_days: number;
  attendance_percentage: number;
}

export type Permission = string;

export interface PagedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// ── Staff ─────────────────────────────────────────────────────────

export type StaffCategory = "TEACHING" | "NON-TEACHING";
export type StaffDesignation = "TEACHER" | "HEADTEACHER" | "ASSISTANT_HEAD" | "BURSAR" | "HOUSEMASTER" | "SENIOR_HOUSEMASTER";
export type StaffEmploymentType = "PERMANENT" | "CONTRACT" | "VOLUNTEER" | "GES_POSTED";
export type Gender = "MALE" | "FEMALE" | "OTHER";

export interface StaffMember {
  id: string;
  school_id: string;
  staff_id: string | null;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  gender: Gender | null;
  date_of_birth: string | null;
  phone: string | null;
  personal_email: string | null;
  address: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  category: StaffCategory;
  employment_type: StaffEmploymentType;
  designation: StaffDesignation | null;
  date_joined: string | null;
  is_active: boolean;
  photo_url: string | null;
  ges_staff_id: string | null;
  registered_no: string | null;
  licence_no: string | null;
  ssnit_no: string | null;
  current_rank: string | null;
  has_account: boolean;
  created_at: string;
  updated_at: string;
}

export interface Qualification {
  id: string;
  degree: string;
  institution: string;
  year: number | null;
  document_url: string | null;
}

export interface Promotion {
  id: string;
  rank: string;
  date_promoted: string;
  date_recorded: string;
  recorded_by: string;
  document_url: string | null;
}

export interface CurrentTermResponse {
  term_name: string;
  year_name: string;
  start_date: string;
  end_date: string;
}

export interface StaffMemberDetail extends StaffMember {
  qualifications: Qualification[];
  promotions: Promotion[];
  invite_pending: boolean;
}

export interface InviteResponse {
  invite_token: string;
  email: string;
  sms_sent: boolean;
}

export interface Role {
  id: string;
  name: string;
  code: string;
  is_system_template: boolean;
}

export interface UserRole {
  id: string;
  role: Role;
  assigned_at: string;
}

export interface StaffPermissionsResponse {
  staff_member_id: string;
  roles: UserRole[];
  permissions: Record<string, boolean>;
  overrides: Array<{
    permission_key: string;
    granted: boolean;
    granted_by: string;
    granted_at: string;
    note: string | null;
  }>;
}

export interface BulkRowError {
  row: number;
  field: string | null;
  message: string;
}

export interface BulkUploadResponse {
  created: number;
  skipped: number;
  errors: BulkRowError[];
}

export interface StaffPosition {
  id: string;
  name: string;
  code: string;
  is_system_template: boolean;
  is_active: boolean;
  permissions: string[];
}
