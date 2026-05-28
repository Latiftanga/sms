<script lang="ts">
  import { onMount } from "svelte";
  import { api } from "$api/client";
  import { toast } from "$stores/toast";
  import { confirmDialog } from "$stores/confirm";
  import { schoolBranding } from "$stores/school";
  import Button    from "$components/ui/Button.svelte";
  import Badge     from "$components/ui/Badge.svelte";
  import Spinner   from "$components/ui/Spinner.svelte";
  import EmptyState from "$components/ui/EmptyState.svelte";
  import PageHeader from "$components/ui/PageHeader.svelte";
  import {
    School2, CalendarDays, LayoutGrid, BookOpen, Shield,
    Plus, Pencil, Trash2, Check, X, ChevronDown,
    AlertCircle, Loader2, MapPin, Phone, Palette, ImagePlus,
  } from "@lucide/svelte";

  // ── Types ─────────────────────────────────────────────────────────
  interface SchoolProfile {
    name: string; phone: string | null; email: string | null;
    address: string | null; region: string | null; district: string | null;
    motto: string | null; accent_color: string; logo_url: string | null;
    education_levels: string[];
  }
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
  let tab: "school" | "calendar" | "classes" | "learning_areas" | "positions" = "school";

  // ── Confirm delete ────────────────────────────────────────────────
  async function confirmDelete(title: string, message: string, fn: () => Promise<void>) {
    const ok = await confirmDialog.show({ title, message, variant: "danger", confirmLabel: "Delete" });
    if (!ok) return;
    try { await fn(); }
    catch (e) { toast.error(apiError(e)); }
  }

  function apiError(e: unknown): string {
    const err = e as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail ?? "Something went wrong. Try again.";
  }

  const LEVEL_LABELS: Record<string, string> = {
    EARLY_CHILDHOOD: "Early Childhood", BASIC: "Basic",
    SHS: "Senior High School", TECHNICAL: "Technical", JHS: "Junior High School",
  };

  // ── School profile ────────────────────────────────────────────────
  let school: SchoolProfile | null = null;
  let schoolLoading = true;
  let schoolLoadError = "";
  let schoolSaving = false;
  let schoolSuccess = false;
  let schoolError = "";

  $: isSHS = school?.education_levels?.includes("SHS") ?? false;
  $: if (!isSHS && tab === "learning_areas") tab = "school";

  async function loadSchool() {
    schoolLoading = true; schoolLoadError = "";
    try { const { data } = await api.get("/settings/school"); school = { ...data }; }
    catch (e) { school = null; schoolLoadError = apiError(e); }
    finally { schoolLoading = false; }
  }

  async function saveSchool() {
    schoolSaving = true; schoolError = ""; schoolSuccess = false;
    try {
      await api.patch("/settings/school", {
        name: school!.name, phone: school!.phone, email: school!.email,
        address: school!.address, region: school!.region, district: school!.district,
        motto: school!.motto || null, accent_color: school!.accent_color,
      });
      schoolSuccess = true;
      toast.success("School profile saved");
      setTimeout(() => schoolSuccess = false, 3000);
    } catch (e) { schoolError = apiError(e); }
    finally { schoolSaving = false; }
  }

  // ── Logo upload ───────────────────────────────────────────────────
  let logoUploading = false;
  let logoError = "";

  async function handleLogoChange(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    logoUploading = true; logoError = "";
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data } = await api.post("/settings/school/logo", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      school = { ...school!, logo_url: data.logo_url };
      // Refresh branding store so sidebar + login page pick up the new logo immediately
      await schoolBranding.load();
      toast.success("Logo uploaded");
    } catch (e) { logoError = apiError(e); toast.error(apiError(e)); }
    finally { logoUploading = false; input.value = ""; }
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

  // Only show levels the school actually offers
  $: availableLevels = LEVELS.filter(l =>
    school?.education_levels?.includes(LEVEL_EDU_MAP[l])
  );
  // If selected level is no longer in the available list, reset to first available
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

  $: classGroups = classes.reduce((acc: Record<string, SchoolClass[]>, c) => {
    (acc[c.education_level] ??= []).push(c);
    return acc;
  }, {});

  // ── Accent colour ─────────────────────────────────────────────────
  function applyAccent(hex: string) {
    document.documentElement.style.setProperty("--accent", hex);
    localStorage.setItem("sis-accent", hex);
  }
  $: if (school?.accent_color && /^#[0-9A-Fa-f]{3}$|^#[0-9A-Fa-f]{6}$/.test(school.accent_color)) {
    if (typeof window !== "undefined") applyAccent(school.accent_color);
  }

  // ── Ghana regions ─────────────────────────────────────────────────
  const GHANA_REGIONS = [
    "Ahafo", "Ashanti", "Bono", "Bono East", "Central",
    "Eastern", "Greater Accra", "North East", "Northern",
    "Oti", "Savannah", "Upper East", "Upper West",
    "Volta", "Western", "Western North",
  ];

  // ── Positions ─────────────────────────────────────────────────────
  interface Position {
    id: string; name: string; code: string;
    is_system_template: boolean; is_active: boolean; permissions: string[];
  }
  interface PermMeta { key: string; name: string; desc: string; }
  interface PermGroup { label: string; perms: PermMeta[]; }

  const PERM_GROUPS: PermGroup[] = [
    { label: "Students", perms: [
      { key: "view_students",             name: "View Students",       desc: "Browse student profiles and records" },
      { key: "enroll_students",           name: "Enroll Students",     desc: "Admit new students and manage enrollment" },
      { key: "transfer_students",         name: "Transfer Students",   desc: "Move students between classes or schools" },
    ]},
    { label: "Staff", perms: [
      { key: "view_staff",                name: "View Staff",          desc: "Browse staff profiles and employment details" },
      { key: "manage_staff",              name: "Manage Staff",        desc: "Create, edit and deactivate staff records" },
      { key: "manage_promotions",         name: "Rank History",        desc: "Record and edit GES rank promotions" },
    ]},
    { label: "Academics", perms: [
      { key: "view_scores",               name: "View Scores",         desc: "View assessment marks and report cards" },
      { key: "enter_scores",              name: "Enter Scores",        desc: "Submit marks for assessments" },
      { key: "approve_scores",            name: "Approve Scores",      desc: "Validate and lock submitted marks" },
      { key: "manage_timetable",          name: "Timetable",           desc: "Create and modify the class timetable" },
    ]},
    { label: "Attendance", perms: [
      { key: "mark_attendance",           name: "Mark Attendance",     desc: "Record daily and period attendance" },
      { key: "view_attendance",           name: "View Attendance",     desc: "View attendance records and reports" },
    ]},
    { label: "Reports", perms: [
      { key: "generate_reports",          name: "Generate Reports",    desc: "Print report cards and official documents" },
      { key: "revoke_documents",          name: "Revoke Documents",    desc: "Cancel already-issued report cards" },
    ]},
    { label: "Fees", perms: [
      { key: "view_fees",                 name: "View Fees",           desc: "See fee balances and payment records" },
      { key: "record_payments",           name: "Record Payments",     desc: "Post student fee payments" },
      { key: "manage_fee_structure",      name: "Fee Structure",       desc: "Set and modify fee schedules" },
      { key: "waive_fees",                name: "Waive Fees",          desc: "Grant fee exemptions or reductions" },
    ]},
    { label: "Communication", perms: [
      { key: "send_sms",                  name: "Send SMS",            desc: "Send text messages to parents and students" },
      { key: "send_announcements",        name: "Announcements",       desc: "Broadcast notices to the school" },
    ]},
    { label: "Boarding", perms: [
      { key: "manage_houses",             name: "Manage Houses",       desc: "Administer boarding houses and house lists" },
      { key: "manage_exeats",             name: "Exeats",              desc: "Issue and track student exit permissions" },
      { key: "night_roll_call",           name: "Night Roll Call",     desc: "Conduct evening boarding attendance" },
    ]},
    { label: "Administration", perms: [
      { key: "manage_school_config",      name: "School Config",       desc: "Edit school profile and branding" },
      { key: "manage_academic_structure", name: "Academic Structure",  desc: "Manage years, terms and classes" },
      { key: "manage_users",              name: "User Accounts",       desc: "Create accounts and assign roles to staff" },
      { key: "view_analytics",            name: "Analytics",           desc: "Access school-wide dashboards and insights" },
    ]},
  ];

  const ALL_PERMISSIONS = PERM_GROUPS.flatMap(g => g.perms.map(p => p.key));
  const PERM_LABELS: Record<string, string> = Object.fromEntries(
    PERM_GROUPS.flatMap(g => g.perms.map(p => [p.key, p.name]))
  );

  let positions: Position[] = [];
  let posLoading = false;
  let posError = "";
  let addingPos = false;
  let savingPos = false;
  let posApiError = "";
  let newPos = { name: "", code: "" };
  let newPosPerms: string[] = [];
  let editingPos: string | null = null;
  let editPosName = "";
  let expandedPos: string | null = null;
  let editingPosPerms: string | null = null;
  let editPosPermsSet = new Set<string>();
  let savingPosPerms = false;
  let posPermsError = "";

  async function loadPositions() {
    posLoading = true; posError = "";
    try {
      const { data } = await api.get<Position[]>("/settings/positions");
      positions = data;
    } catch (e) {
      posError = apiError(e);
    } finally {
      posLoading = false;
    }
  }

  async function savePosition() {
    if (!newPos.name.trim() || !newPos.code.trim()) {
      posApiError = "Name and code are required."; return;
    }
    savingPos = true; posApiError = "";
    try {
      await api.post("/settings/positions", {
        name: newPos.name.trim(),
        code: newPos.code.trim().toUpperCase(),
        permissions: newPosPerms,
      });
      newPos = { name: "", code: "" }; newPosPerms = []; addingPos = false;
      await loadPositions();
      toast.success("Position created");
    } catch (e) {
      posApiError = apiError(e);
    } finally {
      savingPos = false;
    }
  }

  async function updatePositionName(id: string) {
    if (!editPosName.trim()) return;
    try {
      await api.patch(`/settings/positions/${id}`, { name: editPosName.trim() });
      positions = positions.map(p => p.id === id ? { ...p, name: editPosName.trim() } : p);
      editingPos = null;
      toast.success("Name updated");
    } catch (e) { toast.error(apiError(e)); }
  }

  function startEditPosPerms(pos: Position) {
    editingPosPerms = pos.id;
    editPosPermsSet = new Set(pos.permissions);
    posPermsError = "";
  }

  function toggleEditPerm(key: string) {
    if (editPosPermsSet.has(key)) { editPosPermsSet.delete(key); }
    else { editPosPermsSet.add(key); }
    editPosPermsSet = editPosPermsSet;
  }

  async function savePosPerms(id: string) {
    savingPosPerms = true; posPermsError = "";
    try {
      const perms = [...editPosPermsSet];
      await api.patch(`/settings/positions/${id}`, { permissions: perms });
      positions = positions.map(p => p.id === id ? { ...p, permissions: perms } : p);
      editingPosPerms = null;
      toast.success("Permissions updated");
    } catch (e) {
      posPermsError = apiError(e);
    } finally {
      savingPosPerms = false;
    }
  }

  async function deletePosition(id: string) {
    try {
      await api.delete(`/settings/positions/${id}`);
      positions = positions.filter(p => p.id !== id);
      toast.success("Position deleted");
    } catch (e) { toast.error(apiError(e)); }
  }

  function togglePosPermission(perm: string) {
    if (newPosPerms.includes(perm)) { newPosPerms = newPosPerms.filter(p => p !== perm); }
    else { newPosPerms = [...newPosPerms, perm]; }
  }

  $: if (tab === "positions" && positions.length === 0 && !posLoading && !posError) {
    loadPositions();
  }

  // ── Init ──────────────────────────────────────────────────────────
  onMount(async () => {
    await loadSchool();
    await loadYears();
    await loadClasses();
    await loadLearningAreas();
  });
</script>

<svelte:head><title>Settings — TTEK-SIS</title></svelte:head>

<div class="settings-root">

  <!-- ── Tab bar ───────────────────────────────────────────────────── -->
  <div class="tabs-bar">
    <button class="tab" class:active={tab === "school"} on:click={() => tab = "school"}>
      <School2 size={14} /><span class="tab-label">School Profile</span>
    </button>
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
    <button class="tab" class:active={tab === "positions"} on:click={() => tab = "positions"}>
      <Shield size={14} /><span class="tab-label">Positions</span>
    </button>
  </div>

  <!-- ── Content ───────────────────────────────────────────────────── -->
  <div class="content">

    <!-- ══ SCHOOL PROFILE ════════════════════════════════════════════ -->
    {#if tab === "school"}
      {#if schoolLoading}
        <EmptyState message="Loading school data…">
          <svelte:fragment slot="icon"><Spinner size={28} /></svelte:fragment>
        </EmptyState>
      {:else if schoolLoadError}
        <EmptyState message={schoolLoadError} bordered>
          <svelte:fragment slot="icon"><AlertCircle size={28} /></svelte:fragment>
          <Button on:click={loadSchool}>Retry</Button>
        </EmptyState>
      {:else if school}
        <form on:submit|preventDefault={saveSchool} novalidate>
          <div class="two-col">

            <!-- Left: Identity + Branding -->
            <div class="col">

              <div class="card">
                <div class="card-header">
                  <div class="card-hicon"><School2 size={14} /></div>
                  <div>
                    <h2 class="card-title">School Identity</h2>
                    <p class="card-desc">Name and logo shown on reports and the app header.</p>
                  </div>
                </div>
                <div class="card-body form-stack">
                  <!-- Logo upload -->
                  <div class="logo-block">
                    <label class="logo-thumb" class:uploading={logoUploading} for="s-logo-file" title="Click to change logo">
                      {#if logoUploading}
                        <Loader2 size={20} class="spin" />
                      {:else if school.logo_url}
                        <img src={school.logo_url} alt="School logo" />
                        <div class="logo-overlay"><ImagePlus size={14} /></div>
                      {:else}
                        <ImagePlus size={20} style="opacity:.4" />
                        <span class="logo-hint-text">Upload logo</span>
                      {/if}
                    </label>
                    <input
                      id="s-logo-file"
                      type="file"
                      accept="image/jpeg,image/png,image/webp,image/svg+xml"
                      style="display:none"
                      on:change={handleLogoChange}
                    />
                    <div class="field" style="flex:1;min-width:0;">
                      <p class="logo-upload-label">School Logo</p>
                      <p class="hint">Click the thumbnail to upload. JPEG, PNG, WebP or SVG · max 2 MB.</p>
                      {#if logoError}<p class="field-error">{logoError}</p>{/if}
                    </div>
                  </div>

                  <div class="field">
                    <label for="s-name">School Name</label>
                    <input id="s-name" class="input" bind:value={school.name} placeholder="e.g. Accra Academy" />
                  </div>
                  <div class="field">
                    <label for="s-motto">School Motto <span class="opt-label">optional</span></label>
                    <input id="s-motto" class="input" bind:value={school.motto}
                      placeholder="e.g. Excellence in all things" maxlength="300" />
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-hicon"><Palette size={14} /></div>
                  <div>
                    <h2 class="card-title">Branding</h2>
                    <p class="card-desc">Accent colour applied across the whole interface. Changes preview live.</p>
                  </div>
                </div>
                <div class="card-body">
                  <div class="field">
                    <label for="s-accent">Accent Colour</label>
                    <div class="color-row">
                      <input type="color" id="s-accent" class="color-swatch" bind:value={school.accent_color} />
                      <input class="input mono" style="max-width:130px;"
                        bind:value={school.accent_color} placeholder="#185FA5" />
                      <div class="color-sample" style="background:{school.accent_color};">Button preview</div>
                    </div>
                  </div>
                </div>
              </div>

            </div><!-- /col left -->

            <!-- Right: Contact + Location -->
            <div class="col">

              <div class="card">
                <div class="card-header">
                  <div class="card-hicon"><Phone size={14} /></div>
                  <div>
                    <h2 class="card-title">Contact Information</h2>
                    <p class="card-desc">How parents and external parties reach your school.</p>
                  </div>
                </div>
                <div class="card-body form-stack">
                  <div class="field">
                    <label for="s-phone">Phone Number</label>
                    <input id="s-phone" class="input" bind:value={school.phone} placeholder="+233 XX XXX XXXX" />
                  </div>
                  <div class="field">
                    <label for="s-email">Email Address</label>
                    <input id="s-email" type="email" class="input" bind:value={school.email} placeholder="school@example.edu.gh" />
                  </div>
                </div>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-hicon"><MapPin size={14} /></div>
                  <div>
                    <h2 class="card-title">Location</h2>
                    <p class="card-desc">Used on official documents and correspondence.</p>
                  </div>
                </div>
                <div class="card-body form-stack">
                  <div class="field">
                    <label for="s-address">Street Address</label>
                    <input id="s-address" class="input" bind:value={school.address} placeholder="P.O. Box or street address" />
                  </div>
                  <div class="field">
                    <label for="s-region">Region</label>
                    <select id="s-region" class="input" bind:value={school.region}>
                      <option value="">— select region —</option>
                      {#each GHANA_REGIONS as r}<option value={r}>{r}</option>{/each}
                    </select>
                  </div>
                  <div class="field">
                    <label for="s-district">District</label>
                    <input id="s-district" class="input" bind:value={school.district} placeholder="e.g. Accra Metropolitan" />
                  </div>
                </div>
              </div>

            </div><!-- /col right -->
          </div><!-- /two-col -->

          <div class="save-bar">
            {#if schoolError}
              <span class="feedback err"><AlertCircle size={13} />{schoolError}</span>
            {/if}
            {#if schoolSuccess}
              <span class="feedback ok"><Check size={13} />Saved successfully</span>
            {/if}
            <span style="flex:1"></span>
            <Button type="submit" loading={schoolSaving}>
              {schoolSaving ? "Saving…" : "Save changes"}
            </Button>
          </div>
        </form>
      {/if}


    <!-- ══ ACADEMIC CALENDAR ══════════════════════════════════════════ -->
    {:else if tab === "calendar"}
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
      {/if}

      {#each Object.entries(classGroups) as [level, group]}
        <div class="class-section">
          <div class="section-label">
            <span>{LEVEL_LABELS[level] ?? level}</span>
            <span class="pill">{group.length}</span>
          </div>
          <div class="class-grid">
            {#each group as cls}
              <div class="class-chip" class:inactive={!cls.is_active}>
                <span class="chip-name">{cls.name}</span>
                {#if !cls.is_active}<span class="warn-dot" title="Inactive"></span>{/if}
                <button class="chip-del" aria-label="Delete {cls.name}"
                  on:click={() => confirmDelete(
                    "Delete class?",
                    `"${cls.name}" will be permanently removed.`,
                    () => deleteClass(cls.id)
                  )}
                ><X size={11} /></button>
              </div>
            {/each}
          </div>
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
                    <Check size={13} />
                  </Button>
                  <Button variant="icon" ariaLabel="Cancel edit" on:click={() => { editingLA = null; laEditError = ""; }}>
                    <X size={13} />
                  </Button>
                {:else}
                  <Button variant="icon" ariaLabel="Edit code"
                    on:click={() => { editingLA = la.id; editLAShort = la.short_name ?? ""; laEditError = ""; }}>
                    <Pencil size={13} />
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
    {/if}

    <!-- ══ POSITIONS ═════════════════════════════════════════════════ -->
    {#if tab === "positions"}
      <PageHeader title="Staff Positions" description="Define roles and the default permissions they grant.">
        <Button on:click={() => { addingPos = !addingPos; posApiError = ""; newPos = { name: "", code: "" }; newPosPerms = []; }}>
          <Plus size={13} />{addingPos ? "Cancel" : "New Position"}
        </Button>
      </PageHeader>

      {#if addingPos}
        <div class="card" style="margin-bottom:14px;">
          <div class="card-body">
            <div class="form-grid" style="margin-bottom:16px;">
              <div class="field">
                <label for="pos-name">Position name <span class="req">*</span></label>
                <input id="pos-name" class="input" bind:value={newPos.name} placeholder="e.g. Housemaster" />
              </div>
              <div class="field">
                <label for="pos-code">Code <span class="req">*</span></label>
                <input id="pos-code" class="input" bind:value={newPos.code} placeholder="e.g. HOUSEMASTER" style="text-transform:uppercase;" />
                <p class="hint">Unique key. Uppercase + underscores.</p>
              </div>
            </div>

            <p class="perm-section-label">Default permissions</p>
            <div class="perm-create-grid">
              {#each PERM_GROUPS as group}
                <div class="perm-create-group">
                  <p class="perm-group-label">{group.label}</p>
                  {#each group.perms as perm}
                    <label class="perm-check">
                      <input type="checkbox"
                        checked={newPosPerms.includes(perm.key)}
                        on:change={() => togglePosPermission(perm.key)}
                      />
                      <span class="perm-check-name">{perm.name}</span>
                    </label>
                  {/each}
                </div>
              {/each}
            </div>

            {#if posApiError}<div class="api-err" style="margin-top:12px;"><AlertCircle size={13} />{posApiError}</div>{/if}
            <div class="actions">
              <Button on:click={savePosition} loading={savingPos}>
                {savingPos ? "Creating…" : "Create position"}
              </Button>
              <Button variant="ghost" on:click={() => { addingPos = false; posApiError = ""; }}>Cancel</Button>
            </div>
          </div>
        </div>
      {/if}

      {#if posLoading}
        <div class="pos-loading"><Spinner /></div>
      {:else if posError}
        <div class="api-err"><AlertCircle size={13} />{posError}</div>
      {:else if positions.length === 0 && !addingPos}
        <EmptyState message="No positions defined yet. Add one to get started.">
          <svelte:fragment slot="icon"><Shield size={28} /></svelte:fragment>
          <Button on:click={() => addingPos = true}><Plus size={13} />Add first position</Button>
        </EmptyState>
      {:else}
        <div class="pos-list">
          {#each positions as pos}
            {@const isExpanded = expandedPos === pos.id}
            {@const isEditingPerms = editingPosPerms === pos.id}
            {@const grantedCount = pos.permissions.length}
            <div class="pos-card" class:is-expanded={isExpanded}>

              <!-- Card header row -->
              <div class="pos-card-head">
                <!-- Expand toggle (left + chevron) -->
                <button class="pos-toggle" type="button" on:click={() => {
                  expandedPos = isExpanded ? null : pos.id;
                  if (!isExpanded) { editingPosPerms = null; editingPos = null; }
                }}>
                  <ChevronDown size={14} class="pos-chevron {isExpanded ? 'open' : ''}" />
                  {#if pos.is_system_template}<span class="sys-badge">system</span>{/if}

                  {#if editingPos !== pos.id}
                    <span class="pos-name">{pos.name}</span>
                  {/if}
                  <span class="pos-code">{pos.code}</span>
                  <span class="pos-perm-count">
                    {#if grantedCount === 0}No permissions{:else}{grantedCount} permission{grantedCount !== 1 ? "s" : ""}{/if}
                  </span>
                </button>

                <!-- Name edit input (outside toggle button) -->
                {#if editingPos === pos.id}
                  <input class="input pos-name-input" bind:value={editPosName}
                    on:keydown={e => e.key === "Enter" && updatePositionName(pos.id)} />
                {/if}

                <!-- Action buttons (siblings, not inside toggle) -->
                {#if !pos.is_system_template}
                  {#if editingPos === pos.id}
                    <button class="icon-act" title="Save name" on:click={() => updatePositionName(pos.id)}>
                      <Check size={13} />
                    </button>
                    <button class="icon-act" title="Cancel" on:click={() => editingPos = null}>
                      <X size={13} />
                    </button>
                  {:else}
                    <button class="icon-act" title="Rename" on:click={() => {
                      editingPos = pos.id; editPosName = pos.name; expandedPos = pos.id;
                    }}><Pencil size={13} /></button>
                    <button class="icon-act danger" title="Delete" on:click={() => confirmDelete(
                      "Delete position?",
                      `"${pos.name}" will be removed. Staff assigned to it will lose these default permissions.`,
                      () => deletePosition(pos.id)
                    )}><Trash2 size={13} /></button>
                  {/if}
                {/if}
              </div>

              <!-- Expanded permissions panel -->
              {#if isExpanded}
                <div class="perm-panel">
                  {#if isEditingPerms}
                    <!-- Edit mode: grouped checkboxes -->
                    <div class="perm-edit-grid">
                      {#each PERM_GROUPS as group}
                        <div class="perm-edit-group">
                          <p class="perm-group-label">{group.label}</p>
                          {#each group.perms as perm}
                            <label class="perm-check perm-check-sm">
                              <input type="checkbox"
                                checked={editPosPermsSet.has(perm.key)}
                                on:change={() => toggleEditPerm(perm.key)}
                              />
                              <span class="perm-check-name">{perm.name}</span>
                            </label>
                          {/each}
                        </div>
                      {/each}
                    </div>
                    {#if posPermsError}<div class="api-err" style="margin-top:10px;"><AlertCircle size={13} />{posPermsError}</div>{/if}
                    <div class="perm-edit-actions">
                      <Button size="sm" loading={savingPosPerms} on:click={() => savePosPerms(pos.id)}>Save permissions</Button>
                      <Button size="sm" variant="ghost" on:click={() => { editingPosPerms = null; posPermsError = ""; }}>Cancel</Button>
                    </div>

                  {:else}
                    <!-- View mode: grouped permission rows -->
                    <div class="perm-view-grid">
                      {#each PERM_GROUPS as group}
                        {@const groupGranted = group.perms.filter(p => pos.permissions.includes(p.key))}
                        {#if !pos.is_system_template || groupGranted.length > 0}
                          <div class="perm-view-group">
                            <p class="perm-group-label">{group.label}</p>
                            {#each group.perms as perm}
                              {@const granted = pos.permissions.includes(perm.key)}
                              <div class="perm-view-row" class:granted class:denied={!granted}>
                                {#if granted}
                                  <Check size={12} class="pv-check" />
                                {:else}
                                  <span class="pv-dash">—</span>
                                {/if}
                                <span class="perm-view-name">{perm.name}</span>
                              </div>
                            {/each}
                          </div>
                        {/if}
                      {/each}
                    </div>
                    {#if !pos.is_system_template}
                      <div class="perm-edit-actions">
                        <Button size="sm" variant="ghost" on:click={() => startEditPosPerms(pos)}>
                          <Pencil size={12} /> Edit permissions
                        </Button>
                      </div>
                    {/if}
                  {/if}
                </div>
              {/if}

            </div>
          {/each}
        </div>
      {/if}
    {/if}

  </div><!-- /content -->
</div><!-- /settings-root -->

<style>
/* ── Root ─────────────────────────────────────────────────────────── */
.settings-root { display: flex; flex-direction: column; min-height: 100%; }

/* ── Tab bar ─────────────────────────────────────────────────────── */
.tabs-bar {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 24px;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
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

/* ── Two-column (School Profile) ─────────────────────────────────── */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }
.col { display: flex; flex-direction: column; gap: 16px; }
@media (max-width: 860px) { .two-col { grid-template-columns: 1fr; } }

/* ── Cards ───────────────────────────────────────────────────────── */
.card {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  box-shadow: var(--shadow-xs);
  margin-bottom: 14px;
  overflow: hidden;
  transition: box-shadow 0.15s;
}
.card:focus-within { box-shadow: 0 0 0 1px var(--accent-border), var(--shadow-sm); }
.col .card { margin-bottom: 0; }

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 13px 18px;
  background: var(--surface-0);
  border-bottom: 1px solid var(--border-subtle);
}
.card-hicon {
  width: 28px; height: 28px;
  border-radius: 7px;
  background: var(--accent-subtle);
  color: var(--accent);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 1px;
}
.card-title { font-size: 13px; font-weight: 600; color: var(--tx-high); margin: 0 0 2px; }
.card-desc  { font-size: 12px; color: var(--tx-low); margin: 0; line-height: 1.5; }
.card-body { padding: 16px 18px; }

/* ── Form helpers ─────────────────────────────────────────────────── */
.form-stack { display: flex; flex-direction: column; gap: 14px; }
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}
.field { display: flex; flex-direction: column; gap: 5px; }

label {
  font-size: 12px;
  font-weight: 600;
  color: var(--tx-mid);
  letter-spacing: 0.01em;
  user-select: none;
}
.req { color: var(--accent); margin-left: 2px; }
.opt { font-weight: 400; font-size: 11px; color: var(--tx-low); }

.input {
  width: 100%;
  height: 34px;
  padding: 0 11px;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  background: var(--surface-0);
  color: var(--tx-high);
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
  appearance: none;
  -webkit-appearance: none;
}
.input::placeholder { color: var(--tx-placeholder); }
.input:hover:not(:focus):not(:disabled) {
  border-color: color-mix(in srgb, var(--border-strong) 40%, var(--accent));
  background: var(--surface-1);
}
.input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 13%, transparent);
}
.input.invalid { border-color: var(--err-text); }
.input:disabled { opacity: 0.55; cursor: not-allowed; }

select.input {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2396938B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 28px;
  cursor: pointer;
}

.ferr { font-size: 11.5px; color: var(--err-text); margin: 0; }
.hint { font-size: 11.5px; color: var(--tx-low); margin: 0; line-height: 1.4; }

/* ── Actions row ─────────────────────────────────────────────────── */
.actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}

/* ── API-level inline error ──────────────────────────────────────── */
.api-err {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 12px;
  border-radius: 6px;
  background: var(--err-bg);
  color: var(--err-text);
  font-size: 12.5px;
  margin-top: 10px;
  border: 1px solid color-mix(in srgb, var(--err-text) 18%, transparent);
}

/* ── Save bar ────────────────────────────────────────────────────── */
.save-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 0 4px;
  flex-wrap: wrap;
}
.feedback {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  font-weight: 500;
}
.feedback.ok  { color: var(--ok-text); }
.feedback.err { color: var(--err-text); }

/* ── Logo block ──────────────────────────────────────────────────── */
.logo-block {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}
.logo-thumb {
  width: 64px; height: 64px;
  border: 1.5px dashed var(--border-strong);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  overflow: hidden;
  flex-shrink: 0;
  color: var(--tx-low);
  cursor: pointer;
  position: relative;
  transition: border-color 0.15s, background 0.15s;
}
.logo-thumb:hover {
  border-color: var(--accent);
  background: var(--accent-subtle);
}
.logo-thumb.uploading { opacity: .6; pointer-events: none; }
.logo-thumb img { width: 100%; height: 100%; object-fit: contain; }
.logo-overlay {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  opacity: 0;
  transition: opacity 0.15s;
}
.logo-thumb:hover .logo-overlay { opacity: 1; }
.logo-hint-text { font-size: 9px; color: var(--tx-low); text-align: center; line-height: 1.2; }
.logo-upload-label { font-size: 12px; font-weight: 500; color: var(--tx-high); margin-bottom: 3px; }
.opt-label { font-size: 10px; font-weight: 400; color: var(--tx-low); margin-left: 4px; }
.field-error { font-size: 11px; color: #ef4444; margin-top: 3px; }

/* ── Colour picker ───────────────────────────────────────────────── */
.color-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.color-swatch {
  width: 34px; height: 34px;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  padding: 2px;
  cursor: pointer;
  background: none;
  flex-shrink: 0;
}
.color-sample {
  height: 34px;
  padding: 0 14px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  font-size: 12px;
  font-weight: 500;
  color: #fff;
  flex-shrink: 0;
}
.mono { font-family: "Menlo", "Consolas", monospace; }

/* ── Page header (used by non-form tabs) ─────────────────────────── */
:global(.page-head) { margin-bottom: 20px; }

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
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
}
.year-head-l { display: flex; align-items: center; gap: 10px; }
.year-head-r { display: flex; align-items: center; gap: 8px; }

.year-name  { font-size: 13.5px; font-weight: 600; color: var(--tx-high); }
.year-dates { font-size: 11.5px; color: var(--tx-low); margin-top: 1px; }

.expand-btn {
  width: 26px; height: 26px;
  border-radius: 6px;
  border: none;
  background: transparent;
  display: flex; align-items: center; justify-content: center;
  color: var(--tx-low);
  cursor: pointer;
  transition: background 0.1s;
  flex-shrink: 0;
}
.expand-btn:hover { background: var(--surface-2); }
:global(.chevron) { transition: transform 0.18s ease; }
:global(.chevron.open) { transform: rotate(180deg); }

.pill {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 7px;
  border-radius: 5px;
  background: var(--surface-2);
  color: var(--tx-low);
  border: 1px solid var(--border-subtle);
}

.terms-panel {
  border-top: 1px solid var(--border-subtle);
  padding: 8px 14px 12px;
  background: var(--surface-0);
}

.term-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 0;
  border-bottom: 1px solid var(--border-subtle);
}
.term-row:last-child { border-bottom: none; }

.term-l { display: flex; align-items: center; gap: 8px; min-width: 0; }
.term-r { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

.tdot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--border-strong);
  flex-shrink: 0;
  transition: background 0.12s;
}
.tdot.active { background: var(--ok-dot); }

.term-name  { font-size: 13px; font-weight: 500; color: var(--tx-high); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.term-dates { font-size: 11.5px; color: var(--tx-low); white-space: nowrap; }

.terms-empty { font-size: 12.5px; color: var(--tx-low); padding: 10px 0; margin: 0; }

.term-form {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--border-subtle);
}

.add-term-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 0;
  margin-top: 8px;
  border: none;
  background: transparent;
  color: var(--accent);
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.1s;
}
.add-term-btn:hover { opacity: 0.75; }

/* ── Classes ─────────────────────────────────────────────────────── */
.class-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 14px;
}

.class-section { margin-bottom: 18px; }

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--tx-low);
  margin-bottom: 8px;
}

.class-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.class-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 8px 5px 11px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: var(--surface-1);
  font-size: 12.5px;
  font-weight: 500;
  color: var(--tx-high);
  transition: border-color 0.1s, box-shadow 0.1s;
}
.class-chip:hover { border-color: var(--border-strong); box-shadow: var(--shadow-xs); }
.class-chip.inactive { opacity: 0.55; }

.chip-name { white-space: nowrap; }

.chip-del {
  width: 18px; height: 18px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: var(--tx-low);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
  flex-shrink: 0;
}
.chip-del:hover { background: var(--err-bg); color: var(--err-text); }

.warn-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--warn-dot); }

/* ── Learning Areas ──────────────────────────────────────────────── */
.la-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 18px;
}
.border-t { border-top: 1px solid var(--border-subtle); }

.la-main { display: flex; align-items: center; gap: 12px; min-width: 0; flex: 1; }
.la-name { font-size: 13.5px; font-weight: 500; color: var(--tx-high); }
.la-code { font-size: 12px; color: var(--tx-low); background: var(--surface-2); padding: 2px 7px; border-radius: 4px; }
.la-actions { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }

/* ── Positions ────────────────────────────────────────────────────── */
.pos-loading { display: flex; justify-content: center; padding: 40px; }
.pos-list { display: flex; flex-direction: column; gap: 8px; }

.pos-card {
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: var(--surface-1);
  overflow: hidden;
  transition: border-color 0.12s;
}
.pos-card.is-expanded { border-color: color-mix(in srgb, var(--accent) 30%, var(--border-subtle)); }

.pos-card-head {
  display: flex; align-items: center; gap: 6px; padding: 4px 10px 4px 4px;
}

.pos-toggle {
  display: flex; align-items: center; gap: 8px;
  flex: 1; min-width: 0; padding: 8px 10px;
  background: none; border: none; cursor: pointer; text-align: left;
  border-radius: 7px; transition: background 0.1s;
}
.pos-toggle:hover { background: color-mix(in srgb, var(--surface-2) 60%, transparent); }

.pos-name { font-size: 13.5px; font-weight: 600; color: var(--tx-high); }
.pos-name-input { height: 30px; font-size: 13px; width: 180px; }
.pos-code {
  font-size: 10.5px; font-weight: 700; font-family: monospace;
  color: var(--tx-low); background: var(--surface-2);
  padding: 2px 7px; border-radius: 4px; letter-spacing: 0.04em;
  white-space: nowrap;
}
.pos-perm-count { font-size: 11.5px; color: var(--tx-low); white-space: nowrap; }

.sys-badge {
  display: inline-block; padding: 1px 8px; border-radius: 10px;
  font-size: 10px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  color: var(--accent); border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
  flex-shrink: 0;
}

.icon-act {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 6px;
  background: none; border: none; cursor: pointer;
  color: var(--tx-low); transition: background 0.1s, color 0.1s;
}
.icon-act:hover { background: var(--surface-2); color: var(--tx-mid); }
.icon-act.danger:hover { background: color-mix(in srgb, #ef4444 10%, transparent); color: #ef4444; }

:global(.pos-chevron) { color: var(--tx-low); transition: transform 0.18s ease; flex-shrink: 0; }
:global(.pos-chevron.open) { transform: rotate(180deg); }

/* Permissions panel */
.perm-panel {
  border-top: 1px solid var(--border-subtle);
  padding: 16px 18px;
  background: var(--surface-0);
}

/* View mode */
.perm-view-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px 24px;
}
.perm-view-group { display: flex; flex-direction: column; gap: 4px; }

.perm-view-row {
  display: flex; align-items: baseline; gap: 6px;
  font-size: 12.5px; padding: 2px 0;
}
.perm-view-row.denied { opacity: 0.45; }

:global(.pv-check) { color: #10b981; flex-shrink: 0; margin-top: 1px; }
.pv-dash { font-size: 11px; color: var(--border-strong); flex-shrink: 0; width: 12px; text-align: center; }

.perm-view-name { font-weight: 500; color: var(--tx-high); white-space: nowrap; }
.perm-view-row.denied .perm-view-name { color: var(--tx-low); }

/* Edit mode */
.perm-edit-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 16px 24px;
}
.perm-edit-group { display: flex; flex-direction: column; gap: 2px; }

.perm-edit-actions {
  display: flex; gap: 8px; margin-top: 16px; padding-top: 14px;
  border-top: 1px solid var(--border-subtle);
}

/* Create form perm grid */
.perm-section-label {
  font-size: 12px; font-weight: 600; color: var(--tx-mid);
  margin: 0 0 10px; text-transform: uppercase; letter-spacing: 0.04em;
}
.perm-create-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px 24px;
  margin-bottom: 4px;
}
.perm-create-group { display: flex; flex-direction: column; gap: 2px; }

.perm-group-label {
  font-size: 10.5px; font-weight: 700; color: var(--tx-low);
  text-transform: uppercase; letter-spacing: 0.07em;
  margin: 0 0 4px; padding: 0;
}

.perm-check {
  display: flex; align-items: flex-start; gap: 7px;
  padding: 5px 6px; border-radius: 6px;
  cursor: pointer; font-size: 12.5px; color: var(--tx-mid);
  transition: background 0.1s; user-select: none;
}
.perm-check:hover { background: color-mix(in srgb, var(--accent) 5%, transparent); }
.perm-check input[type="checkbox"] { accent-color: var(--accent); width: 13px; height: 13px; margin-top: 2px; flex-shrink: 0; }
.perm-check-sm { padding: 4px 6px; }

.perm-check-name { font-weight: 500; color: var(--tx-high); font-size: 12.5px; }

/* ── Spinner (global keyframe) ───────────────────────────────────── */
:global(.spin) { animation: spin 0.75s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
