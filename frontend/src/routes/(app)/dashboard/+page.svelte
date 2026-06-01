<script lang="ts">
  import { onMount } from "svelte";
  import { api } from "$lib/api/client";
  import { currentUser } from "$stores/auth";
  import { schoolBranding } from "$stores/school";
  import Badge from "$components/ui/Badge.svelte";
  import {
    Users, CreditCard, ClipboardCheck, UserCheck,
    AlertCircle, ArrowRight, UserPlus, FileText,
    CalendarCheck, ChevronRight, GraduationCap,
    Wallet, Clock, Lock,
  } from "@lucide/svelte";

  // ── Greeting ──────────────────────────────────────────────────────
  $: greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  })();
  $: name = $currentUser?.full_name?.split(" ")[0] || $currentUser?.email?.split("@")[0] || "there";
  $: today = new Date().toLocaleDateString("en-GH", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });

  // ── Staff count ───────────────────────────────────────────────────
  let staffLoading = true;
  let staffTotal: number | null = null;

  // ── Current term ──────────────────────────────────────────────────
  let termLoading = true;
  let termLabel: string | null = null;
  let termStart: Date | null = null;
  let termEnd: Date | null = null;

  $: termPct = termStart && termEnd
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
  function fmtDateLong(d: Date) {
    return d.toLocaleDateString("en-GH", { day: "numeric", month: "short", year: "numeric" });
  }

  onMount(() => {
    Promise.all([
      api.get("/staff", { params: { is_active: true, limit: 1 } })
        .then(({ data }) => { staffTotal = data.total; })
        .catch(() => { staffTotal = null; })
        .finally(() => { staffLoading = false; }),

      api.get("/settings/current-term")
        .then(({ data }) => {
          if (data) {
            termLabel = `${data.term_name} · ${data.year_name}`;
            termStart = new Date(data.start_date);
            termEnd   = new Date(data.end_date);
          }
        })
        .catch(() => {})
        .finally(() => { termLoading = false; }),
    ]);
  });

  const quickActions = [
    { label: "Add Student",     icon: UserPlus,       href: "/students/new" },
    { label: "Record Payment",  icon: Wallet,         href: "/fees/record"  },
    { label: "Mark Attendance", icon: ClipboardCheck, href: "/attendance"   },
    { label: "View Reports",    icon: FileText,        href: "/analytics"    },
  ];
</script>

<svelte:head><title>Dashboard — {$schoolBranding?.name ?? 'TTEK-SIS'}</title></svelte:head>

<!-- ── Page header ────────────────────────────────────────────────── -->
<div class="dash-header">
  <div>
    <h1 class="greeting">{greeting}, {name}.</h1>
    {#if $schoolBranding?.motto}
      <p class="sub-text">"{$schoolBranding.motto}"</p>
    {:else}
      <p class="sub-text">Here's an overview of your school.</p>
    {/if}
  </div>
  <div class="header-meta">
    <span class="today-pill"><CalendarCheck size={12} />{today}</span>
    {#if termLabel}
      <Badge variant="accent">{termLabel}</Badge>
    {/if}
  </div>
</div>

<!-- ── KPI grid ───────────────────────────────────────────────────── -->
<div class="kpi-grid">

  <!-- Students — module not yet available -->
  <div class="kpi-card kpi-unavailable">
    <div class="kpi-top">
      <span class="kpi-label">Total Students</span>
      <div class="kpi-icon"><GraduationCap size={15} /></div>
    </div>
    <div class="kpi-value">—</div>
    <div class="kpi-sub unavail-sub"><Lock size={10} />Students module coming soon</div>
  </div>

  <!-- Fees — module not yet available -->
  <div class="kpi-card kpi-unavailable">
    <div class="kpi-top">
      <span class="kpi-label">Fees Collected</span>
      <div class="kpi-icon"><CreditCard size={15} /></div>
    </div>
    <div class="kpi-value">—</div>
    <div class="kpi-sub unavail-sub"><Lock size={10} />Fees module coming soon</div>
  </div>

  <!-- Attendance — module not yet available -->
  <div class="kpi-card kpi-unavailable">
    <div class="kpi-top">
      <span class="kpi-label">Attendance Today</span>
      <div class="kpi-icon"><ClipboardCheck size={15} /></div>
    </div>
    <div class="kpi-value">—</div>
    <div class="kpi-sub unavail-sub"><Lock size={10} />Attendance module coming soon</div>
  </div>

  <!-- Active Staff — live data -->
  <div class="kpi-card">
    <div class="kpi-top">
      <span class="kpi-label">Active Staff</span>
      <div class="kpi-icon"><UserCheck size={15} /></div>
    </div>
    {#if staffLoading}
      <div class="skeleton skeleton-value"></div>
      <div class="skeleton skeleton-sub"></div>
    {:else if staffTotal !== null}
      <div class="kpi-value">{staffTotal}</div>
      <div class="kpi-sub trend-neutral">Active members on record</div>
    {:else}
      <div class="kpi-value">—</div>
      <div class="kpi-sub unavail-sub"><AlertCircle size={10} />Could not load</div>
    {/if}
  </div>

</div>

<!-- ── Content area ───────────────────────────────────────────────── -->
<div class="dash-content">

  <!-- ── Left: Recent activity ────────────────────────────────────── -->
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">Recent Activity</span>
      <a href="/fees" class="view-all">View all <ArrowRight size={11} /></a>
    </div>
    <div class="empty-state">
      <div class="empty-icon"><Clock size={28} /></div>
      <p class="empty-title">No activity yet</p>
      <p class="empty-body">Student payments, attendance events, and other records will appear here once the relevant modules are set up.</p>
    </div>
  </div>

  <!-- ── Right sidebar ─────────────────────────────────────────────── -->
  <aside class="dash-aside">

    <!-- Term at a Glance -->
    <div class="panel">
      <div class="panel-head"><span class="panel-title">Term at a Glance</span></div>
      <div class="panel-body">
        {#if termLoading}
          <div class="skeleton skeleton-line" style="width:60%;margin-bottom:6px"></div>
          <div class="skeleton skeleton-line" style="width:80%"></div>
          <div class="skeleton skeleton-bar" style="margin-top:14px"></div>
        {:else if termLabel && termStart && termEnd && termPct !== null}
          <div class="term-label">{termLabel}</div>
          <div class="term-dates">{fmtDate(termStart)} – {fmtDateLong(termEnd)}</div>
          <div class="progress-track" style="margin-top:12px"
            role="progressbar"
            aria-valuenow={termPct}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Term progress {termPct}%">
            <div class="progress-fill" style="width:{termPct}%"></div>
          </div>
          <div class="term-meta">
            <span class="term-pct">{termPct}% complete</span>
            <span class="term-days">{termDaysLeft} day{termDaysLeft === 1 ? '' : 's'} left</span>
          </div>
        {:else}
          <div class="term-empty">
            <Clock size={18} />
            <span>No active term set.<br />Configure one in Settings → Academic Years.</span>
          </div>
        {/if}
      </div>
    </div>

    <!-- Alerts -->
    <div class="panel">
      <div class="panel-head"><span class="panel-title">Alerts</span></div>
      <div class="panel-body alerts-body">
        <div class="no-alerts">
          <span class="no-alerts-dot"></span>
          All clear — no alerts at this time.
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
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
</div>

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
.sub-text { font-size: 13px; color: var(--tx-low); margin: 0; font-style: italic; }

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

/* ── Skeleton loader ─────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position:  400px 0; }
}
.skeleton {
  background: linear-gradient(90deg,
    var(--surface-2) 25%,
    var(--border-subtle) 50%,
    var(--surface-2) 75%
  );
  background-size: 800px 100%;
  animation: shimmer 1.4s infinite linear;
  border-radius: 6px;
}
.skeleton-value { height: 32px; width: 64px; margin-bottom: 8px; }
.skeleton-sub   { height: 12px; width: 120px; }
.skeleton-line  { height: 13px; border-radius: 4px; }
.skeleton-bar   { height: 6px;  border-radius: 4px; width: 100%; }

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
}
.kpi-card:hover {
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}
.kpi-unavailable {
  opacity: 0.7;
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
.kpi-unavailable .kpi-icon {
  background: var(--surface-2);
  color: var(--tx-low);
}

.kpi-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--tx-high);
  line-height: 1;
  letter-spacing: -0.5px;
}
.kpi-unavailable .kpi-value { color: var(--tx-low); }
@media (max-width: 480px) { .kpi-value { font-size: 20px; } }

.kpi-sub {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11.5px;
  margin-top: 2px;
}
.trend-neutral { color: var(--tx-low); }
.unavail-sub   { color: var(--tx-low); font-style: italic; gap: 5px; }

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

/* ── Empty state ─────────────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 32px;
  gap: 10px;
}
.empty-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: var(--surface-2);
  color: var(--tx-low);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
}
.empty-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--tx-high);
  margin: 0;
}
.empty-body {
  font-size: 13px;
  color: var(--tx-low);
  margin: 0;
  max-width: 380px;
  line-height: 1.55;
}

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
.term-pct  { color: var(--accent); font-weight: 600; }
.term-empty {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  color: var(--tx-low);
  font-size: 12.5px;
  line-height: 1.5;
}
.term-empty :global(svg) { flex-shrink: 0; margin-top: 1px; }

/* ── Alerts ──────────────────────────────────────────────────────── */
.alerts-body { display: flex; flex-direction: column; gap: 8px; }
.no-alerts {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 12.5px;
  color: var(--tx-low);
  padding: 2px 0;
}
.no-alerts-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ok-text);
  flex-shrink: 0;
}

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
