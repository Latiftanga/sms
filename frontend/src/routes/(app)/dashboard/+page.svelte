<script lang="ts">
  import { onMount } from "svelte";
  import { api } from "$lib/api/client";
  import { currentUser } from "$stores/auth";
  import { schoolBranding } from "$stores/school";
  import Badge from "$components/ui/Badge.svelte";
  import {
    Users, BookOpen, UserX, BookMarked,
    AlertTriangle, CheckCircle2, Clock, ChevronRight,
    CalendarCheck, UserPlus, Settings, GraduationCap,
    ClipboardCheck, PenLine, Wallet, User, ArrowRight,
    Lock,
  } from "@lucide/svelte";

  // ── Types ──────────────────────────────────────────────────────────
  interface TermSummary {
    id: string; name: string; year_name: string;
    start_date: string; end_date: string; is_current: boolean;
  }
  interface AdminStats {
    staff_total: number; staff_no_account: number;
    classes_total: number; classes_no_teacher: number;
  }
  interface MyClass {
    id: string; name: string; education_level: string;
    level: string; year: number | null; stream: string | null;
  }
  interface DashboardSummary {
    role: string;
    current_term: TermSummary | null;
    admin: AdminStats | null;
    my_classes: MyClass[] | null;
  }

  // ── State ──────────────────────────────────────────────────────────
  let loading = true;
  let data: DashboardSummary | null = null;

  onMount(async () => {
    try {
      const res = await api.get<DashboardSummary>("/dashboard/summary");
      data = res.data;
    } finally {
      loading = false;
    }
  });

  // ── Greeting ───────────────────────────────────────────────────────
  $: greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  })();
  $: firstName = $currentUser?.full_name?.split(" ")[0]
    || $currentUser?.email?.split("@")[0]
    || "there";
  $: today = new Date().toLocaleDateString("en-GH", {
    weekday: "long", day: "numeric", month: "long",
  });

  // ── Term calculations ──────────────────────────────────────────────
  $: term = data?.current_term ?? null;
  $: termStart  = term ? new Date(term.start_date) : null;
  $: termEnd    = term ? new Date(term.end_date)   : null;
  $: termPct    = termStart && termEnd
    ? Math.min(100, Math.max(0, Math.round(
        ((Date.now() - termStart.getTime()) / (termEnd.getTime() - termStart.getTime())) * 100
      )))
    : null;
  $: termDaysLeft = termEnd
    ? Math.max(0, Math.ceil((termEnd.getTime() - Date.now()) / 86_400_000))
    : null;

  function fmtDate(d: Date) {
    return d.toLocaleDateString("en-GH", { day: "numeric", month: "short" });
  }

  // ── Quick actions by role ──────────────────────────────────────────
  const QUICK_ACTIONS: Record<string, { label: string; icon: unknown; href: string }[]> = {
    admin: [
      { label: "Invite Staff",    icon: UserPlus,       href: "/staff"              },
      { label: "Manage Classes",  icon: BookOpen,       href: "/settings/academic"  },
      { label: "School Settings", icon: Settings,       href: "/settings"           },
      { label: "My Profile",      icon: User,           href: "/profile"            },
    ],
    teacher: [
      { label: "Mark Attendance", icon: ClipboardCheck, href: "/attendance"         },
      { label: "Enter Scores",    icon: PenLine,        href: "/scores"             },
      { label: "My Profile",      icon: User,           href: "/profile"            },
    ],
    staff: [
      { label: "My Profile",      icon: User,           href: "/profile"            },
    ],
  };
  $: quickActions = QUICK_ACTIONS[data?.role ?? "staff"] ?? QUICK_ACTIONS.staff;
</script>

<svelte:head>
  <title>Dashboard — {$schoolBranding?.name ?? "TTEK SMS"}</title>
</svelte:head>

<!-- ── Page header ────────────────────────────────────────────────────────── -->
<div class="dash-header">
  <div>
    <h1 class="greeting">{greeting}, {firstName}.</h1>
    <p class="sub">
      {#if $schoolBranding?.motto}"{$schoolBranding.motto}"
      {:else if data?.role === "admin"}Here's your school at a glance.
      {:else if data?.role === "teacher"}Ready for today's classes.
      {:else}Welcome back.{/if}
    </p>
  </div>
  <div class="header-meta">
    <span class="today-pill"><CalendarCheck size={12} />{today}</span>
    {#if term}
      <Badge variant="accent">{term.name} · {term.year_name}</Badge>
    {/if}
  </div>
</div>

<!-- ── Loading skeleton ───────────────────────────────────────────────────── -->
{#if loading}
  <div class="kpi-grid">
    {#each [1,2,3,4] as _}
      <div class="kpi-card">
        <div class="skeleton sk-label"></div>
        <div class="skeleton sk-value"></div>
        <div class="skeleton sk-sub"></div>
      </div>
    {/each}
  </div>
  <div class="dash-body">
    <div class="panel"><div class="skeleton sk-panel"></div></div>
    <aside class="dash-aside">
      <div class="panel"><div class="skeleton sk-panel-sm"></div></div>
    </aside>
  </div>

<!-- ── ADMIN VIEW ─────────────────────────────────────────────────────────── -->
{:else if data?.role === "admin" && data.admin}
  {@const s = data.admin}

  <div class="kpi-grid">
    <!-- Active Staff -->
    <a href="/staff" class="kpi-card kpi-link">
      <div class="kpi-top">
        <span class="kpi-label">Active Staff</span>
        <div class="kpi-icon"><Users size={15} /></div>
      </div>
      <div class="kpi-value">{s.staff_total}</div>
      <div class="kpi-sub neutral">Members on record</div>
    </a>

    <!-- Total Classes -->
    <a href="/settings/academic" class="kpi-card kpi-link">
      <div class="kpi-top">
        <span class="kpi-label">Classes</span>
        <div class="kpi-icon"><BookOpen size={15} /></div>
      </div>
      <div class="kpi-value">{s.classes_total}</div>
      <div class="kpi-sub neutral">Active classes</div>
    </a>

    <!-- Staff without accounts -->
    <a href="/staff?filter=no_account" class="kpi-card kpi-link"
       class:kpi-warn={s.staff_no_account > 0}>
      <div class="kpi-top">
        <span class="kpi-label">Needs Invite</span>
        <div class="kpi-icon kpi-icon-warn">
          {#if s.staff_no_account > 0}<UserX size={15} />
          {:else}<CheckCircle2 size={15} />{/if}
        </div>
      </div>
      <div class="kpi-value">{s.staff_no_account}</div>
      <div class="kpi-sub" class:warn-text={s.staff_no_account > 0} class:ok-text={s.staff_no_account === 0}>
        {s.staff_no_account > 0 ? "Staff without accounts" : "All staff have accounts"}
      </div>
    </a>

    <!-- Classes without teacher -->
    <a href="/settings/academic" class="kpi-card kpi-link"
       class:kpi-warn={s.classes_no_teacher > 0}>
      <div class="kpi-top">
        <span class="kpi-label">No Teacher</span>
        <div class="kpi-icon kpi-icon-warn">
          {#if s.classes_no_teacher > 0}<BookMarked size={15} />
          {:else}<CheckCircle2 size={15} />{/if}
        </div>
      </div>
      <div class="kpi-value">{s.classes_no_teacher}</div>
      <div class="kpi-sub" class:warn-text={s.classes_no_teacher > 0} class:ok-text={s.classes_no_teacher === 0}>
        {s.classes_no_teacher > 0 ? "Classes unassigned" : "All classes assigned"}
      </div>
    </a>
  </div>

  <div class="dash-body">
    <!-- Setup checklist -->
    <div class="panel">
      <div class="panel-head">
        <span class="panel-title">School Setup</span>
        <a href="/settings" class="view-all">All settings <ArrowRight size={11} /></a>
      </div>
      <div class="checklist">
        <div class="check-item">
          <div class="check-dot" class:dot-ok={!!term} class:dot-warn={!term}>
            {#if term}<CheckCircle2 size={13} />{:else}<AlertTriangle size={13} />{/if}
          </div>
          <div class="check-body">
            <p class="check-label">Active term</p>
            <p class="check-desc">{term ? `${term.name} · ${term.year_name}` : "No active term — set one in Settings → Academic Years"}</p>
          </div>
          <a href="/settings/academic" class="check-action"><ChevronRight size={14} /></a>
        </div>

        <div class="check-item">
          <div class="check-dot" class:dot-ok={s.staff_no_account === 0} class:dot-warn={s.staff_no_account > 0}>
            {#if s.staff_no_account === 0}<CheckCircle2 size={13} />{:else}<AlertTriangle size={13} />{/if}
          </div>
          <div class="check-body">
            <p class="check-label">Staff accounts</p>
            <p class="check-desc">
              {#if s.staff_no_account === 0}All {s.staff_total} staff have login accounts
              {:else}{s.staff_no_account} of {s.staff_total} staff still need inviting{/if}
            </p>
          </div>
          <a href="/staff" class="check-action"><ChevronRight size={14} /></a>
        </div>

        <div class="check-item">
          <div class="check-dot" class:dot-ok={s.classes_no_teacher === 0} class:dot-warn={s.classes_no_teacher > 0}>
            {#if s.classes_no_teacher === 0}<CheckCircle2 size={13} />{:else}<AlertTriangle size={13} />{/if}
          </div>
          <div class="check-body">
            <p class="check-label">Class teacher assignments</p>
            <p class="check-desc">
              {#if s.classes_no_teacher === 0}All {s.classes_total} classes have a teacher
              {:else}{s.classes_no_teacher} of {s.classes_total} classes have no teacher assigned{/if}
            </p>
          </div>
          <a href="/settings/academic" class="check-action"><ChevronRight size={14} /></a>
        </div>

        <!-- Upcoming modules -->
        <div class="check-item check-soon">
          <div class="check-dot dot-soon"><Lock size={13} /></div>
          <div class="check-body">
            <p class="check-label">Student enrollment</p>
            <p class="check-desc">Coming soon — enroll students into classes</p>
          </div>
        </div>

        <div class="check-item check-soon">
          <div class="check-dot dot-soon"><Lock size={13} /></div>
          <div class="check-body">
            <p class="check-label">Fee structure</p>
            <p class="check-desc">Coming soon — configure term fees per class</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Right sidebar -->
    <aside class="dash-aside">
      <div class="panel">
        <div class="panel-head"><span class="panel-title">Term at a Glance</span></div>
        <div class="panel-body">
          {#if term && termStart && termEnd && termPct !== null}
            <div class="term-label">{term.name} · {term.year_name}</div>
            <div class="term-dates">{fmtDate(termStart)} – {fmtDate(termEnd)}</div>
            <div class="progress-track" role="progressbar"
              aria-valuenow={termPct} aria-valuemin={0} aria-valuemax={100}>
              <div class="progress-fill" style="width:{termPct}%"></div>
            </div>
            <div class="term-meta">
              <span class="term-pct">{termPct}% complete</span>
              <span class="term-days">{termDaysLeft}d left</span>
            </div>
          {:else}
            <div class="term-empty">
              <Clock size={16} />
              <span>No active term. Configure one in Settings → Academic Years.</span>
            </div>
          {/if}
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><span class="panel-title">Quick Actions</span></div>
        <div class="qa-list">
          {#each quickActions as action}
            <a href={action.href} class="qa-item">
              <div class="qa-icon"><svelte:component this={action.icon} size={14} /></div>
              <span class="qa-label">{action.label}</span>
              <ChevronRight size={12} class="qa-arrow" />
            </a>
          {/each}
        </div>
      </div>
    </aside>
  </div>

<!-- ── TEACHER VIEW ───────────────────────────────────────────────────────── -->
{:else if data?.role === "teacher"}
  <div class="dash-body">
    <div class="panel">
      <div class="panel-head">
        <span class="panel-title">My Classes</span>
        {#if term}<Badge variant="subtle">{term.year_name}</Badge>{/if}
      </div>

      {#if data.my_classes && data.my_classes.length > 0}
        <div class="class-list">
          {#each data.my_classes as cls}
            <div class="class-item">
              <div class="class-badge">{cls.level.charAt(0)}{cls.year ?? ""}</div>
              <div class="class-body">
                <p class="class-name">{cls.name}</p>
                <p class="class-sub">{cls.education_level.replace("_", " ")}</p>
              </div>
              <div class="class-actions">
                <a href="/attendance?class={cls.id}" class="class-btn">
                  <ClipboardCheck size={13} /> Attendance
                </a>
                <a href="/scores?class={cls.id}" class="class-btn">
                  <PenLine size={13} /> Scores
                </a>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="empty-state">
          <div class="empty-icon"><GraduationCap size={26} /></div>
          <p class="empty-title">No classes assigned yet</p>
          <p class="empty-body">Your class teacher assignments for {term?.year_name ?? "this year"} will appear here once configured by the admin.</p>
        </div>
      {/if}
    </div>

    <aside class="dash-aside">
      <div class="panel">
        <div class="panel-head"><span class="panel-title">Term at a Glance</span></div>
        <div class="panel-body">
          {#if term && termStart && termEnd && termPct !== null}
            <div class="term-label">{term.name} · {term.year_name}</div>
            <div class="term-dates">{fmtDate(termStart)} – {fmtDate(termEnd)}</div>
            <div class="progress-track" role="progressbar"
              aria-valuenow={termPct} aria-valuemin={0} aria-valuemax={100}>
              <div class="progress-fill" style="width:{termPct}%"></div>
            </div>
            <div class="term-meta">
              <span class="term-pct">{termPct}% complete</span>
              <span class="term-days">{termDaysLeft}d left</span>
            </div>
          {:else}
            <div class="term-empty"><Clock size={16} /><span>No active term set.</span></div>
          {/if}
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><span class="panel-title">Quick Actions</span></div>
        <div class="qa-list">
          {#each quickActions as action}
            <a href={action.href} class="qa-item">
              <div class="qa-icon"><svelte:component this={action.icon} size={14} /></div>
              <span class="qa-label">{action.label}</span>
              <ChevronRight size={12} class="qa-arrow" />
            </a>
          {/each}
        </div>
      </div>
    </aside>
  </div>

<!-- ── STUDENT / PARENT VIEW ─────────────────────────────────────────────── -->
{:else if data?.role === "student" || data?.role === "parent"}
  <div class="dash-body">
    <div class="panel">
      <div class="empty-state" style="padding:64px 32px">
        <div class="empty-icon"><GraduationCap size={28} /></div>
        <p class="empty-title">
          {data.role === "student" ? "Student portal" : "Parent portal"} coming soon
        </p>
        <p class="empty-body">
          {data.role === "student"
            ? "Your attendance, scores, timetable and fee balance will appear here."
            : "Your child's academic progress, attendance and fee balance will appear here."}
        </p>
      </div>
    </div>

    <aside class="dash-aside">
      <div class="panel">
        <div class="panel-head"><span class="panel-title">Term at a Glance</span></div>
        <div class="panel-body">
          {#if term && termStart && termEnd && termPct !== null}
            <div class="term-label">{term.name} · {term.year_name}</div>
            <div class="term-dates">{fmtDate(termStart)} – {fmtDate(termEnd)}</div>
            <div class="progress-track" role="progressbar"
              aria-valuenow={termPct} aria-valuemin={0} aria-valuemax={100}>
              <div class="progress-fill" style="width:{termPct}%"></div>
            </div>
            <div class="term-meta">
              <span class="term-pct">{termPct}% complete</span>
              <span class="term-days">{termDaysLeft}d left</span>
            </div>
          {:else}
            <div class="term-empty"><Clock size={16} /><span>No active term set.</span></div>
          {/if}
        </div>
      </div>
    </aside>
  </div>

<!-- ── FALLBACK (staff with no specific role) ─────────────────────────────── -->
{:else if data}
  <div class="dash-body">
    <div class="panel">
      <div class="empty-state">
        <div class="empty-icon"><Users size={26} /></div>
        <p class="empty-title">Welcome to {$schoolBranding?.name ?? "TTEK SMS"}</p>
        <p class="empty-body">Your account is active. Contact your administrator to be assigned a role and permissions.</p>
      </div>
    </div>

    <aside class="dash-aside">
      <div class="panel">
        <div class="panel-head"><span class="panel-title">Term at a Glance</span></div>
        <div class="panel-body">
          {#if term && termStart && termEnd && termPct !== null}
            <div class="term-label">{term.name} · {term.year_name}</div>
            <div class="term-dates">{fmtDate(termStart)} – {fmtDate(termEnd)}</div>
            <div class="progress-track" role="progressbar"
              aria-valuenow={termPct} aria-valuemin={0} aria-valuemax={100}>
              <div class="progress-fill" style="width:{termPct}%"></div>
            </div>
            <div class="term-meta">
              <span class="term-pct">{termPct}% complete</span>
              <span class="term-days">{termDaysLeft}d left</span>
            </div>
          {:else}
            <div class="term-empty"><Clock size={16} /><span>No active term set.</span></div>
          {/if}
        </div>
      </div>
      <div class="panel">
        <div class="panel-head"><span class="panel-title">Quick Actions</span></div>
        <div class="qa-list">
          <a href="/profile" class="qa-item">
            <div class="qa-icon"><User size={14} /></div>
            <span class="qa-label">My Profile</span>
            <ChevronRight size={12} class="qa-arrow" />
          </a>
        </div>
      </div>
    </aside>
  </div>
{/if}

<style>
/* ── Header ──────────────────────────────────────────────────────── */
.dash-header {
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: 16px;
  margin-bottom: 20px; flex-wrap: wrap;
}
.greeting { font-size: 18px; font-weight: 700; color: var(--tx-high); margin: 0 0 2px; }
.sub { font-size: 13px; color: var(--tx-low); margin: 0; font-style: italic; }
.header-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex-shrink: 0; }
.today-pill {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; color: var(--tx-mid);
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 20px; padding: 3px 10px; white-space: nowrap;
}

/* ── KPI grid ────────────────────────────────────────────────────── */
.kpi-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 12px; margin-bottom: 16px;
}
@media (max-width: 1020px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 480px)  { .kpi-grid { grid-template-columns: 1fr 1fr; gap: 8px; } }

.kpi-card {
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 12px; padding: 16px 18px 14px;
  box-shadow: var(--shadow-xs); display: flex; flex-direction: column; gap: 4px;
  text-decoration: none; color: inherit;
  transition: box-shadow 0.15s, transform 0.15s, border-color 0.15s;
}
.kpi-link:hover { box-shadow: var(--shadow-sm); transform: translateY(-1px); }
.kpi-warn { border-color: color-mix(in srgb, #f59e0b 35%, var(--border-subtle)); }
.kpi-warn:hover { border-color: #f59e0b; }

.kpi-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.kpi-label { font-size: 11px; font-weight: 600; color: var(--tx-low); text-transform: uppercase; letter-spacing: 0.04em; }

.kpi-icon {
  width: 28px; height: 28px; border-radius: 7px;
  background: var(--accent-subtle); color: var(--accent);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.kpi-warn .kpi-icon-warn { background: color-mix(in srgb, #f59e0b 12%, transparent); color: #d97706; }
.kpi-card:not(.kpi-warn) .kpi-icon-warn { background: var(--ok-bg, #d1fae5); color: var(--ok-text, #065f46); }

.kpi-value { font-size: 26px; font-weight: 700; color: var(--tx-high); line-height: 1; letter-spacing: -0.5px; }
@media (max-width: 480px) { .kpi-value { font-size: 20px; } }
.kpi-sub { font-size: 11.5px; margin-top: 2px; }
.neutral { color: var(--tx-low); }
.warn-text { color: #d97706; font-weight: 500; }
.ok-text   { color: var(--ok-text, #065f46); font-weight: 500; }

/* ── Body layout ─────────────────────────────────────────────────── */
.dash-body {
  display: grid; grid-template-columns: 1fr 272px;
  gap: 14px; align-items: start;
}
@media (max-width: 960px) {
  .dash-body { grid-template-columns: 1fr; }
  .dash-aside { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
}
@media (max-width: 600px) { .dash-aside { grid-template-columns: 1fr; } }

/* ── Panel ───────────────────────────────────────────────────────── */
.panel {
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 12px; box-shadow: var(--shadow-xs); overflow: hidden;
}
.dash-aside .panel { margin-bottom: 0; }
.panel-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-0);
}
.panel-title { font-size: 13px; font-weight: 600; color: var(--tx-high); }
.view-all {
  display: inline-flex; align-items: center; gap: 3px;
  font-size: 12px; color: var(--accent); text-decoration: none;
  font-weight: 500; transition: opacity 0.1s;
}
.view-all:hover { opacity: 0.75; }
.panel-body { padding: 14px 16px; }

/* ── Setup checklist ─────────────────────────────────────────────── */
.checklist { display: flex; flex-direction: column; }
.check-item {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 13px 16px; border-top: 1px solid var(--border-subtle);
  transition: background 0.1s;
}
.check-item:first-child { border-top: none; }
.check-item:not(.check-soon):hover { background: var(--surface-2); }
.check-soon { opacity: 0.55; }

.check-dot {
  width: 26px; height: 26px; border-radius: 7px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; margin-top: 1px;
}
.dot-ok   { background: var(--ok-bg, #d1fae5);  color: var(--ok-text, #065f46); }
.dot-warn { background: color-mix(in srgb, #f59e0b 12%, transparent); color: #d97706; }
.dot-soon { background: var(--surface-2); color: var(--tx-low); }

.check-body { flex: 1; min-width: 0; }
.check-label { font-size: 13px; font-weight: 500; color: var(--tx-high); margin: 0 0 2px; }
.check-desc  { font-size: 12px; color: var(--tx-low); margin: 0; line-height: 1.4; }

.check-action {
  width: 26px; height: 26px; border-radius: 6px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: var(--tx-low); text-decoration: none; margin-top: 2px;
  transition: background 0.1s, color 0.1s;
}
.check-action:hover { background: var(--accent-subtle); color: var(--accent); }

/* ── Class list (teacher view) ───────────────────────────────────── */
.class-list { display: flex; flex-direction: column; }
.class-item {
  display: flex; align-items: center; gap: 14px;
  padding: 12px 16px; border-top: 1px solid var(--border-subtle);
  transition: background 0.1s;
}
.class-item:first-child { border-top: none; }
.class-item:hover { background: var(--surface-2); }

.class-badge {
  width: 38px; height: 38px; border-radius: 10px; flex-shrink: 0;
  background: var(--accent-subtle); color: var(--accent);
  font-size: 12px; font-weight: 700; letter-spacing: -0.3px;
  display: flex; align-items: center; justify-content: center;
}
.class-body { flex: 1; min-width: 0; }
.class-name { font-size: 13px; font-weight: 600; color: var(--tx-high); margin: 0 0 2px; }
.class-sub  { font-size: 11px; color: var(--tx-low); margin: 0; text-transform: capitalize; }

.class-actions { display: flex; gap: 6px; flex-shrink: 0; }
.class-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 10px; border-radius: 7px; font-size: 12px; font-weight: 500;
  color: var(--tx-mid); border: 1px solid var(--border-subtle);
  text-decoration: none; background: var(--surface-0);
  transition: background 0.1s, color 0.1s, border-color 0.1s;
}
.class-btn:hover {
  background: var(--accent-subtle); color: var(--accent);
  border-color: color-mix(in srgb, var(--accent) 30%, var(--border-subtle));
}
@media (max-width: 600px) { .class-actions { display: none; } }

/* ── Term at a glance ────────────────────────────────────────────── */
.term-label { font-size: 13px; font-weight: 600; color: var(--tx-high); margin-bottom: 3px; }
.term-dates { font-size: 12px; color: var(--tx-low); }
.progress-track {
  height: 6px; border-radius: 4px; background: var(--surface-2);
  overflow: hidden; margin-top: 10px;
}
.progress-fill {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 80%, #fff) 100%);
  transition: width 0.6s ease;
}
.term-meta { display: flex; justify-content: space-between; font-size: 11px; color: var(--tx-low); margin-top: 5px; }
.term-pct { color: var(--accent); font-weight: 600; }
.term-empty { display: flex; align-items: flex-start; gap: 8px; color: var(--tx-low); font-size: 12.5px; line-height: 1.5; }
.term-empty :global(svg) { flex-shrink: 0; margin-top: 1px; }

/* ── Quick actions ───────────────────────────────────────────────── */
.qa-list { display: flex; flex-direction: column; }
.qa-item {
  display: flex; align-items: center; gap: 10px;
  padding: 11px 16px; text-decoration: none;
  color: var(--tx-mid); font-size: 13px; font-weight: 500;
  border-top: 1px solid var(--border-subtle);
  transition: background 0.1s, color 0.1s;
}
.qa-item:first-child { border-top: none; }
.qa-item:hover { background: var(--surface-2); color: var(--tx-high); }
.qa-icon {
  width: 28px; height: 28px; border-radius: 7px;
  background: var(--accent-subtle); color: var(--accent);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  transition: background 0.1s;
}
.qa-item:hover .qa-icon { background: var(--accent); color: var(--accent-fg, #fff); }
.qa-label { flex: 1; }
:global(.qa-arrow) { color: var(--tx-low); flex-shrink: 0; }

/* ── Empty state ─────────────────────────────────────────────────── */
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  text-align: center; padding: 48px 32px; gap: 10px;
}
.empty-icon {
  width: 52px; height: 52px; border-radius: 14px;
  background: var(--surface-2); color: var(--tx-low);
  display: flex; align-items: center; justify-content: center; margin-bottom: 4px;
}
.empty-title { font-size: 14px; font-weight: 600; color: var(--tx-high); margin: 0; }
.empty-body  { font-size: 13px; color: var(--tx-low); margin: 0; max-width: 360px; line-height: 1.55; }

/* ── Skeletons ───────────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position:  400px 0; }
}
.skeleton {
  background: linear-gradient(90deg, var(--surface-2) 25%, var(--border-subtle) 50%, var(--surface-2) 75%);
  background-size: 800px 100%; animation: shimmer 1.4s infinite linear; border-radius: 6px;
}
.sk-label  { height: 10px; width: 60px; margin-bottom: 10px; }
.sk-value  { height: 28px; width: 56px; margin-bottom: 8px; }
.sk-sub    { height: 10px; width: 100px; }
.sk-panel  { height: 220px; margin: 0; border-radius: 0; }
.sk-panel-sm { height: 120px; margin: 0; border-radius: 0; }
</style>
