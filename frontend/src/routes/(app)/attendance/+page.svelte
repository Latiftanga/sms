<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { api } from "$api/client";
  import { auth } from "$stores/auth";
  import { schoolBranding } from "$stores/school";
  import Button from "$components/ui/Button.svelte";
  import Badge from "$components/ui/Badge.svelte";
  import {
    ClipboardCheck, CheckCircle2, AlertCircle,
    Clock, Users, ChevronRight, Calendar,
  } from "@lucide/svelte";

  interface AttendableClass {
    class_id: string;
    class_name: string;
    education_level: string;
    today_submitted: boolean;
  }

  $: canMark    = $auth.user?.permissions?.mark_attendance === true || $auth.user?.system_role === "SUPERADMIN";
  $: canView    = $auth.user?.permissions?.view_attendance === true || $auth.user?.system_role === "SUPERADMIN";
  $: isAdmin    = $auth.user?.permissions?.manage_staff === true || $auth.user?.system_role === "SUPERADMIN";

  let classes: AttendableClass[] = [];
  let loading = true;
  let error = "";

  const today = new Date().toLocaleDateString("en-GH", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });
  const todayISO = new Date().toISOString().slice(0, 10);
  const dayOfWeek = new Date().getDay(); // 0=Sun, 6=Sat
  const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

  onMount(async () => {
    if (!canMark && !canView) { loading = false; return; }
    try {
      const { data } = await api.get<AttendableClass[]>("/attendance/classes");
      classes = data;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error = err?.response?.data?.detail ?? "Could not load classes.";
    } finally {
      loading = false;
    }
  });

  $: submitted  = classes.filter(c => c.today_submitted).length;
  $: pending    = classes.filter(c => !c.today_submitted).length;

  function groupByLevel(list: AttendableClass[]) {
    const map: Record<string, AttendableClass[]> = {};
    for (const c of list) {
      (map[c.education_level] ??= []).push(c);
    }
    return Object.entries(map);
  }
  $: grouped = groupByLevel(classes);

  function levelLabel(l: string): string {
    return ({ BASIC: "Basic / JHS", SHS: "Senior High School", EARLY_CHILDHOOD: "Early Childhood" })[l] ?? l;
  }
</script>

<svelte:head><title>Attendance — {$schoolBranding?.name ?? "TTEK SMS"}</title></svelte:head>

<div class="page-header">
  <div>
    <h1 class="page-title">Attendance</h1>
    <p class="page-sub"><Calendar size={12} /> {today}</p>
  </div>
</div>

{#if isWeekend}
  <div class="weekend-notice">
    <Clock size={16} /> Today is a weekend — no attendance to mark.
  </div>
{:else if loading}
  <div class="class-grid">
    {#each [1,2,3,4] as _}
      <div class="class-card skeleton-card">
        <div class="sk sk-name"></div>
        <div class="sk sk-badge"></div>
      </div>
    {/each}
  </div>

{:else if error}
  <div class="error-box"><AlertCircle size={14} /> {error}</div>

{:else if classes.length === 0}
  <div class="empty-state">
    <div class="empty-icon"><ClipboardCheck size={26} /></div>
    <p class="empty-title">No classes assigned</p>
    <p class="empty-body">
      {#if canMark}Class teacher assignments will appear here once configured by the admin.
      {:else}You don't have permission to mark attendance.{/if}
    </p>
  </div>

{:else}
  <!-- Summary strip -->
  <div class="summary-strip">
    <div class="summary-stat">
      <CheckCircle2 size={15} class="ok-icon" />
      <span class="summary-val">{submitted}</span>
      <span class="summary-label">submitted</span>
    </div>
    <div class="summary-div"></div>
    <div class="summary-stat">
      <Clock size={15} class="pending-icon" />
      <span class="summary-val">{pending}</span>
      <span class="summary-label">pending</span>
    </div>
    <div class="summary-div"></div>
    <div class="summary-stat">
      <Users size={15} />
      <span class="summary-val">{classes.length}</span>
      <span class="summary-label">total classes</span>
    </div>
  </div>

  <!-- Classes grouped by level -->
  {#each grouped as [level, levelClasses]}
    {#if grouped.length > 1}
      <p class="level-label">{levelLabel(level)}</p>
    {/if}
    <div class="class-grid">
      {#each levelClasses as c}
        <button
          class="class-card"
          class:submitted={c.today_submitted}
          on:click={() => goto(`/attendance/mark?class_id=${c.class_id}`)}
        >
          <div class="class-card-top">
            <div class="class-initial">{c.class_name.charAt(0)}</div>
            <div class="class-info">
              <p class="class-name">{c.class_name}</p>
              <p class="class-level">{levelLabel(c.education_level)}</p>
            </div>
          </div>
          <div class="class-card-bottom">
            {#if c.today_submitted}
              <span class="status-chip submitted-chip">
                <CheckCircle2 size={11} /> Submitted
              </span>
            {:else}
              <span class="status-chip pending-chip">
                <Clock size={11} /> Mark attendance
              </span>
            {/if}
            <ChevronRight size={14} class="card-arrow" />
          </div>
        </button>
      {/each}
    </div>
  {/each}
{/if}

<style>
.page-header { margin-bottom: 20px; }
.page-title  { font-size: 18px; font-weight: 700; color: var(--tx-high); margin: 0 0 4px; }
.page-sub    { display: flex; align-items: center; gap: 5px; font-size: 13px; color: var(--tx-low); margin: 0; }

.weekend-notice {
  display: flex; align-items: center; gap: 9px;
  padding: 14px 18px; border-radius: 10px; font-size: 13px;
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  color: var(--tx-low);
}

.error-box {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; border-radius: 10px; font-size: 13px;
  background: color-mix(in srgb, #ef4444 10%, transparent);
  color: #dc2626; border: 1px solid color-mix(in srgb, #ef4444 25%, transparent);
}

/* Summary strip */
.summary-strip {
  display: flex; align-items: center; gap: 0;
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 12px; padding: 14px 20px; margin-bottom: 20px;
  box-shadow: var(--shadow-xs);
}
.summary-stat {
  display: flex; align-items: center; gap: 7px; padding: 0 20px 0 0;
  font-size: 13px; color: var(--tx-mid);
}
.summary-stat:first-child { padding-left: 0; }
.summary-val   { font-size: 20px; font-weight: 700; color: var(--tx-high); }
.summary-label { font-size: 12px; color: var(--tx-low); }
.summary-div   { width: 1px; height: 28px; background: var(--border-subtle); margin: 0 20px 0 0; flex-shrink: 0; }
:global(.ok-icon)      { color: #22c55e; }
:global(.pending-icon) { color: #f59e0b; }

/* Level label */
.level-label {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.07em; color: var(--tx-low); margin: 0 0 10px;
}

/* Class grid */
.class-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px; margin-bottom: 20px;
}

.class-card {
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 12px; padding: 16px; cursor: pointer;
  text-align: left; box-shadow: var(--shadow-xs);
  transition: box-shadow 0.15s, transform 0.15s, border-color 0.15s;
  display: flex; flex-direction: column; gap: 12px;
}
.class-card:hover {
  box-shadow: var(--shadow-sm); transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--accent) 30%, var(--border-subtle));
}
.class-card.submitted { border-color: color-mix(in srgb, #22c55e 30%, var(--border-subtle)); }
.class-card.submitted:hover { border-color: #22c55e; }

.class-card-top { display: flex; align-items: center; gap: 12px; }
.class-initial {
  width: 40px; height: 40px; border-radius: 10px; flex-shrink: 0;
  background: var(--accent-subtle); color: var(--accent);
  font-size: 16px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}
.submitted .class-initial {
  background: color-mix(in srgb, #22c55e 12%, transparent);
  color: #15803d;
}
.class-info { flex: 1; min-width: 0; }
.class-name  { font-size: 15px; font-weight: 600; color: var(--tx-high); margin: 0 0 2px; }
.class-level { font-size: 11px; color: var(--tx-low); margin: 0; }

.class-card-bottom { display: flex; align-items: center; justify-content: space-between; }
.status-chip {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 11.5px; font-weight: 600; padding: 4px 9px; border-radius: 99px;
}
.submitted-chip {
  background: color-mix(in srgb, #22c55e 12%, transparent);
  color: #15803d;
  border: 1px solid color-mix(in srgb, #22c55e 25%, transparent);
}
.pending-chip {
  background: color-mix(in srgb, #f59e0b 10%, transparent);
  color: #d97706;
  border: 1px solid color-mix(in srgb, #f59e0b 25%, transparent);
}
:global(.card-arrow) { color: var(--tx-low); }

/* Empty */
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  text-align: center; padding: 56px 32px; gap: 10px;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 14px;
  background: var(--surface-2); color: var(--tx-low);
  display: flex; align-items: center; justify-content: center; margin-bottom: 4px;
}
.empty-title { font-size: 15px; font-weight: 600; color: var(--tx-high); margin: 0; }
.empty-body  { font-size: 13px; color: var(--tx-low); margin: 0; max-width: 340px; line-height: 1.55; }

/* Skeletons */
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position:  400px 0; }
}
.sk {
  background: linear-gradient(90deg, var(--surface-2) 25%, var(--border-subtle) 50%, var(--surface-2) 75%);
  background-size: 800px 100%; animation: shimmer 1.4s infinite linear; border-radius: 6px;
}
.skeleton-card {
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 12px; padding: 16px; height: 96px;
  display: flex; flex-direction: column; gap: 10px; pointer-events: none;
}
.sk-name  { height: 16px; width: 80px; }
.sk-badge { height: 22px; width: 110px; }
</style>
