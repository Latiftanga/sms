<script lang="ts">
  import { page } from "$app/stores";
  import { onMount } from "svelte";
  import { api } from "$api/client";
  import { auth } from "$stores/auth";
  import { schoolBranding } from "$stores/school";
  import Badge from "$components/ui/Badge.svelte";
  import {
    ArrowLeft, Edit2, GraduationCap, Users,
    BookOpen, Plus, Trash2, Check, X, Phone, Mail,
  } from "@lucide/svelte";

  interface Guardian { id: string; first_name: string; last_name: string; relationship_type: string; phone: string | null; email: string | null; is_primary_contact: boolean; }
  interface Enrollment { id: string; class_name: string; year_name: string; register_number: string | null; student_type: string; status: string; }
  interface Student {
    id: string; first_name: string; middle_name: string | null; last_name: string;
    full_name: string; gender: string; date_of_birth: string | null;
    place_of_birth: string | null; nationality: string; religion: string | null;
    photo_url: string | null; is_active: boolean;
    admission_date: string | null; admission_number: string | null;
    previous_school: string | null;
    current_enrollment: Enrollment | null;
    guardians: Guardian[];
  }

  const studentId = $page.params.id;
  $: canEnroll = $auth.user?.permissions?.enroll_students === true || $auth.user?.system_role === "SUPERADMIN";

  let student: Student | null = null;
  let enrollments: Enrollment[] = [];
  let loading = true;
  let error = "";
  let activeTab: "profile" | "enrollment" | "guardians" = "profile";

  // Enrollment form
  let classes: { id: string; name: string }[] = [];
  let showEnrollForm = false;
  let enrollClassId = "";
  let enrollType = "DAY";
  let enrolling = false;
  let enrollError = "";

  // Guardian form
  let showGuardianForm = false;
  let gFirstName = "", gLastName = "", gRelationship = "FATHER", gPhone = "", gEmail = "";
  let savingGuardian = false;

  async function load() {
    loading = true; error = "";
    try {
      const [sRes, eRes] = await Promise.all([
        api.get<Student>(`/students/${studentId}`),
        api.get<Enrollment[]>(`/students/${studentId}/enrollments`),
      ]);
      student = sRes.data;
      enrollments = eRes.data;
    } catch {
      error = "Student not found.";
    } finally {
      loading = false;
    }
  }

  async function loadClasses() {
    const { data } = await api.get<{ items: { id: string; name: string }[] }>("/settings/classes", { params: { limit: 200 } });
    classes = data.items;
    if (classes.length > 0) enrollClassId = classes[0].id;
  }

  async function doEnroll() {
    enrolling = true; enrollError = "";
    try {
      await api.post(`/students/${studentId}/enroll`, { class_id: enrollClassId, student_type: enrollType });
      showEnrollForm = false;
      await load();
      activeTab = "enrollment";
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      enrollError = err?.response?.data?.detail ?? "Enrollment failed.";
    } finally {
      enrolling = false;
    }
  }

  async function doAddGuardian() {
    savingGuardian = true;
    try {
      await api.post(`/students/${studentId}/guardians`, {
        first_name: gFirstName, last_name: gLastName,
        relationship_type: gRelationship,
        phone: gPhone || null, email: gEmail || null,
        is_primary_contact: student?.guardians.length === 0,
      });
      showGuardianForm = false;
      gFirstName = ""; gLastName = ""; gPhone = ""; gEmail = "";
      await load();
    } catch { /* ignore */ } finally {
      savingGuardian = false;
    }
  }

  async function deleteGuardian(id: string) {
    await api.delete(`/students/${studentId}/guardians/${id}`);
    await load();
  }

  function fmtDate(s: string | null): string {
    if (!s) return "—";
    return new Date(s).toLocaleDateString("en-GH", { day: "numeric", month: "short", year: "numeric" });
  }

  onMount(load);
</script>

<svelte:head>
  <title>{student?.full_name ?? "Student"} — {$schoolBranding?.name ?? "TTEK SMS"}</title>
</svelte:head>

<div class="page-header">
  <a href="/students" class="back-link"><ArrowLeft size={14} /> Students</a>
  {#if loading}
    <div class="skeleton sk-title"></div>
  {:else if student}
    <div class="student-hero">
      <div class="avatar">{(student.first_name[0] + student.last_name[0]).toUpperCase()}</div>
      <div>
        <h1 class="student-name">{student.full_name}</h1>
        <div class="student-meta">
          {#if student.current_enrollment}
            <Badge variant="accent">{student.current_enrollment.class_name}</Badge>
            {#if student.current_enrollment.register_number}
              <span class="reg-no">{student.current_enrollment.register_number}</span>
            {/if}
          {:else}
            <Badge variant="neutral">Not enrolled</Badge>
          {/if}
          <Badge variant={student.is_active ? "ok" : "danger"}>
            {student.is_active ? "Active" : "Inactive"}
          </Badge>
        </div>
      </div>
    </div>
  {:else}
    <p class="error-text">{error}</p>
  {/if}
</div>

{#if student}
  <!-- Tabs -->
  <div class="tabs">
    <button class="tab" class:active={activeTab === "profile"} on:click={() => activeTab = "profile"}>
      <GraduationCap size={13} /> Profile
    </button>
    <button class="tab" class:active={activeTab === "enrollment"} on:click={() => activeTab = "enrollment"}>
      <BookOpen size={13} /> Enrollment
      {#if enrollments.length > 0}<span class="tab-badge">{enrollments.length}</span>{/if}
    </button>
    <button class="tab" class:active={activeTab === "guardians"} on:click={() => activeTab = "guardians"}>
      <Users size={13} /> Guardians
      {#if student.guardians.length > 0}<span class="tab-badge">{student.guardians.length}</span>{/if}
    </button>
  </div>

  <!-- ── Profile tab ──────────────────────────────────────────────── -->
  {#if activeTab === "profile"}
    <div class="card">
      <div class="card-head">Personal Details</div>
      <div class="detail-grid">
        <div class="detail-row"><span class="detail-label">Full name</span><span class="detail-val">{student.full_name}</span></div>
        <div class="detail-row"><span class="detail-label">Gender</span><span class="detail-val">{student.gender === "MALE" ? "Male" : "Female"}</span></div>
        <div class="detail-row"><span class="detail-label">Date of birth</span><span class="detail-val">{fmtDate(student.date_of_birth)}</span></div>
        <div class="detail-row"><span class="detail-label">Place of birth</span><span class="detail-val">{student.place_of_birth ?? "—"}</span></div>
        <div class="detail-row"><span class="detail-label">Nationality</span><span class="detail-val">{student.nationality}</span></div>
        <div class="detail-row"><span class="detail-label">Religion</span><span class="detail-val">{student.religion ?? "—"}</span></div>
        <div class="detail-row"><span class="detail-label">Admission date</span><span class="detail-val">{fmtDate(student.admission_date)}</span></div>
        <div class="detail-row"><span class="detail-label">Admission no.</span><span class="detail-val">{student.admission_number ?? "—"}</span></div>
        <div class="detail-row"><span class="detail-label">Previous school</span><span class="detail-val">{student.previous_school ?? "—"}</span></div>
      </div>
    </div>

  <!-- ── Enrollment tab ───────────────────────────────────────────── -->
  {:else if activeTab === "enrollment"}
    {#if canEnroll && !student.current_enrollment}
      <div class="alert-box">
        <span>Student is not enrolled in the current academic year.</span>
        <button class="btn-sm" on:click={async () => { await loadClasses(); showEnrollForm = true; }}>
          Enroll now
        </button>
      </div>
    {/if}

    {#if showEnrollForm}
      <div class="card" style="margin-bottom:14px">
        <div class="card-head">Enroll in Current Year</div>
        <div class="card-body">
          <div class="form-row-2">
            <div class="field">
              <label>Class</label>
              <select bind:value={enrollClassId}>
                {#each classes as c}<option value={c.id}>{c.name}</option>{/each}
              </select>
            </div>
            <div class="field">
              <label>Student type</label>
              <select bind:value={enrollType}>
                <option value="DAY">Day</option>
                <option value="BOARDING">Boarding</option>
              </select>
            </div>
          </div>
          {#if enrollError}<p class="error-text">{enrollError}</p>{/if}
          <div class="form-actions">
            <button class="btn-ghost" on:click={() => showEnrollForm = false}>Cancel</button>
            <button class="btn-primary" on:click={doEnroll} disabled={enrolling}>
              {enrolling ? "Enrolling…" : "Confirm Enrollment"}
            </button>
          </div>
        </div>
      </div>
    {/if}

    {#if enrollments.length === 0}
      <div class="empty-state">
        <div class="empty-icon"><BookOpen size={22} /></div>
        <p class="empty-title">No enrollment history</p>
        <p class="empty-body">This student has not been enrolled in any academic year yet.</p>
      </div>
    {:else}
      <div class="card">
        <div class="card-head">Enrollment History</div>
        {#each enrollments as e}
          <div class="enroll-row">
            <div>
              <p class="enroll-class">{e.class_name}</p>
              <p class="enroll-year">{e.year_name} · {e.student_type === "DAY" ? "Day" : "Boarding"}</p>
            </div>
            <div class="enroll-right">
              {#if e.register_number}<span class="reg-no">{e.register_number}</span>{/if}
              <Badge variant={e.status === "ACTIVE" ? "ok" : "neutral"}>{e.status}</Badge>
            </div>
          </div>
        {/each}
      </div>
    {/if}

  <!-- ── Guardians tab ─────────────────────────────────────────────── -->
  {:else}
    {#if canEnroll}
      <div class="tab-actions">
        <button class="btn-sm" on:click={() => showGuardianForm = !showGuardianForm}>
          <Plus size={13} /> Add Guardian
        </button>
      </div>
    {/if}

    {#if showGuardianForm}
      <div class="card" style="margin-bottom:14px">
        <div class="card-head">New Guardian</div>
        <div class="card-body">
          <div class="form-row-2">
            <div class="field">
              <label>First name <span class="req">*</span></label>
              <input bind:value={gFirstName} />
            </div>
            <div class="field">
              <label>Last name <span class="req">*</span></label>
              <input bind:value={gLastName} />
            </div>
            <div class="field">
              <label>Relationship</label>
              <select bind:value={gRelationship}>
                <option value="FATHER">Father</option>
                <option value="MOTHER">Mother</option>
                <option value="GUARDIAN">Guardian</option>
              </select>
            </div>
            <div class="field">
              <label>Phone</label>
              <input bind:value={gPhone} placeholder="0244…" />
            </div>
            <div class="field">
              <label>Email</label>
              <input type="email" bind:value={gEmail} placeholder="Optional" />
            </div>
          </div>
          <div class="form-actions">
            <button class="btn-ghost" on:click={() => showGuardianForm = false}>Cancel</button>
            <button class="btn-primary" on:click={doAddGuardian} disabled={savingGuardian || !gFirstName || !gLastName}>
              {savingGuardian ? "Saving…" : "Add Guardian"}
            </button>
          </div>
        </div>
      </div>
    {/if}

    {#if student.guardians.length === 0}
      <div class="empty-state">
        <div class="empty-icon"><Users size={22} /></div>
        <p class="empty-title">No guardians recorded</p>
        <p class="empty-body">Add a parent or guardian to enable the parent portal when it becomes available.</p>
      </div>
    {:else}
      <div class="card">
        {#each student.guardians as g (g.id)}
          <div class="guardian-row">
            <div class="guardian-avatar">{(g.first_name[0] + g.last_name[0]).toUpperCase()}</div>
            <div class="guardian-body">
              <p class="guardian-name">
                {g.first_name} {g.last_name}
                {#if g.is_primary_contact}<span class="primary-chip">Primary</span>{/if}
              </p>
              <p class="guardian-rel">{g.relationship_type.charAt(0) + g.relationship_type.slice(1).toLowerCase()}</p>
              <div class="guardian-contacts">
                {#if g.phone}<span><Phone size={11} />{g.phone}</span>{/if}
                {#if g.email}<span><Mail size={11} />{g.email}</span>{/if}
              </div>
            </div>
            {#if canEnroll}
              <button class="btn-icon-danger" on:click={() => deleteGuardian(g.id)}>
                <Trash2 size={13} />
              </button>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  {/if}
{/if}

<style>
.page-header { margin-bottom: 16px; }
.back-link {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; color: var(--tx-low); text-decoration: none;
  margin-bottom: 10px; transition: color 0.1s;
}
.back-link:hover { color: var(--accent); }

.student-hero { display: flex; align-items: center; gap: 14px; }
.avatar {
  width: 48px; height: 48px; border-radius: 50%; flex-shrink: 0;
  background: var(--accent-subtle); color: var(--accent);
  font-size: 15px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.student-name { font-size: 20px; font-weight: 700; color: var(--tx-high); margin: 0 0 6px; }
.student-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.reg-no { font-family: monospace; font-size: 12px; color: var(--tx-low); }

/* Tabs */
.tabs {
  display: flex; gap: 2px; margin-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle); padding-bottom: 0;
}
.tab {
  display: flex; align-items: center; gap: 6px;
  padding: 9px 14px; font-size: 13px; font-weight: 500;
  color: var(--tx-low); background: transparent; border: none;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
  cursor: pointer; transition: color 0.15s, border-color 0.15s;
  white-space: nowrap;
}
.tab:hover { color: var(--tx-high); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-badge {
  background: var(--accent-subtle); color: var(--accent);
  font-size: 10px; font-weight: 700; border-radius: 99px;
  padding: 1px 6px; min-width: 18px; text-align: center;
}

/* Card */
.card {
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 12px; overflow: hidden; box-shadow: var(--shadow-xs);
  margin-bottom: 14px;
}
.card-head {
  padding: 12px 16px; background: var(--surface-0);
  border-bottom: 1px solid var(--border-subtle);
  font-size: 13px; font-weight: 600; color: var(--tx-high);
}
.card-body { padding: 16px; }

/* Detail grid */
.detail-grid { display: flex; flex-direction: column; }
.detail-row {
  display: flex; align-items: baseline; gap: 12px;
  padding: 10px 16px; border-top: 1px solid var(--border-subtle);
}
.detail-row:first-child { border-top: none; }
.detail-label { font-size: 12px; color: var(--tx-low); width: 130px; flex-shrink: 0; }
.detail-val { font-size: 13px; color: var(--tx-high); }

/* Enrollment rows */
.enroll-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-top: 1px solid var(--border-subtle);
  gap: 12px;
}
.enroll-row:first-child { border-top: none; }
.enroll-class { font-size: 13px; font-weight: 500; color: var(--tx-high); margin: 0 0 3px; }
.enroll-year  { font-size: 12px; color: var(--tx-low); margin: 0; }
.enroll-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

/* Guardian rows */
.guardian-row {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 14px 16px; border-top: 1px solid var(--border-subtle);
}
.guardian-row:first-child { border-top: none; }
.guardian-avatar {
  width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
  background: var(--surface-2); color: var(--tx-mid);
  font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.guardian-body { flex: 1; min-width: 0; }
.guardian-name { font-size: 13px; font-weight: 500; color: var(--tx-high); margin: 0 0 2px; display: flex; align-items: center; gap: 7px; }
.guardian-rel  { font-size: 12px; color: var(--tx-low); margin: 0 0 4px; }
.guardian-contacts { display: flex; gap: 12px; flex-wrap: wrap; }
.guardian-contacts span { display: flex; align-items: center; gap: 5px; font-size: 12px; color: var(--tx-mid); }
.primary-chip {
  font-size: 10px; font-weight: 600; padding: 1px 7px; border-radius: 99px;
  background: var(--accent-subtle); color: var(--accent);
}

/* Forms */
.form-row-2 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 14px; }
@media (max-width: 640px) { .form-row-2 { grid-template-columns: 1fr 1fr; } }
.field { display: flex; flex-direction: column; gap: 5px; }
.field label { font-size: 12px; font-weight: 500; color: var(--tx-mid); }
.field input, .field select {
  padding: 8px 10px; border: 1px solid var(--border-subtle);
  border-radius: 8px; background: var(--surface-0); color: var(--tx-high);
  font-size: 13px; outline: none;
}
.field input:focus, .field select:focus { border-color: var(--accent); }
.req { color: #ef4444; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; }

.btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 500;
  background: var(--accent); color: var(--accent-fg, #fff);
  border: none; cursor: pointer; transition: opacity 0.15s;
}
.btn-primary:hover:not(:disabled) { opacity: 0.88; }
.btn-primary:disabled { opacity: 0.5; cursor: default; }
.btn-ghost {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 12px; border-radius: 8px; font-size: 13px; font-weight: 500;
  background: transparent; color: var(--tx-mid);
  border: 1px solid var(--border-subtle); cursor: pointer;
  text-decoration: none; transition: background 0.1s;
}
.btn-ghost:hover { background: var(--surface-2); }
.btn-sm {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 12px; border-radius: 7px; font-size: 12px; font-weight: 500;
  background: var(--accent-subtle); color: var(--accent);
  border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
  cursor: pointer; transition: background 0.1s;
}
.btn-sm:hover { background: color-mix(in srgb, var(--accent) 15%, transparent); }
.btn-icon-danger {
  width: 28px; height: 28px; border-radius: 6px; border: none;
  background: transparent; color: var(--tx-low); cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.1s, color 0.1s; margin-top: 2px;
}
.btn-icon-danger:hover { background: color-mix(in srgb, #ef4444 10%, transparent); color: #dc2626; }

/* Misc */
.tab-actions { display: flex; justify-content: flex-end; margin-bottom: 12px; }
.alert-box {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 12px 16px; border-radius: 10px; margin-bottom: 14px; font-size: 13px;
  background: color-mix(in srgb, #f59e0b 10%, transparent);
  color: #92400e; border: 1px solid color-mix(in srgb, #f59e0b 25%, transparent);
  flex-wrap: wrap;
}
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  text-align: center; padding: 48px 32px; gap: 10px;
}
.empty-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: var(--surface-2); color: var(--tx-low);
  display: flex; align-items: center; justify-content: center; margin-bottom: 4px;
}
.empty-title { font-size: 14px; font-weight: 600; color: var(--tx-high); margin: 0; }
.empty-body  { font-size: 13px; color: var(--tx-low); margin: 0; max-width: 340px; line-height: 1.55; }
.error-text  { color: #dc2626; font-size: 13px; }
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position:  400px 0; }
}
.skeleton {
  background: linear-gradient(90deg, var(--surface-2) 25%, var(--border-subtle) 50%, var(--surface-2) 75%);
  background-size: 800px 100%; animation: shimmer 1.4s infinite linear; border-radius: 6px;
}
.sk-title { height: 22px; width: 200px; }
</style>
