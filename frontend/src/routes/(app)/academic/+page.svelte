<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { api } from "$api/client";
  import { toast } from "$stores/toast";
  import { confirmDialog } from "$stores/confirm";
  import Button     from "$components/ui/Button.svelte";
  import Badge      from "$components/ui/Badge.svelte";
  import Spinner    from "$components/ui/Spinner.svelte";
  import EmptyState from "$components/ui/EmptyState.svelte";
  import PageHeader from "$components/ui/PageHeader.svelte";
  import {
    CalendarDays, LayoutGrid, BookOpen,
    Plus, Trash2, ChevronDown,
    AlertCircle, X, Search, SlidersHorizontal,
  } from "@lucide/svelte";

  // ── Types ─────────────────────────────────────────────────────────
  interface AcademicTerm {
    id: string; name: string; start_date: string; end_date: string; is_current: boolean;
  }
  interface AcademicYear {
    id: string; name: string; start_date: string; end_date: string;
    is_current: boolean; terms: AcademicTerm[];
  }
  interface LearningArea { id: string; name: string; short_name: string | null; is_active: boolean; }
  interface SchoolClass {
    id: string; name: string; level: string; year: number | null;
    education_level: string; stream: string | null; is_active: boolean;
    learning_area: LearningArea | null;
  }

  // ── Tab ───────────────────────────────────────────────────────────
  let tab: "calendar" | "classes" | "learning_areas" = "calendar";

  function apiError(e: unknown): string {
    const err = e as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail ?? "Something went wrong. Try again.";
  }

  async function confirmDelete(title: string, message: string, fn: () => Promise<void>) {
    const ok = await confirmDialog.show({ title, message, variant: "danger", confirmLabel: "Delete" });
    if (!ok) return;
    try { await fn(); }
    catch (e) { toast.error(apiError(e)); }
  }

  const LEVEL_LABELS: Record<string, string> = {
    EARLY_CHILDHOOD: "Early Childhood", BASIC: "Basic",
    SHS: "Senior High School", TECHNICAL: "Technical", JHS: "Junior High School",
  };

  // ── School education levels (needed for SHS-only features) ────────
  let schoolEdLevels: string[] = [];
  $: isSHS = schoolEdLevels.includes("SHS");
  $: if (!isSHS && tab === "learning_areas") tab = "calendar";

  async function loadSchoolLevels() {
    try {
      const { data } = await api.get("/settings/school");
      schoolEdLevels = data.education_levels ?? [];
    } catch { schoolEdLevels = []; }
  }

  // ── Academic years ────────────────────────────────────────────────
  let years: AcademicYear[] = [];
  let newYear = { name: "", start_date: "", end_date: "" };
  let yearErrors: Record<string, string> = {};
  let addingYear = false;
  let savingYear = false;
  let yearApiError = "";

  async function loadYears() {
    try { const { data } = await api.get("/settings/academic-years"); years = data.items; }
    catch { years = []; }
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
      yearErrors = {}; addingYear = false;
      await loadYears();
      toast.success("Academic year created");
    } catch (e) { yearApiError = apiError(e); }
    finally { savingYear = false; }
  }

  async function activateYear(id: string) {
    try { await api.post(`/settings/academic-years/${id}/activate`); await loadYears(); }
    catch (e) { toast.error(apiError(e)); }
  }

  async function deleteYear(id: string) {
    try { await api.delete(`/settings/academic-years/${id}`); await loadYears(); toast.success("Year deleted"); }
    catch (e) { toast.error(apiError(e)); }
  }

  // ── Terms ─────────────────────────────────────────────────────────
  let expandedYear: string | null = null;
  let newTerm: Record<string, { name: string; start_date: string; end_date: string }> = {};
  let termErrors: Record<string, Record<string, string>> = {};
  let addingTermFor: string | null = null;
  let savingTerm = false;
  let termApiError = "";

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
      termErrors[yearId] = {}; addingTermFor = null;
      await loadYears();
      toast.success("Term created");
    } catch (e) { termApiError = apiError(e); }
    finally { savingTerm = false; }
  }

  async function activateTerm(termId: string) {
    try { await api.post(`/settings/terms/${termId}/activate`); await loadYears(); }
    catch (e) { toast.error(apiError(e)); }
  }

  async function deleteTerm(termId: string) {
    try { await api.delete(`/settings/terms/${termId}`); await loadYears(); toast.success("Term deleted"); }
    catch (e) { toast.error(apiError(e)); }
  }

  // ── Learning areas ────────────────────────────────────────────────
  const GES_AREAS = [
    "Science", "General Arts", "Business", "Applied Technology",
    "Home Economics", "Visual and Performing Arts", "Agriculture",
    "Languages", "Global Studies", "Engineering", "Biomedical Science",
    "Manufacturing", "Information Technology", "Computer Science",
    "Robotics", "Aviation and Aerospace",
  ];
  let learningAreas: LearningArea[] = [];
  let newLA = { name: "", short_name: "" };
  let laErrors: Record<string, string> = {};
  let addingLA = false;
  let savingLA = false;
  let laApiError = "";
  let editingLA: string | null = null;
  let editLAShort = "";
  let savingLAEdit = false;
  let laEditError = "";

  async function loadLearningAreas() {
    try { const { data } = await api.get("/settings/learning-areas"); learningAreas = data.items; }
    catch { learningAreas = []; }
  }

  async function createLA() {
    laErrors = {};
    if (!newLA.name) laErrors.name = "Please select a learning area";
    if (Object.keys(laErrors).length) return;
    savingLA = true; laApiError = "";
    try {
      await api.post("/settings/learning-areas", { name: newLA.name, short_name: newLA.short_name || null });
      newLA = { name: "", short_name: "" }; addingLA = false;
      await loadLearningAreas();
      toast.success("Learning area added");
    } catch (e) { laApiError = apiError(e); }
    finally { savingLA = false; }
  }

  async function saveLA(id: string) {
    savingLAEdit = true; laEditError = "";
    try {
      await api.patch(`/settings/learning-areas/${id}`, { short_name: editLAShort || null });
      editingLA = null;
      await loadLearningAreas();
      toast.success("Code updated");
    } catch (e) { laEditError = apiError(e); }
    finally { savingLAEdit = false; }
  }

  async function deleteLA(id: string) {
    try { await api.delete(`/settings/learning-areas/${id}`); await loadLearningAreas(); toast.success("Learning area removed"); }
    catch (e) { toast.error(apiError(e)); }
  }

  // ── Classes ───────────────────────────────────────────────────────
  const LEVELS = ["Creche", "Nursery", "KG", "Basic", "SHS"];
  const LEVEL_EDU_MAP: Record<string, string> = {
    Creche: "EARLY_CHILDHOOD", Nursery: "EARLY_CHILDHOOD", KG: "EARLY_CHILDHOOD",
    Basic: "BASIC", SHS: "SHS",
  };
  const YEAR_BOUNDS: Record<string, [number, number]> = {
    Nursery: [1, 2], KG: [1, 2], Basic: [1, 9], SHS: [1, 3],
  };

  $: availableLevels = LEVELS.filter(l => schoolEdLevels.includes(LEVEL_EDU_MAP[l]));
  $: if (availableLevels.length && !availableLevels.includes(newClass.level)) {
    newClass = { ...newClass, level: availableLevels[0] };
  }

  let classes: SchoolClass[] = [];
  let newClass = { level: "Basic", year: 1, learning_area_id: "", stream: "" };
  let classErrors: Record<string, string> = {};
  let addingClass = false;
  let savingClass = false;
  let classApiError = "";

  $: newClassYears = newClass.level in YEAR_BOUNDS
    ? Array.from({ length: YEAR_BOUNDS[newClass.level][1] - YEAR_BOUNDS[newClass.level][0] + 1 },
        (_, i) => i + YEAR_BOUNDS[newClass.level][0])
    : [];

  $: if (newClass.level === "SHS" && learningAreas.length === 0) loadLearningAreas();

  async function loadClasses() {
    try { const { data } = await api.get("/settings/classes"); classes = data.items; }
    catch { classes = []; }
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
      const payload: Record<string, unknown> = { level: newClass.level, stream: newClass.stream || null };
      if (newClass.level !== "Creche") payload.year = Number(newClass.year);
      if (newClass.level === "SHS") payload.learning_area_id = newClass.learning_area_id;
      await api.post("/settings/classes", payload);
      newClass = { level: "Basic", year: 1, learning_area_id: "", stream: "" };
      classErrors = {}; addingClass = false;
      await loadClasses();
      toast.success("Class created");
    } catch (e) { classApiError = apiError(e); }
    finally { savingClass = false; }
  }

  async function deleteClass(id: string) {
    try { await api.delete(`/settings/classes/${id}`); await loadClasses(); toast.success("Class deleted"); }
    catch (e) { toast.error(apiError(e)); }
  }

  // ── Class filters ─────────────────────────────────────────────────
  let classSearch = "";
  let classFilterLevel = "all";
  let classFilterStatus: "all" | "active" | "inactive" = "all";

  $: filteredClasses = classes.filter(c => {
    if (classFilterLevel !== "all" && c.education_level !== classFilterLevel) return false;
    if (classFilterStatus === "active" && !c.is_active) return false;
    if (classFilterStatus === "inactive" && c.is_active) return false;
    if (classSearch) {
      const q = classSearch.toLowerCase();
      if (!c.name.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  $: classFilterCount =
    (classFilterLevel !== "all" ? 1 : 0) +
    (classFilterStatus !== "all" ? 1 : 0) +
    (classSearch ? 1 : 0);

  $: uniqueEdLevels = [...new Set(classes.map(c => c.education_level))].sort();

  // ── Init ──────────────────────────────────────────────────────────
  onMount(async () => {
    const urlTab = $page.url.searchParams.get("tab");
    if (urlTab === "classes" || urlTab === "learning_areas" || urlTab === "calendar") {
      tab = urlTab;
    }
    await loadSchoolLevels();
    await loadYears();
    await loadClasses();
    await loadLearningAreas();
  });
</script>

<svelte:head><title>Academic — TTEK-SIS</title></svelte:head>

<div class="academic-root">

  <!-- ── Tab bar ───────────────────────────────────────────────────── -->
  <div class="tabs-bar">
    <button class="tab" class:active={tab === "calendar"} on:click={() => tab = "calendar"}>
      <CalendarDays size={14} /><span class="tab-label">Academic Calendar</span>
    </button>
    {#if isSHS}
      <button class="tab" class:active={tab === "learning_areas"} on:click={() => tab = "learning_areas"}>
        <BookOpen size={14} /><span class="tab-label">Learning Areas</span>
      </button>
    {/if}
    <button class="tab" class:active={tab === "classes"} on:click={() => tab = "classes"}>
      <LayoutGrid size={14} /><span class="tab-label">Classes</span>
    </button>
  </div>

  <!-- ── Content ───────────────────────────────────────────────────── -->
  <div class="content">

    <!-- ══ ACADEMIC CALENDAR ══════════════════════════════════════════ -->
    {#if tab === "calendar"}
      <PageHeader title="Academic Calendar" description="Manage academic years and their terms.">
        <Button on:click={() => { addingYear = !addingYear; yearErrors = {}; yearApiError = ""; }}>
          <Plus size={13} />{addingYear ? "Cancel" : "Add Year"}
        </Button>
      </PageHeader>

      {#if addingYear}
        <div class="card" style="margin-bottom:14px;">
          <div class="card-body">
            <h3 class="card-title" style="margin-bottom:16px;">New Academic Year</h3>
            <div class="form-grid">
              <div class="field">
                <label for="y-name">Year name <span class="req">*</span></label>
                <input id="y-name" class="input" class:invalid={yearErrors.name}
                  bind:value={newYear.name} placeholder="2024/2025" />
                {#if yearErrors.name}<p class="ferr">{yearErrors.name}</p>{/if}
              </div>
              <div class="field">
                <label for="y-start">Start date <span class="req">*</span></label>
                <input id="y-start" type="date" class="input" class:invalid={yearErrors.start_date}
                  bind:value={newYear.start_date} />
                {#if yearErrors.start_date}<p class="ferr">{yearErrors.start_date}</p>{/if}
              </div>
              <div class="field">
                <label for="y-end">End date <span class="req">*</span></label>
                <input id="y-end" type="date" class="input" class:invalid={yearErrors.end_date}
                  bind:value={newYear.end_date} />
                {#if yearErrors.end_date}<p class="ferr">{yearErrors.end_date}</p>{/if}
              </div>
            </div>
            {#if yearApiError}<div class="api-err"><AlertCircle size={13} />{yearApiError}</div>{/if}
            <div class="actions">
              <Button on:click={createYear} loading={savingYear}>
                {savingYear ? "Creating…" : "Create year"}
              </Button>
              <Button variant="ghost" on:click={() => { addingYear = false; yearErrors = {}; }}>Cancel</Button>
            </div>
          </div>
        </div>
      {/if}

      {#if years.length === 0 && !addingYear}
        <EmptyState message="No academic years yet.">
          <svelte:fragment slot="icon"><CalendarDays size={28} /></svelte:fragment>
          <Button on:click={() => addingYear = true}><Plus size={13} />Add your first year</Button>
        </EmptyState>
      {/if}

      {#each years as year}
        <div class="year-card" class:is-current={year.is_current}>
          <div class="year-head">
            <div class="year-head-l">
              <button class="expand-btn"
                on:click={() => expandedYear = expandedYear === year.id ? null : year.id}
                aria-expanded={expandedYear === year.id}>
                <ChevronDown size={14} class="chevron {expandedYear === year.id ? 'open' : ''}" />
              </button>
              <div>
                <div class="year-name">{year.name}</div>
                <div class="year-dates">{year.start_date} – {year.end_date}</div>
              </div>
            </div>
            <div class="year-head-r">
              {#if year.is_current}
                <Badge variant="ok" size="sm">Current</Badge>
              {:else}
                <Button variant="link" on:click={() => activateYear(year.id)}>Set current</Button>
              {/if}
              <span class="pill">{year.terms?.length ?? 0} term{year.terms?.length !== 1 ? "s" : ""}</span>
              <Button
                variant="icon"
                ariaLabel="Delete year"
                disabled={year.is_current}
                on:click={() => confirmDelete(
                  "Delete academic year?",
                  `"${year.name}" and all its terms will be permanently removed.`,
                  () => deleteYear(year.id)
                )}
              ><Trash2 size={13} /></Button>
            </div>
          </div>

          {#if expandedYear === year.id}
            <div class="terms-panel">
              {#if year.terms?.length > 0}
                {#each year.terms as term}
                  <div class="term-row">
                    <div class="term-l">
                      <span class="tdot" class:active={term.is_current}></span>
                      <span class="term-name">{term.name}</span>
                      <span class="term-dates">{term.start_date} – {term.end_date}</span>
                    </div>
                    <div class="term-r">
                      {#if term.is_current}
                        <Badge variant="ok" size="sm">Current</Badge>
                      {:else}
                        <Button variant="link" on:click={() => activateTerm(term.id)}>Set current</Button>
                      {/if}
                      <Button
                        variant="icon"
                        ariaLabel="Delete term"
                        disabled={term.is_current}
                        on:click={() => confirmDelete(
                          "Delete term?",
                          `"${term.name}" will be permanently removed.`,
                          () => deleteTerm(term.id)
                        )}
                      ><Trash2 size={12} /></Button>
                    </div>
                  </div>
                {/each}
              {:else}
                <p class="terms-empty">No terms added yet.</p>
              {/if}

              {#if addingTermFor === year.id}
                <div class="term-form">
                  <div class="form-grid">
                    <div class="field">
                      <label for="t-name-{year.id}">Term name <span class="req">*</span></label>
                      <input id="t-name-{year.id}" class="input" class:invalid={termErrors[year.id]?.name}
                        bind:value={newTerm[year.id].name} placeholder="Term 1" />
                      {#if termErrors[year.id]?.name}<p class="ferr">{termErrors[year.id].name}</p>{/if}
                    </div>
                    <div class="field">
                      <label for="t-start-{year.id}">Start date <span class="req">*</span></label>
                      <input id="t-start-{year.id}" type="date" class="input" class:invalid={termErrors[year.id]?.start_date}
                        bind:value={newTerm[year.id].start_date} />
                      {#if termErrors[year.id]?.start_date}<p class="ferr">{termErrors[year.id].start_date}</p>{/if}
                    </div>
                    <div class="field">
                      <label for="t-end-{year.id}">End date <span class="req">*</span></label>
                      <input id="t-end-{year.id}" type="date" class="input" class:invalid={termErrors[year.id]?.end_date}
                        bind:value={newTerm[year.id].end_date} />
                      {#if termErrors[year.id]?.end_date}<p class="ferr">{termErrors[year.id].end_date}</p>{/if}
                    </div>
                  </div>
                  {#if termApiError}<div class="api-err"><AlertCircle size={13} />{termApiError}</div>{/if}
                  <div class="actions">
                    <Button on:click={() => createTerm(year.id)} loading={savingTerm}>
                      {savingTerm ? "Saving…" : "Save term"}
                    </Button>
                    <Button variant="ghost" on:click={() => { addingTermFor = null; termErrors = {}; }}>Cancel</Button>
                  </div>
                </div>
              {:else}
                <button class="add-term-btn" on:click={() => {
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


    <!-- ══ LEARNING AREAS ══════════════════════════════════════════════ -->
    {:else if tab === "learning_areas"}
      <PageHeader title="Learning Areas" description="GES programmes offered at SHS. Short codes appear in class names.">
        <Button on:click={() => { addingLA = !addingLA; laErrors = {}; laApiError = ""; }}>
          <Plus size={13} />{addingLA ? "Cancel" : "Add Area"}
        </Button>
      </PageHeader>

      {#if addingLA}
        <div class="card" style="margin-bottom:14px;">
          <div class="card-body">
            <h3 class="card-title" style="margin-bottom:16px;">New Learning Area</h3>
            <div class="form-grid">
              <div class="field">
                <label for="la-name">Learning Area <span class="req">*</span></label>
                <select id="la-name" class="input" class:invalid={laErrors.name} bind:value={newLA.name}>
                  <option value="">— select —</option>
                  {#each GES_AREAS.filter(a => !learningAreas.find((l) => l.name === a)) as a}
                    <option>{a}</option>
                  {/each}
                </select>
                {#if laErrors.name}<p class="ferr">{laErrors.name}</p>{/if}
              </div>
              <div class="field">
                <label for="la-code">Short Code <span class="opt">(optional)</span></label>
                <input id="la-code" class="input" bind:value={newLA.short_name} placeholder="SCI, ART, BUS…" />
                <p class="hint">Used in class names e.g. "SHS 2 SCI A"</p>
              </div>
            </div>
            {#if laApiError}<div class="api-err"><AlertCircle size={13} />{laApiError}</div>{/if}
            <div class="actions">
              <Button on:click={createLA} loading={savingLA}>
                {savingLA ? "Adding…" : "Add learning area"}
              </Button>
              <Button variant="ghost" on:click={() => { addingLA = false; laErrors = {}; }}>Cancel</Button>
            </div>
          </div>
        </div>
      {/if}

      {#if learningAreas.length === 0 && !addingLA}
        <EmptyState message="No learning areas configured yet.">
          <svelte:fragment slot="icon"><BookOpen size={28} /></svelte:fragment>
          <Button on:click={() => addingLA = true}><Plus size={13} />Add first learning area</Button>
        </EmptyState>
      {:else if learningAreas.length > 0}
        <div class="card">
          {#each learningAreas as la, i}
            <div class="la-row" class:border-t={i > 0}>
              <div class="la-main">
                <span class="la-name">{la.name}</span>
                {#if editingLA !== la.id}
                  <span class="la-code">{la.short_name ?? "No code"}</span>
                {:else}
                  <div>
                    <input class="input" style="width:110px;"
                      bind:value={editLAShort} placeholder="e.g. ART" />
                    {#if laEditError}<p class="ferr">{laEditError}</p>{/if}
                  </div>
                {/if}
              </div>
              <div class="la-actions">
                {#if editingLA === la.id}
                  <Button variant="icon" ariaLabel="Save code" on:click={() => saveLA(la.id)} loading={savingLAEdit}>
                    <svelte:fragment>✓</svelte:fragment>
                  </Button>
                  <Button variant="icon" ariaLabel="Cancel edit" on:click={() => { editingLA = null; laEditError = ""; }}>
                    <X size={13} />
                  </Button>
                {:else}
                  <Button variant="icon" ariaLabel="Edit code"
                    on:click={() => { editingLA = la.id; editLAShort = la.short_name ?? ""; laEditError = ""; }}>
                    ✎
                  </Button>
                  <Button variant="icon" ariaLabel="Delete {la.name}"
                    on:click={() => confirmDelete(
                      "Remove learning area?",
                      `"${la.name}" will be removed. Classes using it will retain their existing data.`,
                      () => deleteLA(la.id)
                    )}
                  ><Trash2 size={13} /></Button>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}


    <!-- ══ CLASSES ════════════════════════════════════════════════════ -->
    {:else if tab === "classes"}
      <PageHeader title="Classes" description="Define the class structure offered at your school.">
        <Button on:click={() => { addingClass = !addingClass; classErrors = {}; classApiError = ""; }}>
          <Plus size={13} />{addingClass ? "Cancel" : "Add Class"}
        </Button>
      </PageHeader>

      {#if addingClass}
        <div class="card" style="margin-bottom:14px;">
          <div class="card-body">
            <h3 class="card-title" style="margin-bottom:16px;">New Class</h3>
            <div class="class-form-grid">
              <div class="field">
                <label for="c-level">Level</label>
                <select id="c-level" class="input" bind:value={newClass.level}>
                  {#each availableLevels as l}<option>{l}</option>{/each}
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
                  <label for="c-la">Learning Area <span class="req">*</span></label>
                  <select id="c-la" class="input" class:invalid={classErrors.learning_area_id}
                    bind:value={newClass.learning_area_id}>
                    <option value="">— select —</option>
                    {#each learningAreas as la}<option value={la.id}>{la.name}</option>{/each}
                  </select>
                  {#if classErrors.learning_area_id}<p class="ferr">{classErrors.learning_area_id}</p>{/if}
                </div>
              {/if}
              <div class="field">
                <label for="c-stream">Stream <span class="opt">(optional)</span></label>
                <input id="c-stream" class="input" bind:value={newClass.stream} placeholder="A, Gold, Blue…" />
              </div>
            </div>
            {#if classApiError}<div class="api-err"><AlertCircle size={13} />{classApiError}</div>{/if}
            <div class="actions">
              <Button on:click={createClass} loading={savingClass}>
                {savingClass ? "Creating…" : "Create class"}
              </Button>
              <Button variant="ghost" on:click={() => { addingClass = false; classErrors = {}; }}>Cancel</Button>
            </div>
          </div>
        </div>
      {/if}

      {#if classes.length === 0 && !addingClass}
        <EmptyState message="No classes configured yet.">
          <svelte:fragment slot="icon"><LayoutGrid size={28} /></svelte:fragment>
          <Button on:click={() => addingClass = true}><Plus size={13} />Add your first class</Button>
        </EmptyState>
      {:else if classes.length > 0}
        <!-- Filter bar -->
        <div class="cl-filters">
          <div class="cl-search-wrap">
            <Search size={13} style="position:absolute;left:10px;color:var(--tx-low);pointer-events:none;" />
            <input
              class="cl-search"
              placeholder="Search classes…"
              bind:value={classSearch}
            />
            {#if classSearch}
              <button class="cl-clear-search" on:click={() => classSearch = ""} aria-label="Clear search">
                <X size={11} />
              </button>
            {/if}
          </div>

          <select class="cl-select" bind:value={classFilterLevel}>
            <option value="all">All levels</option>
            {#each uniqueEdLevels as lvl}
              <option value={lvl}>{LEVEL_LABELS[lvl] ?? lvl}</option>
            {/each}
          </select>

          <select class="cl-select" bind:value={classFilterStatus}>
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>

          {#if classFilterCount > 0}
            <button class="cl-clear-btn" on:click={() => {
              classSearch = ""; classFilterLevel = "all"; classFilterStatus = "all";
            }}>
              Clear{classFilterCount > 1 ? ` (${classFilterCount})` : ""}
            </button>
          {/if}

          <span class="cl-count">{filteredClasses.length} of {classes.length}</span>
        </div>

        <!-- List -->
        {#if filteredClasses.length === 0}
          <div class="cl-empty">
            <SlidersHorizontal size={22} />
            <p>No classes match your filters.</p>
            <button class="cl-clear-btn" on:click={() => {
              classSearch = ""; classFilterLevel = "all"; classFilterStatus = "all";
            }}>Clear filters</button>
          </div>
        {:else}
          <div class="cl-list">
            <div class="cl-list-head">
              <span class="clh-name">Class</span>
              <span class="clh-level">Level</span>
              <span class="clh-area">Programme</span>
              <span class="clh-stream">Stream</span>
              <span class="clh-status">Status</span>
              <span class="clh-action"></span>
            </div>
            {#each filteredClasses as cls (cls.id)}
              <a href="/academic/classes/{cls.id}" class="cl-row" class:cl-row-inactive={!cls.is_active}>
                <span class="cl-name">{cls.name}</span>
                <span class="cl-level">
                  <span class="cl-level-badge cl-level-{cls.education_level.toLowerCase()}">{cls.level}</span>
                </span>
                <span class="cl-area">{cls.learning_area?.name ?? "—"}</span>
                <span class="cl-stream">{cls.stream ?? "—"}</span>
                <span class="cl-status">
                  {#if cls.is_active}
                    <span class="status-dot active"></span><span class="status-label">Active</span>
                  {:else}
                    <span class="status-dot inactive"></span><span class="status-label">Inactive</span>
                  {/if}
                </span>
                <!-- svelte-ignore a11y-click-events-have-key-events -->
                <!-- svelte-ignore a11y-no-static-element-interactions -->
                <span class="cl-action" on:click|stopPropagation>
                  <button class="cl-del-btn" aria-label="Delete {cls.name}"
                    on:click={() => confirmDelete(
                      "Delete class?",
                      `"${cls.name}" will be permanently removed.`,
                      () => deleteClass(cls.id)
                    )}
                  ><Trash2 size={13} /></button>
                </span>
              </a>
            {/each}
          </div>
        {/if}
      {/if}
    {/if}

  </div><!-- /content -->
</div><!-- /academic-root -->

<style>
.academic-root { display: flex; flex-direction: column; min-height: 100%; }

/* ── Tab bar ─────────────────────────────────────────────────────── */
.tabs-bar {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 24px;
  overflow-x: auto;
  scrollbar-width: none;
}
.tabs-bar::-webkit-scrollbar { display: none; }

.tab {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 10px 16px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--tx-low);
  font-size: 13px;
  font-weight: 400;
  cursor: pointer;
  transition: color 0.12s, border-color 0.12s;
  margin-bottom: -1px;
  white-space: nowrap;
  flex-shrink: 0;
}
.tab:hover { color: var(--tx-mid); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 500; }
@media (max-width: 480px) {
  .tab { padding: 10px 12px; }
  .tab-label { display: none; }
}

/* ── Content ─────────────────────────────────────────────────────── */
.content { width: 100%; }

/* ── Cards ───────────────────────────────────────────────────────── */
.card {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 14px;
}
.card-title { font-size: 13px; font-weight: 600; color: var(--tx-high); margin: 0 0 2px; }
.card-body { padding: 16px 18px; }

/* ── Form helpers ─────────────────────────────────────────────────── */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}
.field { display: flex; flex-direction: column; gap: 5px; }

label {
  font-size: 12px; font-weight: 600; color: var(--tx-mid);
  letter-spacing: 0.01em; user-select: none;
}
.req { color: var(--accent); margin-left: 2px; }
.opt { font-weight: 400; font-size: 11px; color: var(--tx-low); }

.input {
  width: 100%; height: 34px; padding: 0 11px;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  background: var(--surface-0);
  color: var(--tx-high);
  font-size: 13px; font-family: inherit;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
  appearance: none; -webkit-appearance: none;
}
.input::placeholder { color: var(--tx-placeholder); }
.input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 13%, transparent);
}
.input.invalid { border-color: var(--err-text); }

select.input {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2396938B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 28px; cursor: pointer;
}

.ferr { font-size: 11.5px; color: var(--err-text); margin: 0; }
.hint { font-size: 11.5px; color: var(--tx-low); margin: 0; line-height: 1.4; }

.actions { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; }

.api-err {
  display: flex; align-items: center; gap: 7px;
  padding: 8px 12px; border-radius: 6px;
  background: var(--err-bg); color: var(--err-text);
  font-size: 12.5px; margin-top: 10px;
  border: 1px solid color-mix(in srgb, var(--err-text) 18%, transparent);
}

/* ── Academic Calendar ───────────────────────────────────────────── */
.year-card {
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: var(--surface-1);
  margin-bottom: 10px;
  overflow: hidden;
}
.year-card.is-current { border-color: color-mix(in srgb, var(--accent) 35%, var(--border-subtle)); }

.year-head {
  display: flex; align-items: center; justify-content: space-between;
  gap: 10px; padding: 12px 14px;
}
.year-head-l { display: flex; align-items: center; gap: 10px; }
.year-head-r { display: flex; align-items: center; gap: 8px; }
.year-name  { font-size: 13.5px; font-weight: 600; color: var(--tx-high); }
.year-dates { font-size: 11.5px; color: var(--tx-low); margin-top: 1px; }

.expand-btn {
  width: 26px; height: 26px; border-radius: 6px;
  border: none; background: transparent;
  display: flex; align-items: center; justify-content: center;
  color: var(--tx-low); cursor: pointer; flex-shrink: 0;
}
.expand-btn:hover { background: var(--surface-2); }
:global(.chevron) { transition: transform 0.18s ease; }
:global(.chevron.open) { transform: rotate(180deg); }

.pill {
  font-size: 11px; font-weight: 500;
  padding: 2px 7px; border-radius: 5px;
  background: var(--surface-2); color: var(--tx-low);
  border: 1px solid var(--border-subtle);
}

.terms-panel {
  border-top: 1px solid var(--border-subtle);
  padding: 8px 14px 12px;
  background: var(--surface-0);
}

.term-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; padding: 7px 0;
  border-bottom: 1px solid var(--border-subtle);
}
.term-row:last-child { border-bottom: none; }
.term-l { display: flex; align-items: center; gap: 8px; min-width: 0; }
.term-r { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

.tdot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--border-strong); flex-shrink: 0;
}
.tdot.active { background: var(--ok-dot); }

.term-name  { font-size: 13px; font-weight: 500; color: var(--tx-high); }
.term-dates { font-size: 11.5px; color: var(--tx-low); white-space: nowrap; }
.terms-empty { font-size: 12.5px; color: var(--tx-low); padding: 10px 0; margin: 0; }

.term-form {
  margin-top: 10px; padding-top: 10px;
  border-top: 1px dashed var(--border-subtle);
}

.add-term-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 0; margin-top: 8px;
  border: none; background: transparent;
  color: var(--accent); font-size: 12.5px; font-weight: 500;
  cursor: pointer; transition: opacity 0.1s;
}
.add-term-btn:hover { opacity: 0.75; }

/* ── Learning Areas ──────────────────────────────────────────────── */
.la-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 10px; padding: 10px 18px;
}
.border-t { border-top: 1px solid var(--border-subtle); }
.la-main { display: flex; align-items: center; gap: 12px; min-width: 0; flex: 1; }
.la-name { font-size: 13.5px; font-weight: 500; color: var(--tx-high); }
.la-code { font-size: 12px; color: var(--tx-low); background: var(--surface-2); padding: 2px 7px; border-radius: 4px; }
.la-actions { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }

/* ── Classes ─────────────────────────────────────────────────────── */
.class-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 14px;
}

/* Filter bar */
.cl-filters {
  display: flex; align-items: center; gap: 8px;
  flex-wrap: wrap; margin-bottom: 12px;
}
.cl-search-wrap {
  position: relative; display: flex; align-items: center;
  flex: 1; min-width: 160px; max-width: 260px;
}
.cl-search {
  width: 100%; height: 34px; padding: 0 30px 0 32px;
  border: 1px solid var(--border-strong); border-radius: 6px;
  background: var(--surface-0); color: var(--tx-high);
  font-size: 13px; font-family: inherit; outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.cl-search::placeholder { color: var(--tx-placeholder); }
.cl-search:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 13%, transparent);
}
.cl-clear-search {
  position: absolute; right: 8px;
  width: 18px; height: 18px; border-radius: 4px;
  border: none; background: transparent;
  color: var(--tx-low); display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
.cl-clear-search:hover { color: var(--tx-high); }
.cl-select {
  height: 34px; padding: 0 28px 0 11px;
  border: 1px solid var(--border-strong); border-radius: 6px;
  background: var(--surface-0); color: var(--tx-high);
  font-size: 13px; font-family: inherit; outline: none; cursor: pointer;
  appearance: none; -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2396938B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 8px center;
  transition: border-color 0.15s;
}
.cl-select:focus { border-color: var(--accent); }
.cl-clear-btn {
  height: 34px; padding: 0 12px; border-radius: 6px;
  border: 1px solid var(--border-subtle); background: transparent;
  color: var(--tx-low); font-size: 12.5px; cursor: pointer;
  transition: background 0.1s, color 0.1s; white-space: nowrap;
}
.cl-clear-btn:hover { background: var(--surface-2); color: var(--tx-high); }
.cl-count {
  margin-left: auto; font-size: 12px; color: var(--tx-low); white-space: nowrap;
}

/* Empty filtered state */
.cl-empty {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 48px 0; color: var(--tx-low); text-align: center;
}
.cl-empty p { margin: 0; font-size: 13.5px; }

/* List */
.cl-list {
  border: 1px solid var(--border-subtle);
  border-radius: 10px; overflow: hidden;
}
.cl-list-head {
  display: grid;
  grid-template-columns: 1fr 90px 140px 80px 90px 40px;
  padding: 0 14px;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border-subtle);
}
.cl-list-head > span {
  padding: 9px 0;
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--tx-low);
}
.cl-row {
  display: grid;
  grid-template-columns: 1fr 90px 140px 80px 90px 40px;
  padding: 0 14px;
  align-items: center;
  border-bottom: 1px solid var(--border-subtle);
  text-decoration: none; color: inherit;
  transition: background 0.1s;
  min-height: 46px;
}
.cl-row:last-child { border-bottom: none; }
.cl-row:hover { background: var(--accent-subtle); }
.cl-row-inactive { opacity: 0.6; }
.cl-name {
  font-size: 13.5px; font-weight: 500; color: var(--tx-high);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  padding-right: 8px;
}
.cl-row:hover .cl-name { color: var(--accent); }
.cl-level { display: flex; align-items: center; }
.cl-level-badge {
  font-size: 11px; font-weight: 600; padding: 2px 7px;
  border-radius: 4px; white-space: nowrap;
}
.cl-level-early_childhood { background: color-mix(in srgb, #f59e0b 15%, transparent); color: #b45309; }
.cl-level-basic           { background: color-mix(in srgb, #3b82f6 15%, transparent); color: #1d4ed8; }
.cl-level-shs             { background: color-mix(in srgb, #8b5cf6 15%, transparent); color: #6d28d9; }
.cl-area, .cl-stream {
  font-size: 12.5px; color: var(--tx-low);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  padding-right: 8px;
}
.cl-status { display: flex; align-items: center; gap: 6px; }
.status-dot {
  width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
}
.status-dot.active   { background: var(--ok-dot); }
.status-dot.inactive { background: var(--border-strong); }
.status-label { font-size: 12px; color: var(--tx-low); }
.cl-action { display: flex; align-items: center; justify-content: flex-end; }
.cl-del-btn {
  width: 28px; height: 28px; border-radius: 6px;
  border: none; background: transparent;
  color: var(--tx-low); display: flex; align-items: center; justify-content: center;
  cursor: pointer; opacity: 0; transition: opacity 0.1s, background 0.1s, color 0.1s;
}
.cl-row:hover .cl-del-btn { opacity: 1; }
.cl-del-btn:hover { background: var(--err-bg); color: var(--err-text); }

@media (max-width: 640px) {
  .cl-list-head { grid-template-columns: 1fr 80px 80px 36px; }
  .cl-list-head .clh-area,
  .cl-list-head .clh-stream { display: none; }
  .cl-row { grid-template-columns: 1fr 80px 80px 36px; }
  .cl-area, .cl-stream { display: none; }
  .cl-search-wrap { max-width: 100%; }
}
</style>
