/**
 * Application navigation definition.
 *
 * Groups are separated visually by dividers. No section labels — icons and
 * item names are self-descriptive and work for any school without feeling
 * branded to a specific institution.
 *
 * anyPermission rules
 * ───────────────────
 *  absent / []  →  always visible (e.g. Dashboard)
 *  string[]     →  visible if the user holds ANY of the listed keys
 *
 * Adding a new module: append a NavItem to the right group below.
 * The layout re-filters on every auth change — no other changes needed.
 *
 * Custom school permissions (created via Settings → Positions) work
 * automatically — just reference their key string in anyPermission.
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Icon = any;

export interface NavItem {
  href: string;
  label: string;
  icon: Icon;
  /** Visible if user has ANY of these permission keys. Absent = always show. */
  anyPermission?: string[];
}

/** A group of nav items separated from adjacent groups by a divider. */
export interface NavGroup {
  items: NavItem[];
}

import {
  LayoutDashboard,
  Users,
  ClipboardCheck,
  CreditCard,
  Users2,
  Settings2,
  GraduationCap,
  UserCircle,
} from "@lucide/svelte";

export const NAV: NavGroup[] = [
  // ── Entry point ───────────────────────────────────────────────────
  {
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/profile",   label: "My Profile", icon: UserCircle },
    ],
  },

  // ── Student-facing daily work ─────────────────────────────────────
  // Shown to anyone who works directly with students.
  {
    items: [
      {
        href: "/students",
        label: "Students",
        icon: Users,
        anyPermission: ["view_students", "enroll_students"],
      },
      {
        href: "/attendance",
        label: "Attendance",
        icon: ClipboardCheck,
        anyPermission: ["mark_attendance", "view_attendance"],
      },
      {
        href: "/fees",
        label: "Fees",
        icon: CreditCard,
        anyPermission: ["view_fees", "record_payments", "manage_fee_structure", "waive_fees"],
      },
    ],
  },

  // ── School operations ─────────────────────────────────────────────
  // Staff management and system configuration — elevated access only.
  {
    items: [
      {
        href: "/staff",
        label: "Staff",
        icon: Users2,
        anyPermission: ["view_staff"],
      },
      {
        href: "/academic",
        label: "Academic",
        icon: GraduationCap,
        anyPermission: ["manage_academic_structure"],
      },
      {
        href: "/settings",
        label: "Settings",
        icon: Settings2,
        anyPermission: ["manage_school_config", "manage_academic_structure", "manage_users"],
      },
    ],
  },
];
