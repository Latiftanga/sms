<script lang="ts">
  import { page } from "$app/stores";
  import { onMount } from "svelte";
  import { api } from "$api/client";
  import { toast } from "$stores/toast";
  import { confirmDialog } from "$stores/confirm";
  import Button  from "$components/ui/Button.svelte";
  import Badge   from "$components/ui/Badge.svelte";
  import Spinner from "$components/ui/Spinner.svelte";
  import {
    ArrowLeft, UserCheck, Users, GraduationCap, Pencil,
    Check, X, AlertCircle, Loader2, Search, UserX,
    CalendarDays, BookOpen, Hash, ToggleLeft, ToggleRight,
  } from "@lucide/svelte";

  // ── Types ─────────────────────────────────────────────────────────
  interface ClassTeacher { staff_member_id: string; staff_name: string; }
  interface ClassDetail {
    id: string; name: string; level: string; year: number | null;
    education_level: string; stream: string | null; is_active: boolean;
    learning_area: { name: string; short_name: string | null } | null;
    class_teacher: ClassTeacher | null;
    student_count: number;
    current_year_id: string | null;
    current_year_name: string | null;
  }
  interface StaffOption {
    id: string; first_name: string; last_name: string;
    designation: string | null;
  }

  const EDU_LABELS: Record<string, string> = {
    EARLY_CHILDHOOD: "Early Childhood", BASIC: "Basic",
    SHS: "Senior High School", JHS: "Junior High School", TECHNICAL: "Technical",
  };

  // ── State ──────────────────────────────────────────────────────────
  let cls: ClassDetail | null = null;
  let loading = true;
  let loadError = "";

  // Teacher assignment
  let assigningTeacher = false;
  let staffList: StaffOption[] = [];
  let staffLoading = false;
  let staffSearch = "";
  let selectedStaffId = "";
  let saving = false;
  let saveError = "";
  let removing = false;
  let togglingActive = false;

  // Edit stream
  let editingStream = false;
  let streamValue = "";
  let savingStream = false;

  function apiError(e: unknown): string {
    const err = e as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail ?? "Something went wrong.";
  }

  async function load() {
    loading = true; loadError = "";
    try {
      const { data } = await api.get<ClassDetail>(`/settings/classes/${$page.params.id}/detail`);
      cls = data;
      streamValue = data.stream ?? "";
    } catch (e) { loadError = apiError(e); }
    finally { loading = false; }
  }

  async function loadStaff() {
    staffLoading = true;
    try {
      const { data } = await api.get("/staff", {
        params: { category: "TEACHING", is_active: true, limit: 200 },
      });
      staffList = data.items ?? [];
    } catch { staffList = []; }
    finally { staffLoading = false; }
  }

  function openAssign() {
    assigningTeacher = true;
    selectedStaffId = cls?.class_teacher?.staff_member_id ?? "";
    saveError = ""; staffSearch = "";
    if (staffList.length === 0) loadStaff();
  }

  async function saveTeacher() {
    if (!selectedStaffId) { saveError = "Please select a staff member."; return; }
    saving = true; saveError = "";
    try {
      const { data } = await api.put<ClassDetail>(
        `/settings/classes/${$page.params.id}/teacher`,
        { staff_member_id: selectedStaffId },
      );
      cls = data; assigningTeacher = false;
      toast.success("Class teacher assigned");
    } catch (e) { saveError = apiError(e); }
    finally { saving = false; }
  }

  async function removeTeacher() {
    const ok = await confirmDialog.show({
      title: "Remove class teacher?",
      message: `${cls?.class_teacher?.staff_name} will no longer be the class teacher for ${cls?.name} this academic year.`,
      variant: "danger", confirmLabel: "Remove",
    });
    if (!ok) return;
    removing = true;
    try {
      await api.delete(`/settings/classes/${$page.params.id}/teacher`);
      cls = { ...cls!, class_teacher: null };
      toast.success("Class teacher removed");
    } catch (e) { toast.error(apiError(e)); }
    finally { removing = false; }
  }

  async function saveStream() {
    savingStream = true;
    try {
      await api.patch(`/settings/classes/${$page.params.id}`, {
        stream: streamValue.trim() || null,
      });
      cls = { ...cls!, stream: streamValue.trim() || null };
      editingStream = false;
      toast.success("Stream updated");
    } catch (e) { toast.error(apiError(e)); }
    finally { savingStream = false; }
  }

  async function toggleActive() {
    if (!cls) return;
    const next = !cls.is_active;
    togglingActive = true;
    try {
      await api.patch(`/settings/classes/${$page.params.id}`, { is_active: next });
      cls = { ...cls, is_active: next };
      toast.success(next ? "Class activated" : "Class deactivated");
    } catch (e) { toast.error(apiError(e)); }
    finally { togglingActive = false; }
  }

  $: filteredStaff = staffSearch
    ? staffList.filter(s =>
        `${s.first_name} ${s.last_name}`.toLowerCase().includes(staffSearch.toLowerCase())
      )
    : staffList;

  $: selectedStaffName = staffList.find(s => s.id === selectedStaffId)
    ? `${staffList.find(s => s.id === selectedStaffId)!.first_name} ${staffList.find(s => s.id === selectedStaffId)!.last_name}`
    : "";

  onMount(load);
</script>

<svelte:head>
  <title>{cls?.name ?? "Class"} — TTEK-SIS</title>
</svelte:head>

<div class="root">

  <!-- Breadcrumb -->
  <a href="/academic?tab=classes" class="back">
    <ArrowLeft size={13} /><span>Academic</span><span class="sep">/</span><span class="bc-page">Classes</span>
  </a>

  {#if loading}
    <div class="pg-center"><Spinner size={28} /></div>

  {:else if loadError}
    <div class="pg-center">
      <div class="err-state">
        <AlertCircle size={24} />
        <p>{loadError}</p>
        <Button on:click={load}>Retry</Button>
      </div>
    </div>

  {:else if cls}

    <!-- ── Hero header ──────────────────────────────────────────────── -->
    <div class="hero" class:hero-inactive={!cls.is_active}>
      <div class="hero-body">
        <div class="hero-tags">
          <span class="edu-tag edu-{cls.education_level.toLowerCase()}">{EDU_LABELS[cls.education_level] ?? cls.education_level}</span>
          {#if cls.current_year_name}
            <span class="year-tag"><CalendarDays size={11} />{cls.current_year_name}</span>
          {:else}
            <span class="warn-tag"><AlertCircle size={11} />No current year</span>
          {/if}
          {#if !cls.is_active}
            <span class="inactive-tag">Inactive</span>
          {/if}
        </div>
        <h1 class="hero-title">{cls.name}</h1>
        {#if cls.learning_area}
          <p class="hero-sub"><BookOpen size={12} />{cls.learning_area.name}{cls.learning_area.short_name ? ` · ${cls.learning_area.short_name}` : ""}</p>
        {/if}
      </div>

      <!-- Quick stats -->
      <div class="hero-stats">
        <div class="hstat">
          <span class="hstat-val">{cls.student_count}</span>
          <span class="hstat-label">Students</span>
        </div>
        <div class="hstat-div"></div>
        <div class="hstat">
          <span class="hstat-val">{cls.class_teacher ? "Assigned" : "—"}</span>
          <span class="hstat-label">Class Teacher</span>
        </div>
        <div class="hstat-div"></div>
        <div class="hstat">
          <span class="hstat-val">{cls.stream ?? "None"}</span>
          <span class="hstat-label">Stream</span>
        </div>
      </div>
    </div>

    <!-- ── Layout ───────────────────────────────────────────────────── -->
    <div class="layout">

      <!-- ══ Main column ════════════════════════════════════════════ -->
      <div class="main-col">

        <!-- Class Teacher -->
        <div class="card">
          <!-- Single-row display: icon · label · teacher (or unassigned) · action -->
          <div class="teacher-row">
            <div class="card-icon"><UserCheck size={15} /></div>
            <span class="teacher-row-label">Class Teacher</span>

            {#if cls.class_teacher}
              <div class="teacher-pill">
                <span class="teacher-pill-av">{cls.class_teacher.staff_name.charAt(0).toUpperCase()}</span>
                <span class="teacher-pill-name">{cls.class_teacher.staff_name}</span>
              </div>
              {#if !assigningTeacher}
                <div class="teacher-acts">
                  <button class="tact-btn" on:click={openAssign} title="Change teacher"><Pencil size={12} /></button>
                  <button class="tact-btn tact-danger" on:click={removeTeacher} disabled={removing} title="Remove teacher">
                    {#if removing}<Loader2 size={12} class="spin" />{:else}<UserX size={12} />{/if}
                  </button>
                </div>
              {/if}
            {:else}
              <span class="teacher-unassigned">Unassigned</span>
              {#if !assigningTeacher && cls.current_year_id}
                <button class="card-head-action" on:click={openAssign}>
                  <UserCheck size={12} /> Assign
                </button>
              {:else if !cls.current_year_id}
                <span class="teacher-no-year">No active year</span>
              {/if}
            {/if}

            {#if assigningTeacher}
              <button class="tact-btn" on:click={() => { assigningTeacher = false; saveError = ""; }} title="Cancel">
                <X size={13} />
              </button>
            {/if}
          </div>

          <!-- Assignment panel — only shown when actively assigning -->
          {#if assigningTeacher}
            <div class="assign-panel">
              <div class="assign-search">
                <Search size={13} style="position:absolute;left:10px;top:50%;transform:translateY(-50%);color:var(--tx-low);pointer-events:none;" />
                <input
                  class="assign-input"
                  placeholder="Search teaching staff…"
                  bind:value={staffSearch}
                  autofocus
                />
              </div>

              {#if staffLoading}
                <div class="assign-loading"><Loader2 size={15} class="spin" /></div>
              {:else if filteredStaff.length === 0}
                <p class="assign-empty">No teaching staff found.</p>
              {:else}
                <div class="staff-list" role="listbox">
                  {#each filteredStaff as s (s.id)}
                    <button
                      class="staff-item"
                      class:is-selected={selectedStaffId === s.id}
                      role="option"
                      aria-selected={selectedStaffId === s.id}
                      on:click={() => { selectedStaffId = s.id; saveError = ""; }}
                    >
                      <span class="staff-av">{s.first_name.charAt(0)}</span>
                      <span class="staff-name">{s.first_name} {s.last_name}</span>
                      {#if s.designation}
                        <span class="staff-desig">{s.designation.replace(/_/g, " ").toLowerCase()}</span>
                      {/if}
                      {#if selectedStaffId === s.id}
                        <Check size={13} style="color:var(--accent);flex-shrink:0;margin-left:auto;" />
                      {/if}
                    </button>
                  {/each}
                </div>
              {/if}

              {#if saveError}
                <p class="assign-err"><AlertCircle size={12} />{saveError}</p>
              {/if}

              <div class="assign-footer">
                <Button loading={saving} disabled={!selectedStaffId} on:click={saveTeacher}>
                  {saving ? "Saving…" : "Confirm"}
                </Button>
                <Button variant="ghost" on:click={() => { assigningTeacher = false; saveError = ""; }}>Cancel</Button>
              </div>
            </div>
          {/if}
        </div>

        <!-- Students -->
        <div class="card">
          <div class="card-head">
            <div class="card-icon"><Users size={15} /></div>
            <div class="card-head-text">
              <span class="card-title">Students</span>
              <span class="card-sub">Enrolled in {cls.current_year_name ?? "the current academic year"}</span>
            </div>
          </div>
          <div class="card-body">
            <div class="enroll-row">
              <div class="enroll-count">
                <span class="enroll-num">{cls.student_count}</span>
                <span class="enroll-word">student{cls.student_count !== 1 ? "s" : ""} enrolled</span>
              </div>
              <p class="enroll-hint">
                Enroll and manage students from the <strong>Students</strong> module.
              </p>
            </div>
          </div>
        </div>

      </div><!-- /main-col -->

      <!-- ══ Sidebar ════════════════════════════════════════════════ -->
      <div class="side-col">

        <div class="card">
          <div class="card-head">
            <div class="card-icon"><GraduationCap size={15} /></div>
            <div class="card-head-text">
              <span class="card-title">Class Details</span>
            </div>
          </div>
          <div class="card-body no-pad">

            <div class="info-row">
              <span class="info-label">Level</span>
              <span class="info-val">{cls.level}{cls.year ? ` ${cls.year}` : ""}</span>
            </div>

            {#if cls.learning_area}
              <div class="info-row">
                <span class="info-label">Programme</span>
                <span class="info-val">{cls.learning_area.name}</span>
              </div>
            {/if}

            <div class="info-row">
              <span class="info-label">Stream</span>
              {#if editingStream}
                <div class="stream-edit">
                  <input
                    class="stream-inp"
                    bind:value={streamValue}
                    placeholder="A, Gold, Blue…"
                    on:keydown={e => e.key === "Enter" && saveStream()}
                  />
                  <button class="iact ok" on:click={saveStream} disabled={savingStream} title="Save">
                    {#if savingStream}<Loader2 size={12} class="spin" />{:else}<Check size={12} />{/if}
                  </button>
                  <button class="iact" on:click={() => { editingStream = false; streamValue = cls?.stream ?? ""; }} title="Cancel">
                    <X size={12} />
                  </button>
                </div>
              {:else}
                <div class="info-val-row">
                  {#if cls.stream}
                    <span class="info-val">{cls.stream}</span>
                  {:else}
                    <span class="info-val info-muted">None</span>
                  {/if}
                  <button class="iact" on:click={() => { editingStream = true; streamValue = cls?.stream ?? ""; }} title="Edit stream">
                    <Pencil size={12} />
                  </button>
                </div>
              {/if}
            </div>

            <div class="info-row info-row-last">
              <span class="info-label">Status</span>
              <div class="status-toggle">
                {#if cls.is_active}
                  <span class="sdot active"></span><span class="sval">Active</span>
                {:else}
                  <span class="sdot inactive"></span><span class="sval muted">Inactive</span>
                {/if}
                <button
                  class="toggle-status"
                  class:is-active={cls.is_active}
                  on:click={toggleActive}
                  disabled={togglingActive}
                  title={cls.is_active ? "Deactivate class" : "Activate class"}
                >
                  {#if togglingActive}
                    <Loader2 size={13} class="spin" />
                  {:else if cls.is_active}
                    <ToggleRight size={18} />
                  {:else}
                    <ToggleLeft size={18} />
                  {/if}
                </button>
              </div>
            </div>

          </div>
        </div>

      </div><!-- /side-col -->

    </div><!-- /layout -->

  {/if}
</div>

<style>
/* ── Root ────────────────────────────────────────────────────────── */
.root {
  display: flex; flex-direction: column;
  min-height: 100%; padding-bottom: 48px;
}

/* ── Breadcrumb ──────────────────────────────────────────────────── */
.back {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12.5px; color: var(--tx-low); text-decoration: none;
  margin-bottom: 22px; transition: color 0.12s;
}
.back:hover { color: var(--accent); }
.sep { color: var(--border-strong); margin: 0 1px; }
.bc-page { color: var(--tx-mid); }

/* ── Page center (loading/error) ─────────────────────────────────── */
.pg-center {
  display: flex; justify-content: center; align-items: center;
  min-height: 240px;
}
.err-state {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  color: var(--tx-low); text-align: center;
}
.err-state p { margin: 0; font-size: 13.5px; }

/* ── Hero ────────────────────────────────────────────────────────── */
.hero {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 22px 24px;
  margin-bottom: 20px;
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 20px; flex-wrap: wrap;
}
.hero-inactive { opacity: 0.75; }

.hero-body { display: flex; flex-direction: column; gap: 6px; min-width: 0; }

.hero-tags {
  display: flex; align-items: center; gap: 7px; flex-wrap: wrap;
  margin-bottom: 4px;
}

.edu-tag {
  font-size: 11px; font-weight: 600;
  padding: 2px 9px; border-radius: 10px;
  letter-spacing: 0.02em;
}
.edu-early_childhood { background: color-mix(in srgb,#f59e0b 14%,transparent); color:#b45309; border: 1px solid color-mix(in srgb,#f59e0b 25%,transparent); }
.edu-basic           { background: color-mix(in srgb,#3b82f6 14%,transparent); color:#1d4ed8; border: 1px solid color-mix(in srgb,#3b82f6 25%,transparent); }
.edu-shs             { background: color-mix(in srgb,#8b5cf6 14%,transparent); color:#6d28d9; border: 1px solid color-mix(in srgb,#8b5cf6 25%,transparent); }

.year-tag {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11.5px; color: var(--tx-low);
  background: var(--surface-2); border: 1px solid var(--border-subtle);
  padding: 2px 8px; border-radius: 10px;
}
.warn-tag {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11.5px; color: var(--warn-text);
  background: var(--warn-bg); border: 1px solid color-mix(in srgb, var(--warn-text) 20%, transparent);
  padding: 2px 8px; border-radius: 10px;
}
.inactive-tag {
  font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px;
  background: var(--surface-2); color: var(--tx-low);
  border: 1px solid var(--border-subtle);
}

.hero-title {
  font-size: 2rem; font-weight: 800;
  color: var(--tx-high); margin: 0;
  line-height: 1.1; letter-spacing: -0.025em;
}

.hero-sub {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 13px; color: var(--tx-low); margin: 0; margin-top: 2px;
}

/* Hero stats */
.hero-stats {
  display: flex; align-items: center; gap: 0;
  background: var(--surface-0);
  border: 1px solid var(--border-subtle);
  border-radius: 10px; overflow: hidden;
  flex-shrink: 0; align-self: center;
}
.hstat {
  display: flex; flex-direction: column; align-items: center;
  padding: 12px 20px; gap: 2px; min-width: 80px;
}
.hstat-val { font-size: 15px; font-weight: 700; color: var(--tx-high); white-space: nowrap; }
.hstat-label { font-size: 10.5px; color: var(--tx-low); text-transform: uppercase; letter-spacing: 0.05em; }
.hstat-div { width: 1px; background: var(--border-subtle); align-self: stretch; }

/* ── Layout ──────────────────────────────────────────────────────── */
.layout {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 16px;
  align-items: start;
}
@media (max-width: 700px) {
  .layout { grid-template-columns: 1fr; }
  .hero-stats { align-self: flex-start; }
  .hstat { padding: 10px 14px; min-width: 60px; }
}

/* ── Cards ───────────────────────────────────────────────────────── */
.card {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 12px; overflow: hidden;
  margin-bottom: 16px;
}
.card:last-child { margin-bottom: 0; }

.card-head {
  display: flex; align-items: center; gap: 11px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-0);
}
.card-icon {
  width: 30px; height: 30px; border-radius: 8px;
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  color: var(--accent);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.card-head-text {
  display: flex; flex-direction: column; gap: 1px; flex: 1; min-width: 0;
}
.card-title { font-size: 13px; font-weight: 600; color: var(--tx-high); }
.card-sub   { font-size: 11.5px; color: var(--tx-low); }
.card-head-action {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 10px; border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: transparent; color: var(--tx-mid);
  font-size: 12px; font-weight: 500; cursor: pointer;
  transition: background 0.1s, color 0.1s, border-color 0.1s;
  flex-shrink: 0;
}
.card-head-action:hover {
  background: var(--accent-subtle); color: var(--accent);
  border-color: color-mix(in srgb, var(--accent) 25%, transparent);
}

.card-body { padding: 16px 18px; }
.no-pad .card-body,
.card-body.no-pad { padding: 0; }
.no-pad { padding: 0; }

/* ── Teacher: assigned view ──────────────────────────────────────── */
.teacher-card {
  display: flex; align-items: center; gap: 14px;
  padding: 4px 0;
}
/* ── Teacher compact row ─────────────────────────────────────────── */
.teacher-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; flex-wrap: wrap;
}
.teacher-row-label {
  font-size: 13px; font-weight: 600; color: var(--tx-high); flex-shrink: 0;
}
.teacher-pill {
  display: inline-flex; align-items: center; gap: 7px;
  background: color-mix(in srgb, var(--accent) 8%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
  border-radius: 20px; padding: 3px 10px 3px 4px;
  flex-shrink: 0;
}
.teacher-pill-av {
  width: 22px; height: 22px; border-radius: 50%;
  background: color-mix(in srgb, var(--accent) 18%, transparent);
  color: var(--accent);
  font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.teacher-pill-name { font-size: 13px; font-weight: 500; color: var(--tx-high); }
.teacher-unassigned {
  font-size: 12.5px; color: var(--tx-low); flex-shrink: 0;
}
.teacher-no-year {
  font-size: 11.5px; color: var(--tx-low);
  background: var(--surface-2); border: 1px solid var(--border-subtle);
  padding: 2px 8px; border-radius: 6px; flex-shrink: 0;
}
.teacher-acts { display: flex; gap: 2px; margin-left: auto; flex-shrink: 0; }
.tact-btn {
  width: 28px; height: 28px; border-radius: 6px;
  border: none; background: transparent;
  color: var(--tx-low); display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: background 0.1s, color 0.1s;
  flex-shrink: 0;
}
.tact-btn:hover { background: var(--surface-2); color: var(--tx-high); }
.tact-btn.tact-danger:hover { background: var(--err-bg); color: var(--err-text); }
.tact-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Assignment panel ────────────────────────────────────────────── */
.assign-panel {
  display: flex; flex-direction: column; gap: 8px;
  padding: 0 14px 14px; border-top: 1px solid var(--border-subtle);
  padding-top: 12px;
}

.assign-search {
  position: relative; display: flex; align-items: center;
}
.assign-input {
  width: 100%; height: 34px;
  padding: 0 12px 0 34px;
  border: 1px solid var(--border-strong); border-radius: 7px;
  background: var(--surface-0); color: var(--tx-high);
  font-size: 13px; font-family: inherit; outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.assign-input::placeholder { color: var(--tx-placeholder); }
.assign-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent);
}

.assign-loading {
  display: flex; justify-content: center; padding: 14px;
  color: var(--tx-low);
}
.assign-empty {
  font-size: 12.5px; color: var(--tx-low); text-align: center;
  padding: 12px 0; margin: 0;
}

.staff-list {
  max-height: 200px; overflow-y: auto;
  border: 1px solid var(--border-subtle); border-radius: 7px;
  background: var(--surface-0);
}
.staff-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 8px 12px;
  background: none; border: none;
  border-bottom: 1px solid var(--border-subtle);
  cursor: pointer; text-align: left;
  transition: background 0.1s;
}
.staff-item:last-child { border-bottom: none; }
.staff-item:hover { background: var(--surface-1); }
.staff-item.is-selected { background: color-mix(in srgb, var(--accent) 7%, transparent); }
.staff-av {
  width: 26px; height: 26px; border-radius: 6px;
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  color: var(--accent); font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.staff-name { font-size: 13px; font-weight: 500; color: var(--tx-high); flex: 1; }
.staff-desig { font-size: 11px; color: var(--tx-low); text-transform: capitalize; flex-shrink: 0; }

.assign-err {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: var(--err-text); margin: 0;
}
.assign-footer { display: flex; gap: 8px; }

/* ── Students card ───────────────────────────────────────────────── */
.enroll-row {
  display: flex; flex-direction: column; gap: 8px;
}
.enroll-count { display: flex; align-items: baseline; gap: 8px; }
.enroll-num {
  font-size: 2.8rem; font-weight: 800;
  color: var(--tx-high); line-height: 1;
  letter-spacing: -0.04em;
}
.enroll-word { font-size: 14px; color: var(--tx-low); }
.enroll-hint { font-size: 12.5px; color: var(--tx-low); margin: 0; line-height: 1.5; }
.enroll-hint strong { color: var(--tx-mid); }

/* ── Info rows (sidebar) ─────────────────────────────────────────── */
.info-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 10px; padding: 10px 16px;
  border-bottom: 1px solid var(--border-subtle);
}
.info-row-last { border-bottom: none; }
.info-label {
  font-size: 11.5px; font-weight: 600; color: var(--tx-low);
  text-transform: uppercase; letter-spacing: 0.05em; flex-shrink: 0;
}
.info-val {
  font-size: 13px; font-weight: 500; color: var(--tx-high); text-align: right;
}
.info-muted { color: var(--tx-low); font-weight: 400; }
.info-val-row { display: flex; align-items: center; gap: 4px; }

/* ── Stream editing ──────────────────────────────────────────────── */
.stream-edit { display: flex; align-items: center; gap: 4px; }
.stream-inp {
  height: 28px; width: 100px; padding: 0 8px;
  border: 1px solid var(--border-strong); border-radius: 5px;
  background: var(--surface-0); color: var(--tx-high);
  font-size: 13px; font-family: inherit; outline: none;
}
.stream-inp:focus { border-color: var(--accent); }

/* ── Icon action buttons ─────────────────────────────────────────── */
.iact {
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border-radius: 6px;
  background: none; border: none; cursor: pointer;
  color: var(--tx-low); transition: background 0.1s, color 0.1s;
  flex-shrink: 0;
}
.iact:hover { background: var(--surface-2); color: var(--tx-high); }
.iact.ok:hover { background: color-mix(in srgb, var(--accent) 10%, transparent); color: var(--accent); }
.iact:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Status toggle ───────────────────────────────────────────────── */
.status-toggle { display: flex; align-items: center; gap: 6px; }
.sdot {
  width: 7px; height: 7px; border-radius: 50%;
}
.sdot.active   { background: var(--ok-dot); }
.sdot.inactive { background: var(--border-strong); }
.sval { font-size: 12.5px; font-weight: 500; color: var(--tx-high); }
.sval.muted { color: var(--tx-low); }
.toggle-status {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 6px;
  background: none; border: none; cursor: pointer;
  color: var(--tx-low); transition: color 0.12s, background 0.12s;
  margin-left: 2px;
}
.toggle-status:hover { background: var(--surface-2); color: var(--tx-high); }
.toggle-status.is-active { color: var(--accent); }
.toggle-status:disabled { opacity: 0.4; cursor: not-allowed; }

:global(.spin) { animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
