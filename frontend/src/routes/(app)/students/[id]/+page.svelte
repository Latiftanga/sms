<script lang="ts">
  import { page } from "$app/stores";
  import { onMount } from "svelte";
  import { api } from "$api/client";
  import { auth } from "$stores/auth";
  import { schoolBranding } from "$stores/school";
  import Badge from "$components/ui/Badge.svelte";
  import {
    ArrowLeft, GraduationCap, Users,
    BookOpen, Plus, Trash2, Phone, Mail,
    Calendar, MapPin, User, BookMarked,
  } from "@lucide/svelte";

  interface Guardian { id: string; first_name: string; last_name: string; relationship_type: string; phone: string | null; email: string | null; is_primary_contact: boolean; }
  interface Enrollment { id: string; class_name: string; year_name: string; register_number: string | null; student_type: string; status: string; house_name: string | null; }
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

  function calcAge(dob: string | null): string {
    if (!dob) return "—";
    const diff = Date.now() - new Date(dob).getTime();
    const age = Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
    return `${age} yrs`;
  }

  function initials(first: string, last: string): string {
    return (first[0] + last[0]).toUpperCase();
  }

  onMount(load);
</script>

<svelte:head>
  <title>{student?.full_name ?? "Student"} — {$schoolBranding?.name ?? "TTEK SMS"}</title>
</svelte:head>

<!-- Back -->
<a href="/students" class="back-link">
  <ArrowLeft size={13} /> Students
</a>

<!-- ── Loading skeleton ───────────────────────────────────────────── -->
{#if loading}
  <div class="hero-skeleton">
    <div class="sk sk-avatar"></div>
    <div class="sk-info">
      <div class="sk sk-name"></div>
      <div class="sk sk-sub"></div>
      <div class="sk sk-stats"></div>
    </div>
  </div>
  <div class="layout">
    <div class="sk sk-card-main"></div>
    <div class="sk-side">
      <div class="sk sk-card-sm"></div>
      <div class="sk sk-card-sm"></div>
    </div>
  </div>

<!-- ── Error ──────────────────────────────────────────────────────── -->
{:else if error}
  <div class="error-state">{error}</div>

<!-- ── Profile ───────────────────────────────────────────────────── -->
{:else if student}

<!-- Hero card -->
<div class="hero">
  <div class="hero-inner">
    <!-- Avatar -->
    <div class="avatar-wrap">
      {#if student.photo_url}
        <img src={student.photo_url} alt={student.full_name} class="avatar-img" />
      {:else}
        <div class="avatar">{initials(student.first_name, student.last_name)}</div>
      {/if}
      <span
        class="status-dot"
        class:active={student.is_active}
        title={student.is_active ? "Active" : "Inactive"}
      ></span>
    </div>

    <!-- Identity -->
    <div class="hero-body">
      <div class="hero-top">
        <div>
          <h1 class="hero-name">{student.full_name}</h1>
          <div class="hero-sub">
            {#if student.current_enrollment?.register_number}
              <code class="reg-code">{student.current_enrollment.register_number}</code>
            {/if}
            {#if student.current_enrollment}
              <span class="class-pill">
                <GraduationCap size={11} />
                {student.current_enrollment.class_name}
              </span>
              {#if student.current_enrollment.house_name}
                <span class="house-pill">{student.current_enrollment.house_name}</span>
              {/if}
            {:else}
              <span class="no-enroll-pill">Not enrolled</span>
            {/if}
          </div>
        </div>
        <span class="status-badge" class:active={student.is_active}>
          {student.is_active ? "Active" : "Inactive"}
        </span>
      </div>

      <!-- Stat strip -->
      <div class="stat-strip">
        <div class="stat">
          <span class="stat-label">Age</span>
          <span class="stat-val">{calcAge(student.date_of_birth)}</span>
        </div>
        <div class="stat-div"></div>
        <div class="stat">
          <span class="stat-label">Gender</span>
          <span class="stat-val">{student.gender === "MALE" ? "Male" : "Female"}</span>
        </div>
        <div class="stat-div"></div>
        <div class="stat">
          <span class="stat-label">Nationality</span>
          <span class="stat-val">{student.nationality}</span>
        </div>
        {#if student.admission_date}
          <div class="stat-div"></div>
          <div class="stat">
            <span class="stat-label">Admitted</span>
            <span class="stat-val">{fmtDate(student.admission_date)}</span>
          </div>
        {/if}
        {#if student.admission_number}
          <div class="stat-div"></div>
          <div class="stat">
            <span class="stat-label">Adm. No.</span>
            <span class="stat-val">{student.admission_number}</span>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>

<!-- Tab nav -->
<nav class="tab-nav">
  <button class="tn-item" class:tn-active={activeTab === "profile"} on:click={() => activeTab = "profile"}>
    <User size={13} /> Personal
  </button>
  <button class="tn-item" class:tn-active={activeTab === "enrollment"} on:click={() => activeTab = "enrollment"}>
    <BookMarked size={13} /> Enrollment
    {#if enrollments.length > 0}<span class="tn-count">{enrollments.length}</span>{/if}
  </button>
  <button class="tn-item" class:tn-active={activeTab === "guardians"} on:click={() => activeTab = "guardians"}>
    <Users size={13} /> Guardians
    {#if student.guardians.length > 0}<span class="tn-count">{student.guardians.length}</span>{/if}
  </button>
</nav>

<!-- ── Personal tab ───────────────────────────────────────────────── -->
{#if activeTab === "profile"}
<div class="profile-card card">
  <!-- Identity section -->
  <div class="section">
    <p class="section-label"><User size={11} /> Identity</p>
    <div class="info-grid">
      <div class="info-field">
        <span class="if-label">First name</span>
        <span class="if-val">{student.first_name}</span>
      </div>
      <div class="info-field">
        <span class="if-label">Middle name</span>
        <span class="if-val">{student.middle_name ?? "—"}</span>
      </div>
      <div class="info-field">
        <span class="if-label">Last name</span>
        <span class="if-val">{student.last_name}</span>
      </div>
      <div class="info-field">
        <span class="if-label">Gender</span>
        <span class="if-val">{student.gender === "MALE" ? "Male" : "Female"}</span>
      </div>
      <div class="info-field">
        <span class="if-label">Date of birth</span>
        <span class="if-val">{fmtDate(student.date_of_birth)}</span>
      </div>
      <div class="info-field">
        <span class="if-label">Religion</span>
        <span class="if-val">{student.religion ?? "—"}</span>
      </div>
    </div>
  </div>

  <div class="section-divider"></div>

  <!-- Origin section -->
  <div class="section">
    <p class="section-label"><MapPin size={11} /> Origin</p>
    <div class="info-grid">
      <div class="info-field">
        <span class="if-label">Nationality</span>
        <span class="if-val">{student.nationality}</span>
      </div>
      <div class="info-field">
        <span class="if-label">Place of birth</span>
        <span class="if-val">{student.place_of_birth ?? "—"}</span>
      </div>
    </div>
  </div>

  <div class="section-divider"></div>

  <!-- Admission section -->
  <div class="section">
    <p class="section-label"><Calendar size={11} /> Admission</p>
    <div class="info-grid">
      <div class="info-field">
        <span class="if-label">Admission date</span>
        <span class="if-val">{fmtDate(student.admission_date)}</span>
      </div>
      <div class="info-field">
        <span class="if-label">Admission number</span>
        <span class="if-val">{student.admission_number ?? "—"}</span>
      </div>
      <div class="info-field">
        <span class="if-label">Previous school</span>
        <span class="if-val">{student.previous_school ?? "—"}</span>
      </div>
    </div>
  </div>
</div>

<!-- ── Enrollment tab ─────────────────────────────────────────────── -->
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
    <div class="card" style="margin-bottom:16px">
      <div class="card-head">Enroll in Current Year</div>
      <div class="card-body">
        <div class="form-row">
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
        {#if enrollError}<p class="err-txt">{enrollError}</p>{/if}
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
    <div class="timeline">
      {#each enrollments as e, i}
        <div class="tl-item">
          <div class="tl-marker" class:tl-current={e.status === "ACTIVE"}></div>
          <div class="tl-line" class:tl-last={i === enrollments.length - 1}></div>
          <div class="tl-content card">
            <div class="tl-head">
              <div>
                <p class="tl-class">{e.class_name}</p>
                <p class="tl-meta">
                  {e.year_name}
                  · {e.student_type === "DAY" ? "Day student" : "Boarding"}
                  {#if e.house_name} · {e.house_name}{/if}
                </p>
              </div>
              <div class="tl-right">
                {#if e.register_number}
                  <code class="reg-code sm">{e.register_number}</code>
                {/if}
                <span class="status-pill" class:pill-active={e.status === "ACTIVE"}>
                  {e.status}
                </span>
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}

<!-- ── Guardians tab ───────────────────────────────────────────────── -->
{:else}
  <div class="tab-toolbar">
    {#if canEnroll}
      <button class="btn-sm" on:click={() => showGuardianForm = !showGuardianForm}>
        <Plus size={13} /> Add Guardian
      </button>
    {/if}
  </div>

  {#if showGuardianForm}
    <div class="card" style="margin-bottom:16px">
      <div class="card-head">New Guardian</div>
      <div class="card-body">
        <div class="form-row cols-3">
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
          <button class="btn-primary" on:click={doAddGuardian}
            disabled={savingGuardian || !gFirstName || !gLastName}>
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
      <p class="empty-body">Add a parent or guardian to enable the parent portal.</p>
    </div>
  {:else}
    <div class="guardian-grid">
      {#each student.guardians as g (g.id)}
        <div class="g-card card">
          <div class="g-top">
            <div class="g-avatar">{initials(g.first_name, g.last_name)}</div>
            <div class="g-info">
              <p class="g-name">
                {g.first_name} {g.last_name}
                {#if g.is_primary_contact}
                  <span class="primary-chip">Primary</span>
                {/if}
              </p>
              <p class="g-rel">{g.relationship_type.charAt(0) + g.relationship_type.slice(1).toLowerCase()}</p>
            </div>
            {#if canEnroll}
              <button class="btn-del" on:click={() => deleteGuardian(g.id)} title="Remove guardian">
                <Trash2 size={13} />
              </button>
            {/if}
          </div>
          <div class="g-contacts">
            {#if g.phone}
              <a href="tel:{g.phone}" class="g-contact">
                <Phone size={12} /> {g.phone}
              </a>
            {/if}
            {#if g.email}
              <a href="mailto:{g.email}" class="g-contact">
                <Mail size={12} /> {g.email}
              </a>
            {/if}
            {#if !g.phone && !g.email}
              <span class="g-no-contact">No contact details</span>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
{/if}

{/if}

<style>
/* ── Back link ────────────────────────────────────────────────────── */
.back-link {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; font-weight: 500; color: var(--tx-low);
  text-decoration: none; margin-bottom: 18px;
  transition: color 0.12s;
}
.back-link:hover { color: var(--accent); }

/* ── Hero ─────────────────────────────────────────────────────────── */
.hero {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  box-shadow: var(--shadow-xs);
  margin-bottom: 12px;
  overflow: hidden;
  position: relative;
}
.hero::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--accent);
  border-radius: 16px 16px 0 0;
}
.hero-inner {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  padding: 24px 24px 20px;
}

/* Avatar */
.avatar-wrap { position: relative; flex-shrink: 0; }
.avatar {
  width: 72px; height: 72px; border-radius: 50%;
  background: var(--accent-subtle);
  color: var(--accent);
  font-size: 22px; font-weight: 800; letter-spacing: -1px;
  display: flex; align-items: center; justify-content: center;
  border: 3px solid var(--surface-0);
  box-shadow: 0 0 0 1px var(--border-subtle);
}
.avatar-img {
  width: 72px; height: 72px; border-radius: 50%;
  object-fit: cover;
  border: 3px solid var(--surface-0);
  box-shadow: 0 0 0 1px var(--border-subtle);
}
.status-dot {
  position: absolute;
  bottom: 2px; right: 2px;
  width: 14px; height: 14px;
  border-radius: 50%;
  background: var(--tx-low);
  border: 2px solid var(--surface-1);
}
.status-dot.active {
  background: #22c55e;
}

/* Hero body */
.hero-body { flex: 1; min-width: 0; }
.hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.hero-name {
  font-size: 22px; font-weight: 800; color: var(--tx-high);
  margin: 0 0 6px; line-height: 1.1; letter-spacing: -0.3px;
}
.hero-sub {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.reg-code {
  font-family: "SF Mono", "Fira Code", monospace;
  font-size: 11.5px; font-weight: 600;
  background: var(--surface-2);
  color: var(--tx-mid);
  padding: 2px 8px; border-radius: 5px;
  border: 1px solid var(--border-subtle);
  letter-spacing: 0.02em;
}
.reg-code.sm { font-size: 11px; padding: 1px 6px; }
.class-pill {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; font-weight: 600;
  color: var(--accent);
  background: var(--accent-subtle);
  padding: 3px 9px; border-radius: 99px;
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
}
.house-pill {
  font-size: 12px; font-weight: 500;
  color: var(--tx-mid);
  background: var(--surface-2);
  padding: 3px 9px; border-radius: 99px;
  border: 1px solid var(--border-subtle);
}
.no-enroll-pill {
  font-size: 12px; color: var(--tx-low);
  font-style: italic;
}
.status-badge {
  flex-shrink: 0;
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 4px 10px; border-radius: 99px;
  background: var(--surface-2); color: var(--tx-low);
  border: 1px solid var(--border-subtle);
}
.status-badge.active {
  background: color-mix(in srgb, #22c55e 12%, transparent);
  color: #15803d;
  border-color: color-mix(in srgb, #22c55e 25%, transparent);
}

/* Stat strip */
.stat-strip {
  display: flex; align-items: center; gap: 0;
  flex-wrap: wrap;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border-subtle);
}
.stat { display: flex; flex-direction: column; gap: 1px; padding: 0 16px 0 0; }
.stat:first-child { padding-left: 0; }
.stat-label { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--tx-low); }
.stat-val { font-size: 13px; font-weight: 600; color: var(--tx-high); }
.stat-div {
  width: 1px; height: 24px;
  background: var(--border-subtle);
  margin: 0 16px 0 0;
  flex-shrink: 0;
}

/* ── Tab nav ──────────────────────────────────────────────────────── */
.tab-nav {
  display: flex; gap: 4px;
  margin-bottom: 16px;
}
.tn-item {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 14px; border-radius: 8px;
  font-size: 13px; font-weight: 500;
  color: var(--tx-low); background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  cursor: pointer; transition: all 0.12s;
  white-space: nowrap;
}
.tn-item:hover { color: var(--tx-high); background: var(--surface-2); }
.tn-item.tn-active {
  color: var(--accent);
  background: var(--accent-subtle);
  border-color: color-mix(in srgb, var(--accent) 25%, transparent);
}
.tn-count {
  background: var(--accent); color: var(--accent-fg, #fff);
  font-size: 10px; font-weight: 700;
  padding: 1px 6px; border-radius: 99px; min-width: 18px; text-align: center;
}
.tn-item:not(.tn-active) .tn-count {
  background: var(--surface-2); color: var(--tx-low);
}

/* ── Card base ────────────────────────────────────────────────────── */
.card {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-xs);
}
.card-head {
  padding: 12px 20px;
  background: var(--surface-0);
  border-bottom: 1px solid var(--border-subtle);
  font-size: 13px; font-weight: 600; color: var(--tx-high);
}
.card-body { padding: 16px 20px; }

/* ── Profile card / info-grid ─────────────────────────────────────── */
.profile-card { margin-bottom: 0; }
.section { padding: 20px 24px; }
.section-label {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--tx-low);
  margin: 0 0 16px;
}
.section-divider {
  height: 1px;
  background: var(--border-subtle);
  margin: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px 24px;
}
@media (max-width: 680px) {
  .info-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 420px) {
  .info-grid { grid-template-columns: 1fr; }
}

.info-field { display: flex; flex-direction: column; gap: 3px; }
.if-label {
  font-size: 10.5px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--tx-low);
}
.if-val {
  font-size: 13.5px; font-weight: 500; color: var(--tx-high);
  word-break: break-word;
}

/* ── Timeline (enrollment) ────────────────────────────────────────── */
.timeline { display: flex; flex-direction: column; gap: 0; }
.tl-item {
  display: flex; gap: 14px; position: relative;
  padding-bottom: 16px;
}
.tl-item:last-child { padding-bottom: 0; }

.tl-marker {
  flex-shrink: 0;
  width: 12px; height: 12px; border-radius: 50%;
  background: var(--surface-2);
  border: 2px solid var(--border-subtle);
  margin-top: 14px;
  z-index: 1;
}
.tl-marker.tl-current {
  background: var(--accent);
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent);
}

.tl-line {
  position: absolute;
  left: 5px; top: 26px; bottom: 0;
  width: 2px;
  background: var(--border-subtle);
}
.tl-line.tl-last { display: none; }

.tl-content {
  flex: 1; min-width: 0;
}
.tl-head {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; padding: 14px 16px;
  flex-wrap: wrap;
}
.tl-class { font-size: 14px; font-weight: 600; color: var(--tx-high); margin: 0 0 3px; }
.tl-meta { font-size: 12px; color: var(--tx-low); margin: 0; }
.tl-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.status-pill {
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.04em; padding: 3px 8px; border-radius: 99px;
  background: var(--surface-2); color: var(--tx-low);
  border: 1px solid var(--border-subtle);
}
.status-pill.pill-active {
  background: color-mix(in srgb, #22c55e 12%, transparent);
  color: #15803d;
  border-color: color-mix(in srgb, #22c55e 25%, transparent);
}

/* ── Guardian grid ────────────────────────────────────────────────── */
.guardian-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.g-card { padding: 0; }
.g-top {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--border-subtle);
}
.g-avatar {
  width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;
  background: var(--accent-subtle); color: var(--accent);
  font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.g-info { flex: 1; min-width: 0; }
.g-name {
  font-size: 14px; font-weight: 600; color: var(--tx-high);
  margin: 0 0 2px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}
.g-rel { font-size: 12px; color: var(--tx-low); margin: 0; }
.primary-chip {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.04em; padding: 1px 6px; border-radius: 99px;
  background: var(--accent-subtle); color: var(--accent);
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
}
.g-contacts {
  display: flex; flex-direction: column; gap: 6px;
  padding: 12px 16px;
}
.g-contact {
  display: flex; align-items: center; gap: 7px;
  font-size: 12.5px; color: var(--tx-mid);
  text-decoration: none; transition: color 0.1s;
}
.g-contact:hover { color: var(--accent); }
.g-no-contact { font-size: 12px; color: var(--tx-low); font-style: italic; }

.btn-del {
  width: 30px; height: 30px; border-radius: 7px; border: none;
  background: transparent; color: var(--tx-low); cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.1s, color 0.1s;
}
.btn-del:hover {
  background: color-mix(in srgb, #ef4444 10%, transparent);
  color: #dc2626;
}

/* ── Forms ────────────────────────────────────────────────────────── */
.form-row {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px;
}
.form-row.cols-3 { grid-template-columns: repeat(3, 1fr); }
@media (max-width: 600px) {
  .form-row, .form-row.cols-3 { grid-template-columns: 1fr; }
}
.field { display: flex; flex-direction: column; gap: 5px; }
.field label { font-size: 12px; font-weight: 500; color: var(--tx-mid); }
.field input, .field select {
  padding: 8px 10px; border: 1px solid var(--border-subtle);
  border-radius: 8px; background: var(--surface-0); color: var(--tx-high);
  font-size: 13px; outline: none; transition: border-color 0.15s;
}
.field input:focus, .field select:focus { border-color: var(--accent); }
.req { color: #ef4444; }
.form-actions { display: flex; justify-content: flex-end; gap: 8px; padding-top: 4px; }
.err-txt { font-size: 12px; color: #dc2626; margin: 0 0 8px; }

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
  transition: background 0.1s;
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

/* ── Misc ─────────────────────────────────────────────────────────── */
.tab-toolbar { display: flex; justify-content: flex-end; margin-bottom: 12px; }

.alert-box {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 12px 16px; border-radius: 10px; margin-bottom: 14px; font-size: 13px;
  background: color-mix(in srgb, #f59e0b 10%, transparent);
  color: #92400e; border: 1px solid color-mix(in srgb, #f59e0b 25%, transparent);
  flex-wrap: wrap;
}

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
.error-state { font-size: 13px; color: #dc2626; padding: 24px 0; }

/* ── Skeleton ─────────────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -600px 0; }
  100% { background-position:  600px 0; }
}
.sk {
  background: linear-gradient(90deg,
    var(--surface-2) 25%, var(--border-subtle) 50%, var(--surface-2) 75%);
  background-size: 1200px 100%;
  animation: shimmer 1.6s infinite linear;
  border-radius: 8px;
}
.hero-skeleton {
  display: flex; align-items: flex-start; gap: 20px;
  padding: 24px; background: var(--surface-1);
  border: 1px solid var(--border-subtle); border-radius: 16px;
  margin-bottom: 12px;
}
.sk-avatar { width: 72px; height: 72px; border-radius: 50%; flex-shrink: 0; }
.sk-info { flex: 1; display: flex; flex-direction: column; gap: 10px; padding-top: 4px; }
.sk-name  { height: 26px; width: 220px; border-radius: 6px; }
.sk-sub   { height: 16px; width: 160px; border-radius: 6px; }
.sk-stats { height: 12px; width: 300px; border-radius: 6px; margin-top: 8px; }
.layout   { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.sk-side  { display: flex; flex-direction: column; gap: 12px; }
.sk-card-main { height: 260px; border-radius: 12px; }
.sk-card-sm   { height: 120px; border-radius: 12px; }
</style>
