<script lang="ts">
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { api } from "$api/client";
  import { schoolBranding } from "$stores/school";
  import { toast } from "$stores/toast";
  import { ArrowLeft, Save, CheckSquare, Square, Users, AlertTriangle } from "@lucide/svelte";

  interface Student {
    student_id: string; full_name: string; register_number: string | null;
    gender: string; term_enrollment_id: string; registered: boolean;
  }
  interface RegisterResponse {
    class_subject_id: string; class_name: string;
    subject_name: string; subject_code: string;
    term_name: string; year_name: string;
    students: Student[];
  }

  const classSubjectId = $page.params.class_subject_id;

  let data: RegisterResponse | null = null;
  let loading = true;
  let saving = false;
  let error = "";

  // Local selection state: term_enrollment_id → boolean
  let selected: Record<string, boolean> = {};

  onMount(async () => {
    try {
      const res = await api.get<RegisterResponse>(`/subject-registration/${classSubjectId}`);
      data = res.data;
      for (const s of data.students) {
        selected[s.term_enrollment_id] = s.registered;
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error = err?.response?.data?.detail ?? "Could not load student list.";
    } finally {
      loading = false;
    }
  });

  async function save() {
    saving = true;
    try {
      const enrolled = Object.entries(selected)
        .filter(([, v]) => v)
        .map(([id]) => id);
      await api.post(`/subject-registration/${classSubjectId}`, {
        term_enrollment_ids: enrolled,
      });
      toast.success(`Subject register saved — ${enrolled.length} student${enrolled.length !== 1 ? "s" : ""} registered`);
      goto("/dashboard");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err?.response?.data?.detail ?? "Failed to save.");
    } finally {
      saving = false;
    }
  }

  function toggleAll(val: boolean) {
    if (!data) return;
    for (const s of data.students) {
      selected[s.term_enrollment_id] = val;
    }
    selected = { ...selected };
  }

  $: registeredCount = Object.values(selected).filter(Boolean).length;
  $: totalCount = data?.students.length ?? 0;
  $: allSelected = totalCount > 0 && registeredCount === totalCount;
  $: noneSelected = registeredCount === 0;
</script>

<svelte:head>
  <title>
    {data ? `${data.subject_name} — ${data.class_name}` : "Subject Register"} — {$schoolBranding?.name ?? "TTEK SMS"}
  </title>
</svelte:head>

<a href="/dashboard" class="back-link"><ArrowLeft size={13} /> Dashboard</a>

{#if loading}
  <div class="loading">Loading student list…</div>

{:else if error}
  <div class="error-box"><AlertTriangle size={14} /> {error}</div>

{:else if data}
  <!-- Header -->
  <div class="reg-header">
    <div>
      <h1 class="reg-title">{data.subject_name}</h1>
      <p class="reg-sub">
        {data.class_name} · {data.term_name} · {data.year_name}
      </p>
      <p class="reg-hint">
        Select the students who are taking <strong>{data.subject_name}</strong> this term.
        Only selected students will be able to have scores entered for this subject.
      </p>
    </div>
    <div class="reg-stat">
      <span class="reg-count">{registeredCount}</span>
      <span class="reg-count-label">/ {totalCount} registered</span>
    </div>
  </div>

  {#if data.students.length === 0}
    <div class="empty-state">
      <div class="empty-icon"><Users size={24} /></div>
      <p class="empty-title">No students enrolled</p>
      <p class="empty-body">No students are enrolled in {data.class_name} for the current term.</p>
    </div>
  {:else}
    <!-- Toolbar -->
    <div class="toolbar">
      <button class="tool-btn" on:click={() => toggleAll(true)} disabled={allSelected}>
        <CheckSquare size={13} /> Select all
      </button>
      <button class="tool-btn" on:click={() => toggleAll(false)} disabled={noneSelected}>
        <Square size={13} /> Clear all
      </button>
    </div>

    <!-- Student list -->
    <div class="student-list">
      {#each data.students as student (student.term_enrollment_id)}
        {@const checked = selected[student.term_enrollment_id] ?? false}
        <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
        <div
          class="student-row"
          class:row-checked={checked}
          on:click={() => { selected[student.term_enrollment_id] = !checked; selected = { ...selected }; }}
        >
          <div class="check-box" class:checked>
            {#if checked}
              <CheckSquare size={17} />
            {:else}
              <Square size={17} />
            {/if}
          </div>
          <div class="s-avatar s-{student.gender.toLowerCase()}">
            {student.full_name.split(" ").map(w => w[0]).slice(0,2).join("")}
          </div>
          <div class="s-info">
            <p class="s-name">{student.full_name}</p>
            {#if student.register_number}
              <p class="s-reg">{student.register_number}</p>
            {/if}
          </div>
          <span class="s-gender">{student.gender === "MALE" ? "M" : "F"}</span>
        </div>
      {/each}
    </div>

    <!-- Save bar -->
    <div class="save-bar">
      <span class="save-summary">
        {registeredCount} of {totalCount} student{totalCount !== 1 ? "s" : ""} selected for {data.subject_name}
      </span>
      <button class="btn-save" on:click={save} disabled={saving}>
        <Save size={14} /> {saving ? "Saving…" : "Save Register"}
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

.loading { font-size: 13px; color: var(--tx-low); padding: 32px 0; }
.error-box {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; border-radius: 10px; font-size: 13px;
  background: color-mix(in srgb, #ef4444 10%, transparent);
  color: #dc2626; border: 1px solid color-mix(in srgb, #ef4444 25%, transparent);
}

/* Header */
.reg-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 16px; margin-bottom: 20px; flex-wrap: wrap;
}
.reg-title { font-size: 22px; font-weight: 800; color: var(--tx-high); margin: 0 0 4px; letter-spacing: -0.3px; }
.reg-sub   { font-size: 13px; color: var(--tx-low); margin: 0 0 8px; }
.reg-hint  { font-size: 13px; color: var(--tx-mid); margin: 0; line-height: 1.5; max-width: 520px; }
.reg-stat  { display: flex; align-items: baseline; gap: 4px; flex-shrink: 0; padding-top: 4px; }
.reg-count { font-size: 36px; font-weight: 800; color: var(--accent); line-height: 1; letter-spacing: -1px; }
.reg-count-label { font-size: 14px; color: var(--tx-low); }

/* Toolbar */
.toolbar { display: flex; gap: 8px; margin-bottom: 10px; }
.tool-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 12px; border-radius: 7px; font-size: 12px; font-weight: 500;
  border: 1px solid var(--border-subtle); background: var(--surface-1);
  color: var(--tx-mid); cursor: pointer; transition: all 0.1s;
}
.tool-btn:hover:not(:disabled) { background: var(--surface-2); color: var(--tx-high); }
.tool-btn:disabled { opacity: 0.4; cursor: default; }

/* Student list */
.student-list {
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 12px; overflow: hidden; box-shadow: var(--shadow-xs);
  margin-bottom: 16px;
}
.student-row {
  display: flex; align-items: center; gap: 12px;
  padding: 11px 16px; border-top: 1px solid var(--border-subtle);
  cursor: pointer; transition: background 0.1s;
  user-select: none;
}
.student-row:first-child { border-top: none; }
.student-row:hover { background: var(--surface-2); }
.student-row.row-checked { background: color-mix(in srgb, var(--accent) 4%, transparent); }
.student-row.row-checked:hover { background: color-mix(in srgb, var(--accent) 8%, transparent); }

.check-box { color: var(--tx-low); flex-shrink: 0; transition: color 0.1s; }
.check-box.checked { color: var(--accent); }

.s-avatar {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.s-male   { background: color-mix(in srgb,#3b82f6 12%,transparent); color:#1d4ed8; }
.s-female { background: color-mix(in srgb,#ec4899 12%,transparent); color:#be185d; }

.s-info { flex: 1; min-width: 0; }
.s-name { font-size: 13px; font-weight: 500; color: var(--tx-high); margin: 0 0 1px;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.s-reg  { font-size: 11px; font-family: monospace; color: var(--tx-low); margin: 0; }
.s-gender { font-size: 11px; font-weight: 600; color: var(--tx-low); flex-shrink: 0; }

/* Save bar */
.save-bar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; padding: 14px 18px; flex-wrap: wrap;
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 12px; box-shadow: var(--shadow-xs);
}
.save-summary { font-size: 13px; color: var(--tx-low); }
.btn-save {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 10px 20px; border-radius: 9px; font-size: 13px; font-weight: 600;
  background: var(--accent); color: var(--accent-fg, #fff);
  border: none; cursor: pointer; transition: opacity 0.15s;
}
.btn-save:hover:not(:disabled) { opacity: 0.88; }
.btn-save:disabled { opacity: 0.5; cursor: default; }

/* Empty */
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  text-align: center; padding: 56px 32px; gap: 10px;
}
.empty-icon {
  width: 52px; height: 52px; border-radius: 14px;
  background: var(--surface-2); color: var(--tx-low);
  display: flex; align-items: center; justify-content: center; margin-bottom: 4px;
}
.empty-title { font-size: 14px; font-weight: 600; color: var(--tx-high); margin: 0; }
.empty-body  { font-size: 13px; color: var(--tx-low); margin: 0; max-width: 320px; line-height: 1.55; }
</style>
