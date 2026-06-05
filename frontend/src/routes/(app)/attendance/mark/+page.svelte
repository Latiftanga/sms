<script lang="ts">
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { api } from "$api/client";
  import { schoolBranding } from "$stores/school";
  import { toast } from "$stores/toast";
  import {
    ArrowLeft, CheckCircle2, XCircle, Clock, MinusCircle,
    Save, Users, AlertTriangle,
  } from "@lucide/svelte";

  interface RegisterStudent {
    student_id: string; full_name: string; register_number: string | null;
    gender: string; term_enrollment_id: string;
    status: string | null; note: string | null;
  }
  interface RegisterResponse {
    calendar: { id: string; date: string; day_type: string; label: string | null };
    class_id: string; class_name: string;
    records: RegisterStudent[];
    is_submitted: boolean;
  }

  const classId = $page.url.searchParams.get("class_id") ?? "";
  const dateParam = $page.url.searchParams.get("date") ?? undefined;

  let register: RegisterResponse | null = null;
  let loading = true;
  let saving = false;
  let error = "";

  // Local attendance state: term_enrollment_id → status
  let statuses: Record<string, string> = {};

  const STATUS_OPTS = [
    { value: "PRESENT", label: "Present", icon: CheckCircle2, color: "green" },
    { value: "ABSENT",  label: "Absent",  icon: XCircle,      color: "red"   },
    { value: "LATE",    label: "Late",    icon: Clock,         color: "amber" },
    { value: "EXCUSED", label: "Excused", icon: MinusCircle,   color: "blue"  },
  ];

  onMount(async () => {
    if (!classId) { error = "No class selected."; loading = false; return; }
    try {
      const params: Record<string, string> = { class_id: classId };
      if (dateParam) params.target_date = dateParam;
      const { data } = await api.get<RegisterResponse>("/attendance/register", { params });
      register = data;
      // Pre-fill from existing records
      for (const s of data.records) {
        statuses[s.term_enrollment_id] = s.status ?? "PRESENT";
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error = err?.response?.data?.detail ?? "Could not load register.";
    } finally {
      loading = false;
    }
  });

  async function submit() {
    if (!register) return;
    saving = true;
    try {
      const records = register.records.map(s => ({
        term_enrollment_id: s.term_enrollment_id,
        status: statuses[s.term_enrollment_id] ?? "PRESENT",
      }));
      await api.post("/attendance/register", {
        class_id: classId,
        date: register.calendar.date,
        records,
      });
      toast.success(`Attendance saved — ${records.length} student${records.length !== 1 ? "s" : ""}`);
      goto("/attendance");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err?.response?.data?.detail ?? "Failed to save attendance.");
    } finally {
      saving = false;
    }
  }

  function markAll(status: string) {
    if (!register) return;
    for (const s of register.records) {
      statuses[s.term_enrollment_id] = status;
    }
    statuses = { ...statuses };
  }

  function fmtDate(s: string): string {
    return new Date(s).toLocaleDateString("en-GH", {
      weekday: "long", day: "numeric", month: "long", year: "numeric",
    });
  }

  $: presentCount = Object.values(statuses).filter(v => v === "PRESENT").length;
  $: absentCount  = Object.values(statuses).filter(v => v === "ABSENT").length;
  $: lateCount    = Object.values(statuses).filter(v => v === "LATE").length;
  $: excusedCount = Object.values(statuses).filter(v => v === "EXCUSED").length;
</script>

<svelte:head>
  <title>Mark Attendance{register ? ` — ${register.class_name}` : ""} — {$schoolBranding?.name ?? "TTEK SMS"}</title>
</svelte:head>

<a href="/attendance" class="back-link"><ArrowLeft size={13} /> Attendance</a>

{#if loading}
  <div class="loading-state">Loading register…</div>

{:else if error}
  <div class="error-box"><AlertTriangle size={14} /> {error}</div>

{:else if register}
  <!-- Header -->
  <div class="mark-header">
    <div>
      <h1 class="mark-title">{register.class_name}</h1>
      <p class="mark-date">{fmtDate(register.calendar.date)}</p>
    </div>
    <div class="header-stats">
      <span class="stat-chip green">{presentCount} present</span>
      <span class="stat-chip red">{absentCount} absent</span>
      {#if lateCount > 0}<span class="stat-chip amber">{lateCount} late</span>{/if}
      {#if excusedCount > 0}<span class="stat-chip blue">{excusedCount} excused</span>{/if}
    </div>
  </div>

  {#if register.is_submitted}
    <div class="resubmit-notice">
      <CheckCircle2 size={14} /> Attendance already submitted today — you can update it below.
    </div>
  {/if}

  {#if register.records.length === 0}
    <div class="empty-state">
      <div class="empty-icon"><Users size={24} /></div>
      <p class="empty-title">No students enrolled</p>
      <p class="empty-body">This class has no students enrolled in the current term.</p>
    </div>
  {:else}
    <!-- Quick-mark toolbar -->
    <div class="toolbar">
      <span class="toolbar-label">Mark all as:</span>
      {#each STATUS_OPTS as opt}
        <button class="quick-btn quick-{opt.color}" on:click={() => markAll(opt.value)}>
          <svelte:component this={opt.icon} size={12} /> {opt.label}
        </button>
      {/each}
    </div>

    <!-- Register table -->
    <div class="register-card">
      <div class="register-head">
        <span class="rh-student">Student</span>
        {#each STATUS_OPTS as opt}
          <span class="rh-status rh-{opt.color}">{opt.label}</span>
        {/each}
      </div>

      {#each register.records as student (student.term_enrollment_id)}
        {@const current = statuses[student.term_enrollment_id] ?? "PRESENT"}
        <div class="register-row" class:row-absent={current === "ABSENT"}>
          <div class="student-cell">
            <div class="s-avatar s-{student.gender.toLowerCase()}">
              {student.full_name.split(" ").map(w => w[0]).slice(0,2).join("")}
            </div>
            <div class="s-info">
              <p class="s-name">{student.full_name}</p>
              {#if student.register_number}
                <p class="s-reg">{student.register_number}</p>
              {/if}
            </div>
          </div>

          <div class="status-radios">
            {#each STATUS_OPTS as opt}
              <label
                class="radio-label radio-{opt.color}"
                class:radio-selected={current === opt.value}
                title={opt.label}
              >
                <input
                  type="radio"
                  name="status_{student.term_enrollment_id}"
                  value={opt.value}
                  bind:group={statuses[student.term_enrollment_id]}
                  style="display:none"
                />
                <svelte:component this={opt.icon} size={18} />
              </label>
            {/each}
          </div>
        </div>
      {/each}
    </div>

    <!-- Submit -->
    <div class="submit-bar">
      <span class="submit-summary">
        {register.records.length} student{register.records.length !== 1 ? "s" : ""}
        · {presentCount} present · {absentCount} absent
        {#if lateCount > 0}· {lateCount} late{/if}
      </span>
      <button class="btn-submit" on:click={submit} disabled={saving}>
        <Save size={14} /> {saving ? "Saving…" : "Save Attendance"}
      </button>
    </div>
  {/if}
{/if}

<style>
.back-link {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; font-weight: 500; color: var(--tx-low);
  text-decoration: none; margin-bottom: 18px; transition: color 0.12s;
}
.back-link:hover { color: var(--accent); }

.loading-state { font-size: 13px; color: var(--tx-low); padding: 32px 0; }
.error-box {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; border-radius: 10px; font-size: 13px;
  background: color-mix(in srgb, #ef4444 10%, transparent);
  color: #dc2626; border: 1px solid color-mix(in srgb, #ef4444 25%, transparent);
}

/* Header */
.mark-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 12px; margin-bottom: 14px; flex-wrap: wrap;
}
.mark-title { font-size: 20px; font-weight: 800; color: var(--tx-high); margin: 0 0 4px; letter-spacing: -0.3px; }
.mark-date  { font-size: 13px; color: var(--tx-low); margin: 0; }
.header-stats { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }

.stat-chip {
  display: inline-flex; align-items: center;
  font-size: 12px; font-weight: 600; padding: 3px 9px; border-radius: 99px;
}
.stat-chip.green { background: color-mix(in srgb,#22c55e 12%,transparent); color:#15803d; border:1px solid color-mix(in srgb,#22c55e 25%,transparent); }
.stat-chip.red   { background: color-mix(in srgb,#ef4444 12%,transparent); color:#b91c1c; border:1px solid color-mix(in srgb,#ef4444 25%,transparent); }
.stat-chip.amber { background: color-mix(in srgb,#f59e0b 12%,transparent); color:#b45309; border:1px solid color-mix(in srgb,#f59e0b 25%,transparent); }
.stat-chip.blue  { background: color-mix(in srgb,#3b82f6 12%,transparent); color:#1d4ed8; border:1px solid color-mix(in srgb,#3b82f6 25%,transparent); }

.resubmit-notice {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 14px;
  background: color-mix(in srgb, #22c55e 8%, transparent);
  color: #15803d; border: 1px solid color-mix(in srgb, #22c55e 20%, transparent);
}

/* Toolbar */
.toolbar {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  margin-bottom: 12px;
}
.toolbar-label { font-size: 12px; color: var(--tx-low); font-weight: 500; }
.quick-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 5px 10px; border-radius: 7px; font-size: 12px; font-weight: 500;
  border: 1px solid var(--border-subtle); background: var(--surface-1);
  cursor: pointer; transition: all 0.1s;
}
.quick-green:hover { background: color-mix(in srgb,#22c55e 12%,transparent); color:#15803d; border-color: color-mix(in srgb,#22c55e 25%,transparent); }
.quick-red:hover   { background: color-mix(in srgb,#ef4444 12%,transparent); color:#b91c1c; border-color: color-mix(in srgb,#ef4444 25%,transparent); }
.quick-amber:hover { background: color-mix(in srgb,#f59e0b 12%,transparent); color:#b45309; border-color: color-mix(in srgb,#f59e0b 25%,transparent); }
.quick-blue:hover  { background: color-mix(in srgb,#3b82f6 12%,transparent); color:#1d4ed8; border-color: color-mix(in srgb,#3b82f6 25%,transparent); }

/* Register */
.register-card {
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 12px; overflow: hidden; box-shadow: var(--shadow-xs);
  margin-bottom: 16px;
}
.register-head {
  display: flex; align-items: center;
  padding: 10px 16px; background: var(--surface-0);
  border-bottom: 1px solid var(--border-subtle);
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--tx-low);
}
.rh-student { flex: 1; }
.rh-status  { width: 68px; text-align: center; }
.rh-green   { color: #15803d; }
.rh-red     { color: #b91c1c; }
.rh-amber   { color: #b45309; }
.rh-blue    { color: #1d4ed8; }

@media (max-width: 520px) {
  .rh-status { width: 48px; font-size: 9px; }
}

.register-row {
  display: flex; align-items: center;
  padding: 10px 16px; border-top: 1px solid var(--border-subtle);
  transition: background 0.1s;
}
.register-row:first-of-type { border-top: none; }
.register-row:hover { background: var(--surface-2); }
.register-row.row-absent { opacity: 0.7; }

.student-cell { flex: 1; display: flex; align-items: center; gap: 10px; min-width: 0; }
.s-avatar {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.s-male   { background: color-mix(in srgb,#3b82f6 12%,transparent); color: #1d4ed8; }
.s-female { background: color-mix(in srgb,#ec4899 12%,transparent); color: #be185d; }
.s-info { min-width: 0; }
.s-name { font-size: 13px; font-weight: 500; color: var(--tx-high); margin: 0 0 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.s-reg  { font-size: 11px; font-family: monospace; color: var(--tx-low); margin: 0; }

.status-radios { display: flex; gap: 4px; flex-shrink: 0; }

.radio-label {
  width: 36px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; border: 2px solid transparent;
  color: var(--tx-low); transition: all 0.12s;
}
.radio-label:hover { background: var(--surface-2); color: var(--tx-mid); }
.radio-green.radio-selected  { background: color-mix(in srgb,#22c55e 15%,transparent); color:#15803d; border-color:#22c55e; }
.radio-red.radio-selected    { background: color-mix(in srgb,#ef4444 15%,transparent); color:#b91c1c; border-color:#ef4444; }
.radio-amber.radio-selected  { background: color-mix(in srgb,#f59e0b 15%,transparent); color:#b45309; border-color:#f59e0b; }
.radio-blue.radio-selected   { background: color-mix(in srgb,#3b82f6 15%,transparent); color:#1d4ed8; border-color:#3b82f6; }

@media (max-width: 520px) {
  .radio-label { width: 30px; height: 30px; border-radius: 6px; }
}

/* Submit bar */
.submit-bar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; padding: 14px 18px; flex-wrap: wrap;
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 12px; box-shadow: var(--shadow-xs);
}
.submit-summary { font-size: 13px; color: var(--tx-low); }
.btn-submit {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 10px 20px; border-radius: 9px; font-size: 13px; font-weight: 600;
  background: var(--accent); color: var(--accent-fg, #fff);
  border: none; cursor: pointer; transition: opacity 0.15s;
}
.btn-submit:hover:not(:disabled) { opacity: 0.88; }
.btn-submit:disabled { opacity: 0.5; cursor: default; }

/* Empty */
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
.empty-body  { font-size: 13px; color: var(--tx-low); margin: 0; max-width: 320px; line-height: 1.55; }
</style>
