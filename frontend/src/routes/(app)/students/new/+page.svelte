<script lang="ts">
  import { goto } from "$app/navigation";
  import { api } from "$api/client";
  import { schoolBranding } from "$stores/school";
  import { ArrowLeft, Plus, Trash2, UserPlus } from "@lucide/svelte";

  interface ClassItem { id: string; name: string; }

  // ── Form state ─────────────────────────────────────────────────────
  let step = 1; // 1 = student details, 2 = enrollment

  // Student fields
  let firstName = "", middleName = "", lastName = "";
  let gender = "MALE";
  let dob = "", nationality = "Ghanaian", religion = "", placeOfBirth = "";
  let admissionDate = "", admissionNumber = "", previousSchool = "";

  // Guardian fields
  let guardians: { first_name: string; last_name: string; relationship_type: string; phone: string; email: string; is_primary_contact: boolean }[] = [];

  // Enrollment fields
  let classes: ClassItem[] = [];
  let classId = "", studentType = "DAY";
  let classesLoading = false;

  let saving = false;
  let errors: Record<string, string> = {};

  async function loadClasses() {
    classesLoading = true;
    try {
      const { data } = await api.get<{ items: ClassItem[] }>("/settings/classes", { params: { limit: 200 } });
      classes = data.items;
      if (classes.length > 0) classId = classes[0].id;
    } catch { /* non-fatal */ } finally {
      classesLoading = false;
    }
  }

  function addGuardian() {
    guardians = [...guardians, {
      first_name: "", last_name: "", relationship_type: "FATHER",
      phone: "", email: "", is_primary_contact: guardians.length === 0,
    }];
  }

  function removeGuardian(i: number) {
    guardians = guardians.filter((_, idx) => idx !== i);
  }

  function validate(): boolean {
    errors = {};
    if (!firstName.trim()) errors.firstName = "Required";
    if (!lastName.trim()) errors.lastName = "Required";
    if (!gender) errors.gender = "Required";
    for (let i = 0; i < guardians.length; i++) {
      if (!guardians[i].first_name.trim()) errors[`g_first_${i}`] = "Required";
      if (!guardians[i].last_name.trim()) errors[`g_last_${i}`] = "Required";
    }
    return Object.keys(errors).length === 0;
  }

  async function handleNext() {
    if (!validate()) return;
    await loadClasses();
    step = 2;
  }

  async function handleSubmit() {
    saving = true;
    try {
      const { data: student } = await api.post("/students", {
        first_name: firstName.trim(),
        middle_name: middleName.trim() || null,
        last_name: lastName.trim(),
        gender,
        date_of_birth: dob || null,
        place_of_birth: placeOfBirth.trim() || null,
        nationality: nationality.trim() || "Ghanaian",
        religion: religion.trim() || null,
        admission_date: admissionDate || null,
        admission_number: admissionNumber.trim() || null,
        previous_school: previousSchool.trim() || null,
        guardians: guardians.filter(g => g.first_name.trim()),
      });

      if (classId) {
        await api.post(`/students/${student.id}/enroll`, {
          class_id: classId,
          student_type: studentType,
        });
      }

      goto(`/students/${student.id}`);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      errors.submit = err?.response?.data?.detail ?? "Failed to save student.";
      saving = false;
    }
  }
</script>

<svelte:head><title>Add Student — {$schoolBranding?.name ?? "TTEK SMS"}</title></svelte:head>

<div class="page-header">
  <a href="/students" class="back-link"><ArrowLeft size={14} /> Students</a>
  <h1 class="page-title">Add Student</h1>
</div>

<!-- Step indicator -->
<div class="steps">
  <div class="step" class:active={step === 1} class:done={step > 1}>
    <div class="step-num">1</div>
    <span>Student details</span>
  </div>
  <div class="step-line"></div>
  <div class="step" class:active={step === 2}>
    <div class="step-num">2</div>
    <span>Enrollment</span>
  </div>
</div>

<!-- ── Step 1: Student details ─────────────────────────────────────── -->
{#if step === 1}
<div class="card">
  <div class="card-head">Personal Information</div>
  <div class="card-body">
    <div class="form-row">
      <div class="field" class:has-error={errors.firstName}>
        <label>First name <span class="req">*</span></label>
        <input bind:value={firstName} placeholder="e.g. Kwame" />
        {#if errors.firstName}<p class="field-error">{errors.firstName}</p>{/if}
      </div>
      <div class="field">
        <label>Middle name</label>
        <input bind:value={middleName} placeholder="Optional" />
      </div>
      <div class="field" class:has-error={errors.lastName}>
        <label>Last name <span class="req">*</span></label>
        <input bind:value={lastName} placeholder="e.g. Mensah" />
        {#if errors.lastName}<p class="field-error">{errors.lastName}</p>{/if}
      </div>
    </div>

    <div class="form-row">
      <div class="field" class:has-error={errors.gender}>
        <label>Gender <span class="req">*</span></label>
        <select bind:value={gender}>
          <option value="MALE">Male</option>
          <option value="FEMALE">Female</option>
        </select>
        {#if errors.gender}<p class="field-error">{errors.gender}</p>{/if}
      </div>
      <div class="field">
        <label>Date of birth</label>
        <input type="date" bind:value={dob} />
      </div>
      <div class="field">
        <label>Nationality</label>
        <input bind:value={nationality} />
      </div>
    </div>

    <div class="form-row">
      <div class="field">
        <label>Place of birth</label>
        <input bind:value={placeOfBirth} placeholder="e.g. Kumasi" />
      </div>
      <div class="field">
        <label>Religion</label>
        <input bind:value={religion} placeholder="e.g. Christian" />
      </div>
    </div>
  </div>
</div>

<div class="card">
  <div class="card-head">Admission</div>
  <div class="card-body">
    <div class="form-row">
      <div class="field">
        <label>Admission date</label>
        <input type="date" bind:value={admissionDate} />
      </div>
      <div class="field">
        <label>Admission number</label>
        <input bind:value={admissionNumber} placeholder="School admission no." />
      </div>
      <div class="field">
        <label>Previous school</label>
        <input bind:value={previousSchool} placeholder="Name of previous school" />
      </div>
    </div>
  </div>
</div>

<div class="card">
  <div class="card-head" style="display:flex;align-items:center;justify-content:space-between">
    <span>Guardians</span>
    <button class="btn-ghost" on:click={addGuardian}>
      <Plus size={13} /> Add guardian
    </button>
  </div>
  {#if guardians.length === 0}
    <div class="card-body">
      <p class="hint">No guardians added. You can add them now or later from the student profile.</p>
    </div>
  {:else}
    {#each guardians as g, i}
      <div class="card-body guardian-block">
        <div class="guardian-header">
          <span class="guardian-label">Guardian {i + 1}</span>
          <button class="btn-icon-danger" on:click={() => removeGuardian(i)}><Trash2 size={13} /></button>
        </div>
        <div class="form-row">
          <div class="field" class:has-error={errors[`g_first_${i}`]}>
            <label>First name <span class="req">*</span></label>
            <input bind:value={g.first_name} />
            {#if errors[`g_first_${i}`]}<p class="field-error">{errors[`g_first_${i}`]}</p>{/if}
          </div>
          <div class="field" class:has-error={errors[`g_last_${i}`]}>
            <label>Last name <span class="req">*</span></label>
            <input bind:value={g.last_name} />
            {#if errors[`g_last_${i}`]}<p class="field-error">{errors[`g_last_${i}`]}</p>{/if}
          </div>
          <div class="field">
            <label>Relationship</label>
            <select bind:value={g.relationship_type}>
              <option value="FATHER">Father</option>
              <option value="MOTHER">Mother</option>
              <option value="GUARDIAN">Guardian</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="field">
            <label>Phone</label>
            <input bind:value={g.phone} placeholder="0244…" />
          </div>
          <div class="field">
            <label>Email</label>
            <input type="email" bind:value={g.email} placeholder="Optional" />
          </div>
          <div class="field check-field">
            <label class="checkbox-label">
              <input type="checkbox" bind:checked={g.is_primary_contact} />
              Primary contact
            </label>
          </div>
        </div>
      </div>
    {/each}
  {/if}
</div>

<div class="form-actions">
  <a href="/students" class="btn-ghost">Cancel</a>
  <button class="btn-primary" on:click={handleNext}>Next: Enrollment →</button>
</div>

<!-- ── Step 2: Enrollment ───────────────────────────────────────────── -->
{:else}
<div class="card">
  <div class="card-head">Class Enrollment</div>
  <div class="card-body">
    {#if classesLoading}
      <p class="hint">Loading classes…</p>
    {:else if classes.length === 0}
      <div class="warn-box">
        No active classes found. You can still create the student and enroll them later
        once classes are set up in Settings → Academic Structure.
      </div>
    {:else}
      <div class="form-row">
        <div class="field">
          <label>Class <span class="req">*</span></label>
          <select bind:value={classId}>
            {#each classes as c}
              <option value={c.id}>{c.name}</option>
            {/each}
          </select>
        </div>
        <div class="field">
          <label>Student type</label>
          <select bind:value={studentType}>
            <option value="DAY">Day student</option>
            <option value="BOARDING">Boarding student</option>
          </select>
        </div>
      </div>
    {/if}
  </div>
</div>

{#if errors.submit}
  <div class="error-banner">{errors.submit}</div>
{/if}

<div class="form-actions">
  <button class="btn-ghost" on:click={() => step = 1}>← Back</button>
  <button class="btn-primary" on:click={handleSubmit} disabled={saving}>
    {#if saving}Saving…{:else}<UserPlus size={14} /> Enroll Student{/if}
  </button>
</div>
{/if}

<style>
.page-header { margin-bottom: 20px; }
.back-link {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; color: var(--tx-low); text-decoration: none;
  margin-bottom: 8px; transition: color 0.1s;
}
.back-link:hover { color: var(--accent); }
.page-title { font-size: 18px; font-weight: 700; color: var(--tx-high); margin: 0; }

/* Steps */
.steps {
  display: flex; align-items: center; gap: 0;
  margin-bottom: 20px; max-width: 340px;
}
.step { display: flex; align-items: center; gap: 8px; }
.step-num {
  width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
  border: 2px solid var(--border-subtle); background: var(--surface-1);
  color: var(--tx-low); font-size: 12px; font-weight: 600;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.step.active .step-num { border-color: var(--accent); background: var(--accent); color: #fff; }
.step.done  .step-num { border-color: var(--ok-text, #065f46); background: var(--ok-bg, #d1fae5); color: var(--ok-text, #065f46); }
.step span  { font-size: 13px; font-weight: 500; color: var(--tx-low); }
.step.active span { color: var(--tx-high); }
.step-line  { flex: 1; height: 2px; background: var(--border-subtle); margin: 0 10px; max-width: 60px; }

/* Cards */
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

/* Form */
.form-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 14px; }
.form-row:last-child { margin-bottom: 0; }
@media (max-width: 640px) { .form-row { grid-template-columns: 1fr; } }

.field { display: flex; flex-direction: column; gap: 5px; }
.field label { font-size: 12px; font-weight: 500; color: var(--tx-mid); }
.field input, .field select {
  padding: 8px 10px; border: 1px solid var(--border-subtle);
  border-radius: 8px; background: var(--surface-0); color: var(--tx-high);
  font-size: 13px; outline: none; transition: border-color 0.15s;
}
.field input:focus, .field select:focus { border-color: var(--accent); }
.has-error input, .has-error select { border-color: #ef4444; }
.field-error { font-size: 11px; color: #dc2626; margin: 0; }
.req { color: #ef4444; }

.check-field { justify-content: flex-end; }
.checkbox-label {
  display: flex; align-items: center; gap: 7px;
  font-size: 13px; color: var(--tx-mid); cursor: pointer;
  padding: 8px 0;
}

.hint { font-size: 13px; color: var(--tx-low); margin: 0; }

.guardian-block { border-top: 1px solid var(--border-subtle); }
.guardian-block:first-of-type { border-top: none; }
.guardian-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.guardian-label { font-size: 12px; font-weight: 600; color: var(--tx-low); text-transform: uppercase; letter-spacing: 0.04em; }

.warn-box {
  padding: 12px; border-radius: 8px; font-size: 13px;
  background: color-mix(in srgb, #f59e0b 10%, transparent);
  color: #92400e; border: 1px solid color-mix(in srgb, #f59e0b 25%, transparent);
}
.error-banner {
  padding: 12px 16px; border-radius: 10px; font-size: 13px; margin-bottom: 12px;
  background: color-mix(in srgb, #ef4444 10%, transparent);
  color: #dc2626; border: 1px solid color-mix(in srgb, #ef4444 25%, transparent);
}

/* Actions */
.form-actions {
  display: flex; justify-content: flex-end; gap: 10px;
  padding-top: 4px;
}
.btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 18px; border-radius: 8px; font-size: 13px; font-weight: 500;
  background: var(--accent); color: var(--accent-fg, #fff);
  border: none; cursor: pointer; transition: opacity 0.15s;
}
.btn-primary:hover:not(:disabled) { opacity: 0.88; }
.btn-primary:disabled { opacity: 0.5; cursor: default; }
.btn-ghost {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 14px; border-radius: 8px; font-size: 13px; font-weight: 500;
  background: transparent; color: var(--tx-mid);
  border: 1px solid var(--border-subtle); cursor: pointer;
  text-decoration: none; transition: background 0.1s;
}
.btn-ghost:hover { background: var(--surface-2); }
.btn-icon-danger {
  width: 28px; height: 28px; border-radius: 6px; border: none;
  background: transparent; color: var(--tx-low); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.1s, color 0.1s;
}
.btn-icon-danger:hover {
  background: color-mix(in srgb, #ef4444 10%, transparent); color: #dc2626;
}
</style>
