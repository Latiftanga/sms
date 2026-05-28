<script lang="ts">
  import { currentUser } from "$stores/auth";
  import { schoolBranding } from "$stores/school";
  import Badge from "$components/ui/Badge.svelte";
  import {
    Users, CreditCard, ClipboardCheck, UserCheck,
    TrendingUp, TrendingDown, Minus,
    AlertCircle, CheckCircle2, Info,
    ArrowRight, UserPlus, FileText, CalendarCheck,
    ChevronRight, GraduationCap, Wallet,
  } from "@lucide/svelte";

  // ── Greeting ──────────────────────────────────────────────────────
  $: greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  })();
  $: name = $currentUser?.email?.split("@")[0] ?? "there";
  $: today = new Date().toLocaleDateString("en-GH", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });

  // ── Mock data — replace with TanStack Query ───────────────────────
  const students    = { total: 1248, change: +12, label: "+12 this term" };
  const feesTotal   = 112000;
  const feesPaid    = 84320;
  const attendance  = { pct: 91.4, present: 1139, total: 1248 };
  const staff       = { active: 68, onLeave: 4 };

  $: feesPct = Math.round((feesPaid / feesTotal) * 100);

  // SVG donut ring (r=30, stroke-width=6 → circ ≈ 188.5)
  const RING_R    = 30;
  const RING_CIRC = 2 * Math.PI * RING_R;
  $: ringDash = `${(attendance.pct / 100) * RING_CIRC} ${RING_CIRC}`;

  // Term progress
  const termStart   = new Date("2026-01-06");
  const termEnd     = new Date("2026-04-11");
  const termLabel   = "Term 2, 2025/2026";
  $: termPct = Math.min(100, Math.max(0, Math.round(
    ((Date.now() - termStart.getTime()) / (termEnd.getTime() - termStart.getTime())) * 100
  )));
  $: termDaysLeft = Math.max(0, Math.ceil((termEnd.getTime() - Date.now()) / 86_400_000));

  // Weekly attendance sparkline (Mon–Fri)
  const spark = [88.2, 91.0, 90.5, 93.1, 91.4];
  const sparkMax = Math.max(...spark);
  const sparkMin = Math.min(...spark) - 2;

  const transactions = [
    { student: "Ama Owusu",    initials: "AO", class: "JHS 3A", amount: "GHS 850",   date: "26 May",  status: "paid"    },
    { student: "Kweku Mensah", initials: "KM", class: "SHS 1B", amount: "GHS 1,200", date: "26 May",  status: "paid"    },
    { student: "Abena Asante", initials: "AA", class: "JHS 2C", amount: "GHS 700",   date: "25 May",  status: "paid"    },
    { student: "Kofi Boateng", initials: "KB", class: "SHS 2A", amount: "GHS 950",   date: "25 May",  status: "partial" },
    { student: "Akosua Darko", initials: "AD", class: "JHS 1B", amount: "GHS 850",   date: "24 May",  status: "paid"    },
  ];

  const alerts = [
    { type: "warn", text: "14 students have outstanding fees over 30 days." },
    { type: "info", text: "Term 2 timetable has not been published yet."    },
    { type: "ok",   text: "All attendance records up to date."              },
  ];

  const quickActions = [
    { label: "Add Student",      icon: UserPlus,       href: "/students/new"  },
    { label: "Record Payment",   icon: Wallet,         href: "/fees/record"   },
    { label: "Mark Attendance",  icon: ClipboardCheck, href: "/attendance"    },
    { label: "View Reports",     icon: FileText,       href: "/analytics"     },
  ];
</script>

<svelte:head><title>Dashboard — {$schoolBranding?.name ?? 'TTEK-SIS'}</title></svelte:head>

<!-- ── Page header ────────────────────────────────────────────────── -->
<div class="dash-header">
  <div>
    <h1 class="greeting">{greeting}, {name}.</h1>
    {#if $schoolBranding?.motto}
      <p class="school-motto-tag">"{$schoolBranding.motto}"</p>
    {:else}
      <p class="greeting-sub">Here's what's happening at your school today.</p>
    {/if}
  </div>
  <div class="header-meta">
    <span class="today-pill"><CalendarCheck size={12} />{today}</span>
    <Badge variant="accent">{termLabel}</Badge>
  </div>
</div>

<!-- ── KPI grid ───────────────────────────────────────────────────── -->
<div class="kpi-grid">

  <!-- Students -->
  <div class="kpi-card">
    <div class="kpi-top">
      <span class="kpi-label">Total Students</span>
      <div class="kpi-icon"><GraduationCap size={15} /></div>
    </div>
    <div class="kpi-value">{students.total.toLocaleString()}</div>
    <div class="kpi-sub trend-up">
      <TrendingUp size={11} />{students.label}
    </div>
    <!-- Weekly sparkline bars -->
    <div class="spark" aria-hidden="true">
      {#each spark as v, i}
        <div
          class="spark-bar"
          class:spark-last={i === spark.length - 1}
          style="height:{Math.round(((v - sparkMin) / (sparkMax - sparkMin)) * 32) + 6}px"
        ></div>
      {/each}
    </div>
  </div>

  <!-- Fees -->
  <div class="kpi-card">
    <div class="kpi-top">
      <span class="kpi-label">Fees Collected</span>
      <div class="kpi-icon"><CreditCard size={15} /></div>
    </div>
    <div class="kpi-value">GHS {feesPaid.toLocaleString()}</div>
    <div class="kpi-sub trend-neutral">
      <Minus size={11} />of GHS {feesTotal.toLocaleString()} billed
    </div>
    <!-- Progress bar -->
    <div class="progress-track" role="progressbar" aria-valuenow={feesPct} aria-valuemin={0} aria-valuemax={100} aria-label="Fees collected {feesPct}%">
      <div class="progress-fill" style="width:{feesPct}%"></div>
    </div>
    <div class="progress-label">{feesPct}% collected</div>
  </div>

  <!-- Attendance -->
  <div class="kpi-card kpi-attendance">
    <div class="kpi-top">
      <span class="kpi-label">Attendance Today</span>
      <div class="kpi-icon"><ClipboardCheck size={15} /></div>
    </div>
    <div class="kpi-attend-body">
      <div>
        <div class="kpi-value">{attendance.pct}%</div>
        <div class="kpi-sub trend-down">
          <TrendingDown size={11} />{attendance.present} of {attendance.total} present
        </div>
      </div>
      <!-- SVG donut ring -->
      <svg class="donut" width="72" height="72" aria-hidden="true">
        <circle
          class="donut-fill"
          cx="36" cy="36" r={RING_R}
          stroke-dasharray={ringDash}
          stroke-dashoffset="0"
          transform="rotate(-90 36 36)"
        />
      </svg>
    </div>
  </div>

  <!-- Staff -->
  <div class="kpi-card">
    <div class="kpi-top">
      <span class="kpi-label">Active Staff</span>
      <div class="kpi-icon"><UserCheck size={15} /></div>
    </div>
    <div class="kpi-value">{staff.active}</div>
    <div class="kpi-sub trend-neutral">
      <Minus size={11} />{staff.onLeave} on leave today
    </div>
    <!-- Leave indicator dots -->
    <div class="leave-dots" aria-hidden="true">
      {#each Array(Math.min(staff.onLeave, 8)) as _}
        <span class="leave-dot leave"></span>
      {/each}
      {#each Array(Math.min(staff.active, 20)) as _}
        <span class="leave-dot active"></span>
      {/each}
    </div>
  </div>

</div><!-- /kpi-grid -->

<!-- ── Content area ───────────────────────────────────────────────── -->
<div class="dash-content">

  <!-- ── Left: Payments table ─────────────────────────────────────── -->
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">Recent Payments</span>
      <a href="/fees" class="view-all">View all <ArrowRight size={11} /></a>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Student</th>
            <th>Class</th>
            <th class="align-right">Amount</th>
            <th class="hide-sm">Date</th>
            <th class="align-center">Status</th>
          </tr>
        </thead>
        <tbody>
          {#each transactions as tx}
            <tr>
              <td>
                <div class="student-cell">
                  <div class="student-av">{tx.initials}</div>
                  <span class="student-name">{tx.student}</span>
                </div>
              </td>
              <td class="text-muted">{tx.class}</td>
              <td class="align-right fw-med">{tx.amount}</td>
              <td class="text-muted hide-sm">{tx.date}</td>
              <td class="align-center">
                <Badge variant={tx.status === "paid" ? "ok" : "warn"} size="sm">
                  {tx.status}
                </Badge>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  <!-- ── Right sidebar ─────────────────────────────────────────────── -->
  <aside class="dash-aside">

    <!-- Term at a glance -->
    <div class="panel">
      <div class="panel-head"><span class="panel-title">Term at a Glance</span></div>
      <div class="panel-body">
        <div class="term-label">{termLabel}</div>
        <div class="term-dates">
          {termStart.toLocaleDateString("en-GH", { day: "numeric", month: "short" })} –
          {termEnd.toLocaleDateString("en-GH", { day: "numeric", month: "short", year: "numeric" })}
        </div>
        <div class="progress-track" style="margin-top:12px;"
          role="progressbar" aria-valuenow={termPct} aria-valuemin={0} aria-valuemax={100} aria-label="Term progress {termPct}%">
          <div class="progress-fill" style="width:{termPct}%"></div>
        </div>
        <div class="term-meta">
          <span class="term-pct">{termPct}% complete</span>
          <span class="term-days">{termDaysLeft} days left</span>
        </div>
      </div>
    </div>

    <!-- Alerts -->
    <div class="panel">
      <div class="panel-head"><span class="panel-title">Alerts</span></div>
      <div class="panel-body alerts-body">
        {#each alerts as alert}
          <div class="alert-row alert-{alert.type}">
            {#if alert.type === "warn"}
              <AlertCircle size={13} class="alert-icon" />
            {:else if alert.type === "ok"}
              <CheckCircle2 size={13} class="alert-icon" />
            {:else}
              <Info size={13} class="alert-icon" />
            {/if}
            <span class="alert-text">{alert.text}</span>
          </div>
        {/each}
      </div>
    </div>

    <!-- Quick actions -->
    <div class="panel">
      <div class="panel-head"><span class="panel-title">Quick Actions</span></div>
      <div class="qa-list">
        {#each quickActions as action}
          <a href={action.href} class="qa-item">
            <div class="qa-icon"><svelte:component this={action.icon} size={14} /></div>
            <span class="qa-label">{action.label}</span>
            <ChevronRight size={13} class="qa-arrow" />
          </a>
        {/each}
      </div>
    </div>

  </aside>
</div><!-- /dash-content -->

<style>
/* ── Page header ─────────────────────────────────────────────────── */
.dash-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
  flex-wrap: wrap;
}
.greeting {
  font-size: 18px;
  font-weight: 700;
  color: var(--tx-high);
  margin: 0 0 2px;
  line-height: 1.2;
}
.greeting-sub { font-size: 13px; color: var(--tx-low); margin: 0; }
.school-motto-tag {
  font-size: 12px;
  color: var(--tx-low);
  font-style: italic;
  margin: 0;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex-shrink: 0;
}
.today-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--tx-mid);
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  padding: 3px 10px;
  white-space: nowrap;
}

/* ── KPI grid ────────────────────────────────────────────────────── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 18px;
}
@media (max-width: 1020px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 480px)  { .kpi-grid { grid-template-columns: 1fr 1fr; gap: 10px; } }

.kpi-card {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 16px 18px 14px;
  box-shadow: var(--shadow-xs);
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: box-shadow 0.15s, transform 0.15s;
  position: relative;
  overflow: hidden;
}
.kpi-card:hover {
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.kpi-label {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--tx-low);
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.kpi-icon {
  width: 28px;
  height: 28px;
  border-radius: 7px;
  background: var(--accent-subtle);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kpi-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--tx-high);
  line-height: 1;
  letter-spacing: -0.5px;
}
@media (max-width: 480px) { .kpi-value { font-size: 20px; } }

.kpi-sub {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11.5px;
  margin-top: 2px;
}
.trend-up      { color: var(--ok-text); }
.trend-down    { color: var(--err-text); }
.trend-neutral { color: var(--tx-low); }

/* Sparkline */
.spark {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  margin-top: 12px;
  height: 38px;
}
.spark-bar {
  flex: 1;
  background: var(--accent-muted);
  border-radius: 3px 3px 0 0;
  opacity: 0.5;
  transition: opacity 0.1s;
}
.spark-bar.spark-last { background: var(--accent); opacity: 1; }
.kpi-card:hover .spark-bar { opacity: 0.7; }
.kpi-card:hover .spark-bar.spark-last { opacity: 1; }

/* Progress bar */
.progress-track {
  height: 6px;
  border-radius: 4px;
  background: var(--surface-2);
  overflow: hidden;
  margin-top: 10px;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 80%, #fff) 100%);
  border-radius: 4px;
  transition: width 0.6s ease;
}
.progress-label {
  font-size: 11px;
  color: var(--tx-low);
  margin-top: 4px;
}

/* Attendance ring */
.kpi-attend-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex: 1;
}

.donut { overflow: visible; }
.donut-fill {
  fill: none;
  stroke: var(--accent);
  stroke-width: 6;
  stroke-linecap: round;
  transition: stroke-dasharray 0.6s ease;
}

/* Leave dot indicators */
.leave-dots {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: 12px;
}
.leave-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}
.leave-dot.active { background: var(--accent-muted); }
.leave-dot.leave  { background: var(--warn-dot); }

/* ── Content layout ──────────────────────────────────────────────── */
.dash-content {
  display: grid;
  grid-template-columns: 1fr 288px;
  gap: 14px;
  align-items: start;
}
@media (max-width: 960px) {
  .dash-content { grid-template-columns: 1fr; }
  .dash-aside { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
}
@media (max-width: 600px) {
  .dash-aside { grid-template-columns: 1fr; }
}

/* ── Generic panel ───────────────────────────────────────────────── */
.panel {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  box-shadow: var(--shadow-xs);
  overflow: hidden;
}
.dash-aside .panel { margin-bottom: 0; }

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 13px 16px;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-0);
}
.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--tx-high);
}
.view-all {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.1s;
}
.view-all:hover { opacity: 0.75; }

.panel-body { padding: 14px 16px; }

/* ── Data table ──────────────────────────────────────────────────── */
.table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 440px;
}

.data-table thead tr {
  background: var(--surface-2);
}
.data-table th {
  padding: 8px 16px;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--tx-low);
  text-align: left;
  white-space: nowrap;
}
.data-table td {
  padding: 10px 16px;
  font-size: 13px;
  color: var(--tx-high);
  border-top: 1px solid var(--border-subtle);
}
.data-table tbody tr { transition: background 0.1s; }
.data-table tbody tr:hover { background: var(--surface-2); }

.student-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.student-av {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent-subtle);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}
.student-name {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.align-right  { text-align: right !important; }
.align-center { text-align: center !important; }
.text-muted   { color: var(--tx-low) !important; font-size: 12px !important; }
.fw-med       { font-weight: 500; }

@media (max-width: 520px) { .hide-sm { display: none; } }

/* ── Term at a glance ────────────────────────────────────────────── */
.term-label { font-size: 13px; font-weight: 600; color: var(--tx-high); margin-bottom: 3px; }
.term-dates { font-size: 12px; color: var(--tx-low); }
.term-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--tx-low);
  margin-top: 5px;
}
.term-pct   { color: var(--accent); font-weight: 600; }
.term-days  { }

/* ── Alerts ──────────────────────────────────────────────────────── */
.alerts-body { display: flex; flex-direction: column; gap: 8px; }

.alert-row {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  padding: 9px 11px;
  border-radius: 8px;
  font-size: 12.5px;
  line-height: 1.45;
}
.alert-warn { background: var(--warn-bg); color: var(--warn-text); }
.alert-ok   { background: var(--ok-bg);   color: var(--ok-text);   }
.alert-info { background: var(--accent-subtle); color: var(--accent); }
:global(.alert-icon) { flex-shrink: 0; margin-top: 1px; }
.alert-text { flex: 1; }

/* ── Quick actions ───────────────────────────────────────────────── */
.qa-list { display: flex; flex-direction: column; }

.qa-item {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 16px;
  text-decoration: none;
  color: var(--tx-mid);
  font-size: 13px;
  font-weight: 500;
  border-top: 1px solid var(--border-subtle);
  transition: background 0.1s, color 0.1s;
}
.qa-item:first-child { border-top: none; }
.qa-item:hover { background: var(--surface-2); color: var(--tx-high); }

.qa-icon {
  width: 30px;
  height: 30px;
  border-radius: 7px;
  background: var(--accent-subtle);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.1s;
}
.qa-item:hover .qa-icon { background: var(--accent); color: var(--accent-fg); }

.qa-label { flex: 1; }
:global(.qa-arrow) { color: var(--tx-low); flex-shrink: 0; }
</style>
