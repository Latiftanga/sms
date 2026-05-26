<script lang="ts">
  import { onMount } from "svelte";
  import { api } from "$api/client";
  import {
    School2, CalendarDays, LayoutGrid, BookOpen,
    Plus, Pencil, Trash2, Check, X, ChevronRight,
    AlertCircle, Loader2,
  } from "@lucide/svelte";

  // ── Tab ───────────────────────────────────────────────────────────
  let tab: "school" | "calendar" | "classes" | "learning_areas" = "school";

  const LEVEL_LABELS: Record<string, string> = {
    EARLY_CHILDHOOD: "Early Childhood",
    BASIC: "Basic",
    SHS: "Senior High School",
    TECHNICAL: "Technical",
    JHS: "Junior High School",
  };

  // ── Helpers ───────────────────────────────────────────────────────
  function apiError(e: unknown): string {
    const err = e as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail ?? "Something went wrong. Try again.";
  }

  // ── School profile ────────────────────────────────────────────────
  let school: any = null;
  let schoolSaving = false;
  let schoolSuccess = false;
  let schoolError = "";

  $: isSHS = school?.education_levels?.includes("SHS") ?? false;

  async function loadSchool() {
    try {
      const { data } = await api.get("/settings/school");
      school = { ...data };
    } catch { school = null; }
  }

  async function saveSchool() {
    schoolSaving = true; schoolError = ""; schoolSuccess = false;
    try {
      await api.patch("/settings/school", {
        name: school.name, phone: school.phone, email: school.email,
        address: school.address, region: school.region,
        district: school.district, accent_color: school.accent_color,
      });
      schoolSuccess = true;
      setTimeout(() => schoolSuccess = false, 3000);
    } catch (e) { schoolError = apiError(e); }
    finally { schoolSaving = false; }
  }

  // ── Academic years ────────────────────────────────────────────────
  let years: any[] = [];
  let newYear = { name: "", start_date: "", end_date: "" };
  let yearErrors: Record<string, string> = {};
  let addingYear = false;
  let savingYear = false;
  let yearApiError = "";
  let confirmDeleteYear: string | null = null;

  async function loadYears() {
    try {
      const { data } = await api.get("/settings/academic-years");
      years = data;
    } catch { years = []; }
  }

  function validateYear() {
    const errs: Record<string, string> = {};
    if (!newYear.name.trim()) errs.name = "Name is required";
    if (!newYear.start_date) errs.start_date = "Start date is required";
    if (!newYear.end_date) errs.end_date = "End date is required";
    if (newYear.start_date && newYear.end_date && newYear.end_date <= newYear.start_date)
      errs.end_date = "End date must be after start date";
    return errs;
  }

  async function createYear() {
    yearErrors = validateYear();
    if (Object.keys(yearErrors).length) return;
    savingYear = true; yearApiError = "";
    try {
      await api.post("/settings/academic-years", newYear);
      newYear = { name: "", start_date: "", end_date: "" };
      yearErrors = {};
      addingYear = false;
      await loadYears();
    } catch (e) { yearApiError = apiError(e); }
    finally { savingYear = false; }
  }

  async function activateYear(id: string) {
    await api.post(`/settings/academic-years/${id}/activate`);
    await loadYears();
  }

  async function deleteYear(id: string) {
    try {
      await api.delete(`/settings/academic-years/${id}`);
      confirmDeleteYear = null;
      await loadYears();
    } catch (e) { alert(apiError(e)); }
  }

  // ── Terms ─────────────────────────────────────────────────────────
  let expandedYear: string | null = null;
  let newTerm: Record<string, any> = {};
  let termErrors: Record<string, Record<string, string>> = {};
  let addingTermFor: string | null = null;
  let savingTerm = false;
  let termApiError = "";
  let confirmDeleteTerm: string | null = null;

  function validateTerm(yearId: string) {
    const t = newTerm[yearId] ?? {};
    const errs: Record<string, string> = {};
    if (!t.name?.trim()) errs.name = "Name is required";
    if (!t.start_date) errs.start_date = "Start date is required";
    if (!t.end_date) errs.end_date = "End date is required";
    if (t.start_date && t.end_date && t.end_date <= t.start_date)
      errs.end_date = "End date must be after start date";
    return errs;
  }

  async function createTerm(yearId: string) {
    termErrors[yearId] = validateTerm(yearId);
    if (Object.keys(termErrors[yearId]).length) return;
    savingTerm = true; termApiError = "";
    try {
      await api.post(`/settings/academic-years/${yearId}/terms`, newTerm[yearId]);
      newTerm[yearId] = { name: "", start_date: "", end_date: "" };
      termErrors[yearId] = {};
      addingTermFor = null;
      await loadYears();
    } catch (e) { termApiError = apiError(e); }
    finally { savingTerm = false; }
  }

  async function activateTerm(termId: string) {
    await api.post(`/settings/terms/${termId}/activate`);
    await loadYears();
  }

  async function deleteTerm(termId: string) {
    try {
      await api.delete(`/settings/terms/${termId}`);
      confirmDeleteTerm = null;
      await loadYears();
    } catch (e) { alert(apiError(e)); }
  }

  // ── Learning areas ────────────────────────────────────────────────
  const GES_AREAS = [
    "General Science", "General Arts", "Business",
    "Visual Arts", "Home Economics", "Technical", "Agriculture",
  ];
  let learningAreas: any[] = [];
  let newLA = { name: "", short_name: "" };
  let laErrors: Record<string, string> = {};
  let addingLA = false;
  let savingLA = false;
  let laApiError = "";
  let editingLA: string | null = null;
  let editLAShort = "";
  let savingLAEdit = false;
  let confirmDeleteLA: string | null = null;

  async function loadLearningAreas() {
    try {
      const { data } = await api.get("/settings/learning-areas");
      learningAreas = data;
    } catch { learningAreas = []; }
  }

  async function createLA() {
    laErrors = {};
    if (!newLA.name) laErrors.name = "Please select a learning area";
    if (Object.keys(laErrors).length) return;
    savingLA = true; laApiError = "";
    try {
      await api.post("/settings/learning-areas", { name: newLA.name, short_name: newLA.short_name || null });
      newLA = { name: "", short_name: "" };
      addingLA = false;
      await loadLearningAreas();
    } catch (e) { laApiError = apiError(e); }
    finally { savingLA = false; }
  }

  async function saveLA(id: string) {
    savingLAEdit = true;
    try {
      await api.patch(`/settings/learning-areas/${id}`, { short_name: editLAShort || null });
      editingLA = null;
      await loadLearningAreas();
    } catch { /* silent */ }
    finally { savingLAEdit = false; }
  }

  async function deleteLA(id: string) {
    try {
      await api.delete(`/settings/learning-areas/${id}`);
      confirmDeleteLA = null;
      await loadLearningAreas();
    } catch (e) { alert(apiError(e)); }
  }

  // ── Classes ───────────────────────────────────────────────────────
  const LEVELS = ["Creche", "Nursery", "KG", "Basic", "SHS"];
  const YEAR_BOUNDS: Record<string, [number, number]> = {
    Nursery: [1, 2], KG: [1, 2], Basic: [1, 9], SHS: [1, 3],
  };
  let classes: any[] = [];
  let newClass = { level: "Basic", year: 1, learning_area_id: "", stream: "" };
  let classErrors: Record<string, string> = {};
  let addingClass = false;
  let savingClass = false;
  let classApiError = "";
  let confirmDeleteClass: string | null = null;

  $: newClassYears = newClass.level in YEAR_BOUNDS
    ? Array.from({ length: YEAR_BOUNDS[newClass.level][1] - YEAR_BOUNDS[newClass.level][0] + 1 },
        (_, i) => i + YEAR_BOUNDS[newClass.level][0])
    : [];

  $: if (newClass.level === "SHS" && isSHS && learningAreas.length === 0) loadLearningAreas();

  async function loadClasses() {
    try {
      const { data } = await api.get("/settings/classes");
      classes = data;
    } catch { classes = []; }
  }

  function validateClass() {
    const errs: Record<string, string> = {};
    if (newClass.level === "SHS" && !newClass.learning_area_id)
      errs.learning_area_id = "Learning area is required for SHS";
    return errs;
  }

  async function createClass() {
    classErrors = validateClass();
    if (Object.keys(classErrors).length) return;
    savingClass = true; classApiError = "";
    try {
      const payload: any = { level: newClass.level, stream: newClass.stream || null };
      if (newClass.level !== "Creche") payload.year = Number(newClass.year);
      if (newClass.level === "SHS") payload.learning_area_id = newClass.learning_area_id;
      await api.post("/settings/classes", payload);
      newClass = { level: "Basic", year: 1, learning_area_id: "", stream: "" };
      classErrors = {};
      addingClass = false;
      await loadClasses();
    } catch (e) { classApiError = apiError(e); }
    finally { savingClass = false; }
  }

  async function deleteClass(id: string) {
    try {
      await api.delete(`/settings/classes/${id}`);
      confirmDeleteClass = null;
      await loadClasses();
    } catch (e) { alert(apiError(e)); }
  }

  $: classGroups = classes.reduce((acc: Record<string, any[]>, c: any) => {
    (acc[c.education_level] ??= []).push(c);
    return acc;
  }, {});

  // ── Init ─────────────────────────────────────────────────────────
  onMount(async () => {
    await loadSchool();
    await loadYears();
    await loadClasses();
    if (school?.education_levels?.includes("SHS")) await loadLearningAreas();
  });
</script>

<svelte:head><title>Settings — TTEK-SIS</title></svelte:head>

<!-- Page header -->
<div class="page-header">
  <h1 class="page-title">Settings</h1>
  <p class="page-subtitle">Configure your school, academic calendar, classes and learning areas.</p>
</div>

<!-- Tabs -->
<div class="tabs">
  {#each [
    { id: "school",         label: "School",           icon: School2 },
    { id: "calendar",       label: "Academic Calendar", icon: CalendarDays },
    { id: "classes",        label: "Classes",           icon: LayoutGrid },
    ...(isSHS ? [{ id: "learning_areas", label: "Learning Areas", icon: BookOpen }] : []),
  ] as t}
    <button class="tab-btn" class:active={tab === t.id} on:click={() => tab = t.id as any}>
      <svelte:component this={t.icon} size={14} />
      {t.label}
    </button>
  {/each}
</div>


<!-- ══ SCHOOL PROFILE ══════════════════════════════════════════════ -->
{#if tab === "school"}
  <div class="card form-card max-w-lg">
    <h2 class="section-title" style="margin-bottom:18px;">School Profile</h2>

    {#if school}
      <form on:submit|preventDefault={saveSchool} novalidate>
        <div class="field-grid">
          {#each [
            { key: "name",     label: "School Name",  id: "s-name" },
            { key: "phone",    label: "Phone",         id: "s-phone" },
            { key: "email",    label: "Email",         id: "s-email" },
            { key: "address",  label: "Address",       id: "s-address" },
            { key: "region",   label: "Region",        id: "s-region" },
            { key: "district", label: "District",      id: "s-district" },
          ] as f}
            <div class="field">
              <label for={f.id}>{f.label}</label>
              <input id={f.id} class="input" bind:value={school[f.key]} />
            </div>
          {/each}

          <div class="field">
            <label for="s-accent">Accent Colour</label>
            <div class="color-row">
              <input type="color" id="s-accent" class="color-swatch" bind:value={school.accent_color} />
              <input class="input" bind:value={school.accent_color} placeholder="#185FA5" aria-label="Hex colour value" />
            </div>
          </div>
        </div>

        {#if schoolError}
          <div class="form-error" role="alert">
            <AlertCircle size={14} />{schoolError}
          </div>
        {/if}

        <div class="form-footer">
          <button type="submit" class="btn-primary" disabled={schoolSaving}>
            {#if schoolSaving}<Loader2 size={14} class="spin" />{/if}
            {schoolSaving ? "Saving…" : "Save changes"}
          </button>
          {#if schoolSuccess}
            <span class="success-text"><Check size={13} />Saved</span>
          {/if}
        </div>
      </form>
    {:else}
      <p class="text-muted">Loading school data…</p>
    {/if}
  </div>


<!-- ══ ACADEMIC CALENDAR ════════════════════════════════════════════ -->
{:else if tab === "calendar"}
  <div class="max-w-2xl">

    <div class="section-header">
      <h2 class="section-title">Academic Years</h2>
      <button class="btn-primary" on:click={() => { addingYear = !addingYear; yearErrors = {}; yearApiError = ""; }}>
        <Plus size={13} />{addingYear ? "Cancel" : "Add Year"}
      </button>
    </div>

    {#if addingYear}
      <div class="card form-card">
        <form on:submit|preventDefault={createYear} novalidate>
          <div class="grid-3">
            <div class="field">
              <label for="y-name">Name <span class="required">*</span></label>
              <input
                id="y-name" class="input" class:invalid={yearErrors.name}
                bind:value={newYear.name}
                aria-invalid={!!yearErrors.name}
                aria-describedby={yearErrors.name ? "y-name-err" : undefined}
                placeholder="2025/2026"
              />
              {#if yearErrors.name}<p id="y-name-err" class="field-error">{yearErrors.name}</p>{/if}
            </div>
            <div class="field">
              <label for="y-start">Start date <span class="required">*</span></label>
              <input
                type="date" id="y-start" class="input" class:invalid={yearErrors.start_date}
                bind:value={newYear.start_date}
                aria-invalid={!!yearErrors.start_date}
                aria-describedby={yearErrors.start_date ? "y-start-err" : undefined}
              />
              {#if yearErrors.start_date}<p id="y-start-err" class="field-error">{yearErrors.start_date}</p>{/if}
            </div>
            <div class="field">
              <label for="y-end">End date <span class="required">*</span></label>
              <input
                type="date" id="y-end" class="input" class:invalid={yearErrors.end_date}
                bind:value={newYear.end_date}
                aria-invalid={!!yearErrors.end_date}
                aria-describedby={yearErrors.end_date ? "y-end-err" : undefined}
              />
              {#if yearErrors.end_date}<p id="y-end-err" class="field-error">{yearErrors.end_date}</p>{/if}
            </div>
          </div>

          {#if yearApiError}
            <div class="form-error" role="alert"><AlertCircle size={14} />{yearApiError}</div>
          {/if}

          <div class="form-footer">
            <button type="submit" class="btn-primary" disabled={savingYear}>
              {#if savingYear}<Loader2 size={14} class="spin" />{/if}
              {savingYear ? "Saving…" : "Save year"}
            </button>
            <button type="button" class="btn-secondary" on:click={() => { addingYear = false; yearErrors = {}; }}>Cancel</button>
          </div>
        </form>
      </div>
    {/if}

    {#if years.length === 0 && !addingYear}
      <div class="empty-state">
        <CalendarDays size={28} />
        <p>No academic years yet.</p>
        <button class="btn-primary" on:click={() => addingYear = true}><Plus size={13} />Add your first year</button>
      </div>
    {/if}

    {#each years as year}
      <div class="card year-card">
        <!-- Year row -->
        <div
          class="year-header"
          role="button" tabindex="0"
          on:click={() => expandedYear = expandedYear === year.id ? null : year.id}
          on:keydown={(e) => e.key === "Enter" && (expandedYear = expandedYear === year.id ? null : year.id)}
        >
          <ChevronRight size={14} class="chevron{expandedYear === year.id ? ' open' : ''}" />
          <span class="year-name">{year.name}</span>
          <span class="year-dates">{year.start_date} – {year.end_date}</span>

          {#if year.is_current}
            <span class="badge-ok">Current</span>
          {:else}
            <button class="btn-link" on:click|stopPropagation={() => activateYear(year.id)}>Set current</button>
          {/if}

          <!-- Delete with inline confirmation -->
          {#if confirmDeleteYear === year.id}
            <span class="confirm-label">Delete?</span>
            <button class="btn-danger-sm" on:click|stopPropagation={() => deleteYear(year.id)}>Yes</button>
            <button class="btn-secondary-sm" on:click|stopPropagation={() => confirmDeleteYear = null}>No</button>
          {:else}
            <button class="btn-icon" title="Delete year"
              on:click|stopPropagation={() => { if (!year.is_current) confirmDeleteYear = year.id; }}
              disabled={year.is_current}
            ><Trash2 size={13} /></button>
          {/if}
        </div>

        <!-- Terms panel -->
        {#if expandedYear === year.id}
          <div class="terms-panel">
            {#if year.terms.length === 0}
              <p class="text-muted small">No terms added yet.</p>
            {/if}

            {#each year.terms as term}
              <div class="term-row">
                <span class="term-name">{term.name}</span>
                <span class="term-dates">{term.start_date} – {term.end_date}</span>

                {#if term.is_current}
                  <span class="badge-ok">Current</span>
                {:else}
                  <button class="btn-link" on:click={() => activateTerm(term.id)}>Set current</button>
                {/if}

                {#if confirmDeleteTerm === term.id}
                  <span class="confirm-label">Delete?</span>
                  <button class="btn-danger-sm" on:click={() => deleteTerm(term.id)}>Yes</button>
                  <button class="btn-secondary-sm" on:click={() => confirmDeleteTerm = null}>No</button>
                {:else}
                  <button class="btn-icon" title="Delete term"
                    on:click={() => { if (!term.is_current) confirmDeleteTerm = term.id; }}
                    disabled={term.is_current}
                  ><Trash2 size={12} /></button>
                {/if}
              </div>
            {/each}

            {#if addingTermFor === year.id}
              <div class="term-form">
                <div class="grid-3">
                  <div class="field">
                    <label for="t-name-{year.id}">Term name <span class="required">*</span></label>
                    <input
                      id="t-name-{year.id}" class="input" class:invalid={termErrors[year.id]?.name}
                      bind:value={newTerm[year.id].name} placeholder="Term 1"
                    />
                    {#if termErrors[year.id]?.name}<p class="field-error">{termErrors[year.id].name}</p>{/if}
                  </div>
                  <div class="field">
                    <label for="t-start-{year.id}">Start <span class="required">*</span></label>
                    <input type="date" id="t-start-{year.id}" class="input"
                      class:invalid={termErrors[year.id]?.start_date}
                      bind:value={newTerm[year.id].start_date} />
                    {#if termErrors[year.id]?.start_date}<p class="field-error">{termErrors[year.id].start_date}</p>{/if}
                  </div>
                  <div class="field">
                    <label for="t-end-{year.id}">End <span class="required">*</span></label>
                    <input type="date" id="t-end-{year.id}" class="input"
                      class:invalid={termErrors[year.id]?.end_date}
                      bind:value={newTerm[year.id].end_date} />
                    {#if termErrors[year.id]?.end_date}<p class="field-error">{termErrors[year.id].end_date}</p>{/if}
                  </div>
                </div>
                {#if termApiError}
                  <div class="form-error" role="alert"><AlertCircle size={14} />{termApiError}</div>
                {/if}
                <div class="form-footer">
                  <button class="btn-primary" on:click={() => createTerm(year.id)} disabled={savingTerm}>
                    {#if savingTerm}<Loader2 size={14} class="spin" />{/if}
                    {savingTerm ? "Saving…" : "Save term"}
                  </button>
                  <button class="btn-secondary" on:click={() => { addingTermFor = null; termErrors = {}; }}>Cancel</button>
                </div>
              </div>
            {:else}
              <button class="btn-link small" on:click={() => {
                addingTermFor = year.id;
                newTerm[year.id] = { name: "", start_date: "", end_date: "" };
                termErrors[year.id] = {};
              }}>
                <Plus size={12} /> Add term
              </button>
            {/if}
          </div>
        {/if}
      </div>
    {/each}
  </div>


<!-- ══ CLASSES ══════════════════════════════════════════════════════ -->
{:else if tab === "classes"}
  <div class="max-w-2xl">

    <div class="section-header">
      <h2 class="section-title">Classes</h2>
      <button class="btn-primary" on:click={() => { addingClass = !addingClass; classErrors = {}; classApiError = ""; }}>
        <Plus size={13} />{addingClass ? "Cancel" : "Add Class"}
      </button>
    </div>

    {#if addingClass}
      <div class="card form-card">
        <form on:submit|preventDefault={createClass} novalidate>
          <div class="grid-auto">
            <div class="field">
              <label for="c-level">Level</label>
              <select id="c-level" class="input" bind:value={newClass.level}>
                {#each LEVELS as l}<option>{l}</option>{/each}
              </select>
            </div>

            {#if newClass.level !== "Creche"}
              <div class="field">
                <label for="c-year">Year</label>
                <select id="c-year" class="input" bind:value={newClass.year}>
                  {#each newClassYears as y}<option value={y}>{y}</option>{/each}
                </select>
              </div>
            {/if}

            {#if newClass.level === "SHS"}
              <div class="field">
                <label for="c-la">Learning Area <span class="required">*</span></label>
                <select id="c-la" class="input" class:invalid={classErrors.learning_area_id}
                  bind:value={newClass.learning_area_id}
                  aria-invalid={!!classErrors.learning_area_id}
                >
                  <option value="">— select —</option>
                  {#each learningAreas as la}<option value={la.id}>{la.name}</option>{/each}
                </select>
                {#if classErrors.learning_area_id}
                  <p class="field-error">{classErrors.learning_area_id}</p>
                {/if}
              </div>
            {/if}

            <div class="field">
              <label for="c-stream">Stream <span class="optional">(optional)</span></label>
              <input id="c-stream" class="input" bind:value={newClass.stream} placeholder="A, Gold, Blue…" />
            </div>
          </div>

          {#if classApiError}
            <div class="form-error" role="alert"><AlertCircle size={14} />{classApiError}</div>
          {/if}

          <div class="form-footer">
            <button type="submit" class="btn-primary" disabled={savingClass}>
              {#if savingClass}<Loader2 size={14} class="spin" />{/if}
              {savingClass ? "Saving…" : "Create class"}
            </button>
            <button type="button" class="btn-secondary" on:click={() => { addingClass = false; classErrors = {}; }}>Cancel</button>
          </div>
        </form>
      </div>
    {/if}

    {#if classes.length === 0 && !addingClass}
      <div class="empty-state">
        <LayoutGrid size={28} />
        <p>No classes yet.</p>
        <button class="btn-primary" on:click={() => addingClass = true}><Plus size={13} />Add your first class</button>
      </div>
    {/if}

    {#each Object.entries(classGroups) as [level, group]}
      <div class="class-group">
        <div class="group-label">{LEVEL_LABELS[level] ?? level}</div>
        <div class="class-chips">
          {#each group as cls}
            <div class="chip" class:inactive={!cls.is_active}>
              <span class="chip-name">{cls.name}</span>
              {#if !cls.is_active}<span class="chip-badge">inactive</span>{/if}

              {#if confirmDeleteClass === cls.id}
                <span class="confirm-label">Delete?</span>
                <button class="btn-danger-xs" on:click={() => deleteClass(cls.id)}>Yes</button>
                <button class="btn-ghost-xs" on:click={() => confirmDeleteClass = null}>No</button>
              {:else}
                <button class="chip-del" title="Delete class" on:click={() => confirmDeleteClass = cls.id}>
                  <X size={11} />
                </button>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {/each}
  </div>


<!-- ══ LEARNING AREAS ═══════════════════════════════════════════════ -->
{:else if tab === "learning_areas"}
  <div class="max-w-lg">

    <div class="section-header">
      <div>
        <h2 class="section-title">Learning Areas</h2>
        <p class="section-subtitle">GES programmes offered at your SHS. Short codes appear in class names.</p>
      </div>
      <button class="btn-primary" on:click={() => { addingLA = !addingLA; laErrors = {}; laApiError = ""; }}>
        <Plus size={13} />{addingLA ? "Cancel" : "Add"}
      </button>
    </div>

    {#if addingLA}
      <div class="card form-card">
        <form on:submit|preventDefault={createLA} novalidate>
          <div class="grid-2">
            <div class="field">
              <label for="la-name">Learning Area <span class="required">*</span></label>
              <select id="la-name" class="input" class:invalid={laErrors.name}
                bind:value={newLA.name}
                aria-invalid={!!laErrors.name}
                aria-describedby={laErrors.name ? "la-name-err" : undefined}
              >
                <option value="">— select —</option>
                {#each GES_AREAS.filter(a => !learningAreas.find((l: any) => l.name === a)) as a}
                  <option>{a}</option>
                {/each}
              </select>
              {#if laErrors.name}<p id="la-name-err" class="field-error">{laErrors.name}</p>{/if}
            </div>
            <div class="field">
              <label for="la-code">Short code <span class="optional">(optional)</span></label>
              <input id="la-code" class="input" bind:value={newLA.short_name} placeholder="SCI, ART, BUS…" />
              <p class="field-hint">Used in class names, e.g. "2 SCI A"</p>
            </div>
          </div>

          {#if laApiError}
            <div class="form-error" role="alert"><AlertCircle size={14} />{laApiError}</div>
          {/if}

          <div class="form-footer">
            <button type="submit" class="btn-primary" disabled={savingLA}>
              {#if savingLA}<Loader2 size={14} class="spin" />{/if}
              {savingLA ? "Saving…" : "Add learning area"}
            </button>
            <button type="button" class="btn-secondary" on:click={() => { addingLA = false; laErrors = {}; }}>Cancel</button>
          </div>
        </form>
      </div>
    {/if}

    {#if learningAreas.length === 0 && !addingLA}
      <div class="empty-state">
        <BookOpen size={28} />
        <p>No learning areas configured yet.</p>
        <button class="btn-primary" on:click={() => addingLA = true}><Plus size={13} />Add first learning area</button>
      </div>
    {:else if learningAreas.length > 0}
      <div class="card list-card">
        {#each learningAreas as la, i}
          <div class="list-row" class:border-top={i > 0}>
            <div class="list-row-main">
              <div class="list-row-title">{la.name}</div>
              {#if editingLA !== la.id}
                <div class="list-row-sub">Code: {la.short_name ?? "—"}</div>
              {:else}
                <input class="input inline-input" bind:value={editLAShort} placeholder="e.g. ART"
                  aria-label="Short code for {la.name}" />
              {/if}
            </div>

            <div class="list-row-actions">
              {#if editingLA === la.id}
                <button class="btn-icon ok" title="Save" on:click={() => saveLA(la.id)} disabled={savingLAEdit}>
                  {#if savingLAEdit}<Loader2 size={13} class="spin" />{:else}<Check size={13} />{/if}
                </button>
                <button class="btn-icon" title="Cancel" on:click={() => editingLA = null}><X size={13} /></button>
              {:else if confirmDeleteLA === la.id}
                <span class="confirm-label">Delete?</span>
                <button class="btn-danger-sm" on:click={() => deleteLA(la.id)}>Yes</button>
                <button class="btn-secondary-sm" on:click={() => confirmDeleteLA = null}>No</button>
              {:else}
                <button class="btn-icon" title="Edit short code"
                  on:click={() => { editingLA = la.id; editLAShort = la.short_name ?? ""; }}>
                  <Pencil size={13} />
                </button>
                <button class="btn-icon danger" title="Delete" on:click={() => confirmDeleteLA = la.id}>
                  <Trash2 size={13} />
                </button>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
{/if}

<style>
  /* ── Layout ──────────────────────────────────────────────────── */
  .page-header { margin-bottom: 20px; }
  .page-title  { font-size: 17px; font-weight: 600; color: var(--tx-high); }
  .page-subtitle { font-size: 13px; color: var(--tx-low); margin-top: 3px; }

  .max-w-lg  { max-width: 560px; }
  .max-w-2xl { max-width: 680px; }

  /* ── Tabs ────────────────────────────────────────────────────── */
  .tabs {
    display: flex;
    gap: 2px;
    margin-bottom: 22px;
    border-bottom: 1px solid var(--border-subtle);
  }
  .tab-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 8px 14px;
    font-size: 13px; font-weight: 400;
    color: var(--tx-mid);
    border: none; border-bottom: 2px solid transparent;
    background: transparent; cursor: pointer;
    margin-bottom: -1px;
    transition: color 0.12s;
  }
  .tab-btn:hover { color: var(--tx-high); }
  .tab-btn.active { color: var(--accent); font-weight: 600; border-bottom-color: var(--accent); }

  /* ── Cards ───────────────────────────────────────────────────── */
  .card {
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius);
    box-shadow: var(--shadow-xs);
  }
  .card.form-card { padding: 20px; margin-bottom: 14px; }
  .card.list-card { overflow: hidden; }
  .year-card    { margin-bottom: 10px; overflow: hidden; }

  /* ── Section header ──────────────────────────────────────────── */
  .section-header {
    display: flex; align-items: flex-start; justify-content: space-between;
    margin-bottom: 14px; gap: 12px;
  }
  .section-title   { font-size: 14px; font-weight: 600; color: var(--tx-high); margin: 0; }
  .section-subtitle { font-size: 12px; color: var(--tx-low); margin-top: 2px; }

  /* ── Fields ──────────────────────────────────────────────────── */
  .field-grid { display: grid; gap: 14px; margin-bottom: 18px; }
  .grid-2     { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
  .grid-3     { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 14px; }
  .grid-auto  { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 14px; }

  @media (max-width: 600px) {
    .grid-2, .grid-3, .grid-auto { grid-template-columns: 1fr; }
  }

  .field { display: flex; flex-direction: column; gap: 4px; }
  .field label {
    font-size: 11.5px; font-weight: 500; color: var(--tx-low);
  }
  .required { color: var(--accent); }
  .optional  { color: var(--tx-low); font-weight: 400; font-size: 10.5px; }

  .input {
    width: 100%;
    padding: 7px 10px;
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-sm);
    background: var(--surface-1);
    color: var(--tx-high);
    font-size: 13px;
    outline: none;
    transition: border-color 0.12s, box-shadow 0.12s;
  }
  .input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 15%, transparent);
  }
  .input.invalid {
    border-color: var(--err-text);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--err-text) 12%, transparent);
  }
  .input.inline-input { width: 130px; margin-top: 4px; }

  select.input { cursor: pointer; }

  .field-error {
    font-size: 11.5px; color: var(--err-text);
    display: flex; align-items: center; gap: 4px;
    margin: 0;
  }
  .field-hint  { font-size: 11px; color: var(--tx-low); margin: 0; }

  /* ── Colour picker ───────────────────────────────────────────── */
  .color-row { display: flex; align-items: center; gap: 8px; }
  .color-swatch {
    width: 38px; height: 34px;
    padding: 2px; border: 1px solid var(--border-strong);
    border-radius: var(--radius-sm); cursor: pointer;
    flex-shrink: 0;
  }
  .color-row .input { flex: 1; }

  /* ── Form footer ─────────────────────────────────────────────── */
  .form-footer {
    display: flex; align-items: center; gap: 10px; margin-top: 18px;
  }
  .form-error {
    display: flex; align-items: center; gap: 7px;
    padding: 9px 12px; margin-top: 12px;
    border-radius: var(--radius-sm);
    background: var(--err-bg); color: var(--err-text);
    font-size: 13px;
  }
  .success-text {
    display: flex; align-items: center; gap: 5px;
    font-size: 13px; color: var(--ok-text);
  }

  /* ── Buttons ─────────────────────────────────────────────────── */
  .btn-primary {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 7px 16px;
    border-radius: var(--radius-sm);
    background: var(--accent); color: var(--accent-fg);
    border: none; font-size: 13px; font-weight: 500;
    cursor: pointer; white-space: nowrap;
    transition: opacity 0.12s;
  }
  .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

  .btn-secondary {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 7px 14px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-strong);
    background: transparent; color: var(--tx-mid);
    font-size: 13px; font-weight: 400; cursor: pointer;
    transition: background 0.12s;
  }
  .btn-secondary:hover { background: var(--surface-2); }

  .btn-icon {
    display: inline-flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 6px;
    border: none; background: transparent;
    color: var(--tx-low); cursor: pointer;
    transition: background 0.12s, color 0.12s;
  }
  .btn-icon:hover { background: var(--surface-2); color: var(--tx-high); }
  .btn-icon:disabled { opacity: 0.35; cursor: not-allowed; }
  .btn-icon.ok:hover  { color: var(--ok-text); }
  .btn-icon.danger:hover { color: var(--err-text); }

  .btn-link {
    background: none; border: none; padding: 0;
    color: var(--accent); font-size: 12px; font-weight: 500;
    cursor: pointer; white-space: nowrap;
  }
  .btn-link:hover { text-decoration: underline; }
  .btn-link.small { display: flex; align-items: center; gap: 4px; margin-top: 8px; font-size: 12px; }

  /* ── Delete confirmation inline buttons ──────────────────────── */
  .confirm-label  { font-size: 12px; color: var(--tx-mid); white-space: nowrap; }
  .btn-danger-sm {
    padding: 3px 9px; border-radius: 5px; font-size: 12px; font-weight: 600;
    border: none; background: var(--err-text); color: #fff; cursor: pointer;
  }
  .btn-secondary-sm {
    padding: 3px 9px; border-radius: 5px; font-size: 12px;
    border: 1px solid var(--border-strong); background: transparent;
    color: var(--tx-mid); cursor: pointer;
  }
  .btn-danger-xs {
    padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 600;
    border: none; background: var(--err-text); color: #fff; cursor: pointer;
  }
  .btn-ghost-xs {
    padding: 2px 7px; border-radius: 4px; font-size: 11px;
    border: 1px solid var(--border-strong); background: transparent;
    color: var(--tx-mid); cursor: pointer;
  }

  /* ── Academic year rows ──────────────────────────────────────── */
  .year-header {
    display: flex; align-items: center; gap: 10px;
    padding: 12px 16px; cursor: pointer;
    user-select: none;
  }
  .year-header:hover { background: var(--surface-2); }
  .year-name  { font-size: 13px; font-weight: 600; color: var(--tx-high); flex: 1; }
  .year-dates { font-size: 11.5px; color: var(--tx-low); white-space: nowrap; }

  :global(.chevron) { color: var(--tx-low); transition: transform 0.15s; flex-shrink: 0; }
  :global(.chevron.open) { transform: rotate(90deg); }

  .terms-panel {
    border-top: 1px solid var(--border-subtle);
    padding: 12px 16px 14px;
    background: var(--surface-0);
  }
  .term-row {
    display: flex; align-items: center; gap: 10px;
    padding: 7px 10px; border-radius: 6px;
    background: var(--surface-1);
    margin-bottom: 6px;
  }
  .term-name  { font-size: 13px; font-weight: 500; color: var(--tx-high); flex: 1; }
  .term-dates { font-size: 11.5px; color: var(--tx-low); white-space: nowrap; }
  .term-form  { margin-top: 12px; padding: 14px; border-radius: var(--radius-sm); background: var(--surface-1); }

  /* ── Badges ──────────────────────────────────────────────────── */
  .badge-ok {
    font-size: 11px; font-weight: 600;
    padding: 2px 8px; border-radius: 4px;
    background: var(--ok-bg); color: var(--ok-text);
    white-space: nowrap;
  }

  /* ── Class chips ─────────────────────────────────────────────── */
  .class-group { margin-bottom: 18px; }
  .group-label {
    font-size: 11px; font-weight: 600; letter-spacing: .07em;
    text-transform: uppercase; color: var(--tx-low); margin-bottom: 8px;
  }
  .class-chips { display: flex; flex-wrap: wrap; gap: 8px; }
  .chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 10px;
    border-radius: 6px;
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
  }
  .chip.inactive { opacity: 0.55; }
  .chip-name  { font-size: 13px; font-weight: 500; color: var(--tx-high); }
  .chip-badge { font-size: 10px; color: var(--tx-low); }
  .chip-del {
    display: inline-flex; align-items: center; justify-content: center;
    width: 18px; height: 18px; border-radius: 4px;
    border: none; background: transparent; color: var(--tx-low);
    cursor: pointer; transition: background 0.1s, color 0.1s;
  }
  .chip-del:hover { background: var(--err-bg); color: var(--err-text); }

  /* ── List rows (learning areas) ──────────────────────────────── */
  .list-row {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 16px;
  }
  .list-row.border-top { border-top: 1px solid var(--border-subtle); }
  .list-row-main  { flex: 1; min-width: 0; }
  .list-row-title { font-size: 13px; font-weight: 500; color: var(--tx-high); }
  .list-row-sub   { font-size: 12px; color: var(--tx-low); margin-top: 1px; }
  .list-row-actions { display: flex; align-items: center; gap: 4px; }

  /* ── Empty state ─────────────────────────────────────────────── */
  .empty-state {
    display: flex; flex-direction: column; align-items: center;
    gap: 10px; padding: 44px 20px; text-align: center;
    color: var(--tx-low);
    border: 1px dashed var(--border-subtle);
    border-radius: var(--radius);
  }
  .empty-state p { font-size: 14px; color: var(--tx-mid); margin: 0; }

  /* ── Misc ────────────────────────────────────────────────────── */
  .text-muted { font-size: 13px; color: var(--tx-low); }
  .small      { font-size: 12px; }

  :global(.spin) {
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }
</style>
