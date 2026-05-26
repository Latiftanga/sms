export interface User {
  id: string;
  email: string;
  system_role: "SUPERADMIN" | "SCHOOL_STAFF" | "STUDENT" | "PARENT";
  school_id: string | null;
  permissions: Record<string, boolean>;
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
