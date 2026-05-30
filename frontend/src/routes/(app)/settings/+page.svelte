<script lang="ts">
  import { onMount } from "svelte";
  import { api } from "$api/client";
  import { auth } from "$stores/auth";
  import { toast } from "$stores/toast";
  import { confirmDialog } from "$stores/confirm";
  import { schoolBranding } from "$stores/school";
  import Button    from "$components/ui/Button.svelte";
  import Badge     from "$components/ui/Badge.svelte";
  import Spinner   from "$components/ui/Spinner.svelte";
  import EmptyState from "$components/ui/EmptyState.svelte";
  import PageHeader from "$components/ui/PageHeader.svelte";
  import {
    School2, Shield,
    Pencil, Trash2, Check, X, ChevronDown,
    AlertCircle, Loader2, MapPin, Phone, Palette, ImagePlus,
    Users, ScrollText, ToggleLeft, ToggleRight, KeyRound, Plus, Search,
  } from "@lucide/svelte";

  // ── Types ─────────────────────────────────────────────────────────
  interface SchoolProfile {
    name: string; phone: string | null; email: string | null;
    address: string | null; region: string | null; district: string | null;
    motto: string | null; accent_color: string; logo_url: string | null;
    education_levels: string[];
  }
  // ── Permissions ───────────────────────────────────────────────────
  $: isSuperAdmin   = $auth.user?.system_role === "SUPERADMIN";
  $: canSchool      = isSuperAdmin || $auth.user?.permissions?.manage_school_config === true;
  $: canUsers       = isSuperAdmin || $auth.user?.permissions?.manage_users === true;

  // ── Tab ───────────────────────────────────────────────────────────
  let tab: "school" | "positions" | "users" | "logs" = "school";
  $: if (!canSchool && canUsers && tab === "school") tab = "positions";

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

  // ── School profile ────────────────────────────────────────────────
  let school: SchoolProfile | null = null;
  let schoolLoading = true;
  let schoolLoadError = "";
  let schoolSaving = false;
  let schoolSuccess = false;
  let schoolError = "";

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

  // ── User accounts ─────────────────────────────────────────────────
  interface UserAccount {
    id: string;
    email: string;
    is_active: boolean;
    is_verified: boolean;
    must_change_password: boolean;
    last_login_at: string | null;
    staff_name: string | null;
    roles: string[];
  }

  let userAccounts: UserAccount[] = [];
  let usersLoading = false;
  let usersError = "";
  let userActionId: string | null = null;

  // ── Filters ───────────────────────────────────────────────────────
  let filterSearch = "";
  let filterStatus: "all" | "active" | "inactive" = "all";
  let filterRole = "";

  $: allRoles = [...new Set(userAccounts.flatMap(u => u.roles))].sort();

  $: filteredUsers = userAccounts.filter(u => {
    if (filterStatus === "active"   && !u.is_active) return false;
    if (filterStatus === "inactive" &&  u.is_active) return false;
    if (filterRole && !u.roles.includes(filterRole)) return false;
    if (filterSearch) {
      const q = filterSearch.toLowerCase();
      if (!(u.staff_name?.toLowerCase().includes(q) || u.email.toLowerCase().includes(q))) return false;
    }
    return true;
  });

  $: activeFilterCount =
    (filterStatus !== "all" ? 1 : 0) +
    (filterRole ? 1 : 0) +
    (filterSearch ? 1 : 0);

  function clearFilters() {
    filterSearch = "";
    filterStatus = "all";
    filterRole = "";
  }

  async function loadUsers() {
    usersLoading = true; usersError = "";
    try {
      const { data } = await api.get<UserAccount[]>("/settings/users");
      userAccounts = data;
    } catch (e) { usersError = apiError(e); }
    finally { usersLoading = false; }
  }

  async function toggleUserActive(u: UserAccount) {
    userActionId = u.id;
    try {
      const { data } = await api.patch<UserAccount>(`/settings/users/${u.id}`, { is_active: !u.is_active });
      userAccounts = userAccounts.map(a => a.id === u.id ? data : a);
      toast.success(data.is_active ? "Account activated" : "Account deactivated");
    } catch (e) { toast.error(apiError(e)); }
    finally { userActionId = null; }
  }

  async function forcePasswordReset(u: UserAccount) {
    userActionId = u.id + "_pw";
    try {
      const { data } = await api.patch<UserAccount>(`/settings/users/${u.id}`, { must_change_password: true });
      userAccounts = userAccounts.map(a => a.id === u.id ? data : a);
      toast.success("User will be prompted to change password on next login");
    } catch (e) { toast.error(apiError(e)); }
    finally { userActionId = null; }
  }

  function formatLastLogin(dt: string | null): string {
    if (!dt) return "Never";
    const d = new Date(dt);
    const now = new Date();
    const diff = Math.floor((now.getTime() - d.getTime()) / 1000);
    if (diff < 60) return "Just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 7 * 86400) return `${Math.floor(diff / 86400)}d ago`;
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
  }

  $: if (tab === "users" && userAccounts.length === 0 && !usersLoading && !usersError) {
    loadUsers();
  }

  // ── Init ──────────────────────────────────────────────────────────
  onMount(async () => {
    await loadSchool();
  });
</script>

<svelte:head><title>Settings — TTEK-SIS</title></svelte:head>

<div class="settings-root">

  <!-- ── Tab bar ───────────────────────────────────────────────────── -->
  <div class="tabs-bar">
    {#if canSchool}
      <button class="tab" class:active={tab === "school"} on:click={() => tab = "school"}>
        <School2 size={14} /><span class="tab-label">School Profile</span>
      </button>
    {/if}
    {#if canUsers}
      <button class="tab" class:active={tab === "positions"} on:click={() => tab = "positions"}>
        <Shield size={14} /><span class="tab-label">Roles</span>
      </button>
      <button class="tab" class:active={tab === "users"} on:click={() => tab = "users"}>
        <Users size={14} /><span class="tab-label">Users</span>
      </button>
    {/if}
    {#if canSchool || canUsers}
      <button class="tab" class:active={tab === "logs"} on:click={() => tab = "logs"}>
        <ScrollText size={14} /><span class="tab-label">Logs</span>
      </button>
    {/if}
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
    {/if}

    <!-- ══ POSITIONS ═════════════════════════════════════════════════ -->
    {#if tab === "positions"}
      <PageHeader title="Roles" description="Define staff roles and the default permissions they grant.">
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
        <div class="api-err" style="margin-bottom:14px;"><AlertCircle size={13} />{posError}</div>
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

    <!-- ══ USERS ═══════════════════════════════════════════════════════ -->
    {#if tab === "users"}
      <PageHeader title="User Accounts" description="All staff accounts in your school. Manage access and account status.">
        <Button on:click={loadUsers} variant="ghost">
          <Loader2 size={13} class={usersLoading ? "spin" : ""} />Refresh
        </Button>
      </PageHeader>

      {#if usersLoading}
        <div class="pos-loading"><Spinner /></div>
      {:else if usersError}
        <div class="api-err"><AlertCircle size={13} />{usersError}
          <Button variant="link" on:click={loadUsers} style="margin-left:8px;">Retry</Button>
        </div>
      {:else}
        <!-- Filter bar -->
        <div class="user-filters">
          <div class="uf-search">
            <Search size={13} class="uf-search-icon" />
            <input
              class="uf-input"
              placeholder="Search by name or email…"
              bind:value={filterSearch}
            />
            {#if filterSearch}
              <button class="uf-clear-btn" on:click={() => filterSearch = ""} aria-label="Clear search">
                <X size={12} />
              </button>
            {/if}
          </div>

          <div class="uf-selects">
            <select class="uf-select" bind:value={filterStatus}>
              <option value="all">All status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>

            <select class="uf-select" bind:value={filterRole}>
              <option value="">All roles</option>
              {#each allRoles as role}
                <option value={role}>{role}</option>
              {/each}
            </select>
          </div>

          {#if activeFilterCount > 0}
            <button class="uf-reset" on:click={clearFilters}>
              <X size={11} /> Clear {activeFilterCount} filter{activeFilterCount !== 1 ? "s" : ""}
            </button>
          {/if}
        </div>

        <!-- Results summary -->
        {#if userAccounts.length > 0}
          <p class="user-count">
            {filteredUsers.length} of {userAccounts.length} account{userAccounts.length !== 1 ? "s" : ""}
            {activeFilterCount > 0 ? "match filters" : "total"}
          </p>
        {/if}

        {#if filteredUsers.length === 0 && userAccounts.length === 0}
          <EmptyState message="No user accounts found.">
            <svelte:fragment slot="icon"><Users size={28} /></svelte:fragment>
          </EmptyState>
        {:else if filteredUsers.length === 0}
          <EmptyState message="No accounts match the current filters.">
            <svelte:fragment slot="icon"><Search size={28} /></svelte:fragment>
            <Button variant="ghost" on:click={clearFilters}><X size={13} />Clear filters</Button>
          </EmptyState>
        {:else}
        <div class="user-list">
          {#each filteredUsers as u (u.id)}
            <div class="user-row" class:inactive={!u.is_active}>
              <!-- Avatar + Identity -->
              <div class="user-id">
                <div class="user-avatar" class:av-inactive={!u.is_active}>
                  {(u.staff_name ?? u.email).charAt(0).toUpperCase()}
                </div>
                <div class="user-meta">
                  <span class="user-name">{u.staff_name ?? "—"}</span>
                  <span class="user-email">{u.email}</span>
                </div>
              </div>

              <!-- Role pills -->
              <div class="user-roles">
                {#if u.roles.length === 0}
                  <span class="no-role">No role</span>
                {:else}
                  {#each u.roles as role}
                    <span class="role-pill">{role}</span>
                  {/each}
                {/if}
              </div>

              <!-- Status + last login -->
              <div class="user-status-col">
                {#if u.is_active}
                  <Badge variant="ok" size="sm">Active</Badge>
                {:else}
                  <Badge variant="warn" size="sm">Inactive</Badge>
                {/if}
                {#if u.must_change_password}
                  <span class="pw-flag" title="Must change password on next login">
                    <KeyRound size={11} /> Pwd reset
                  </span>
                {/if}
              </div>

              <!-- Last login -->
              <div class="user-login">{formatLastLogin(u.last_login_at)}</div>

              <!-- Actions -->
              <div class="user-actions">
                <button class="icon-act" title={u.is_active ? "Deactivate account" : "Activate account"}
                  disabled={userActionId === u.id}
                  on:click={() => toggleUserActive(u)}>
                  {#if userActionId === u.id}
                    <Loader2 size={13} class="spin" />
                  {:else if u.is_active}
                    <ToggleRight size={15} style="color:var(--ok-text)" />
                  {:else}
                    <ToggleLeft size={15} style="color:var(--tx-low)" />
                  {/if}
                </button>
                <button class="icon-act" title="Force password change on next login"
                  disabled={userActionId === u.id + "_pw" || u.must_change_password}
                  on:click={() => forcePasswordReset(u)}>
                  {#if userActionId === u.id + "_pw"}
                    <Loader2 size={13} class="spin" />
                  {:else}
                    <KeyRound size={13} />
                  {/if}
                </button>
              </div>
            </div>
          {/each}
        </div>
        {/if}
      {/if}
    {/if}

    <!-- ══ LOGS ════════════════════════════════════════════════════════ -->
    {#if tab === "logs"}
      <PageHeader title="Activity Logs" description="Audit trail of administrative actions in your school." />
      <div class="logs-placeholder">
        <ScrollText size={32} style="opacity:.25;margin-bottom:12px;" />
        <p class="lp-title">Activity logs coming soon</p>
        <p class="lp-desc">This section will show a timestamped record of logins, account changes, and data edits.</p>
      </div>
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

/* ── User filters ────────────────────────────────────────────────── */
.user-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.uf-search {
  position: relative;
  flex: 1;
  min-width: 200px;
  max-width: 340px;
  display: flex;
  align-items: center;
}
:global(.uf-search-icon) {
  position: absolute;
  left: 10px;
  color: var(--tx-low);
  pointer-events: none;
}
.uf-input {
  width: 100%;
  height: 32px;
  padding: 0 30px 0 30px;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  background: var(--surface-0);
  color: var(--tx-high);
  font-size: 12.5px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.14s, box-shadow 0.14s;
}
.uf-input::placeholder { color: var(--tx-placeholder); }
.uf-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent);
}
.uf-clear-btn {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  color: var(--tx-low);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 2px;
  border-radius: 3px;
  transition: color 0.1s;
}
.uf-clear-btn:hover { color: var(--tx-mid); }

.uf-selects {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.uf-select {
  height: 32px;
  padding: 0 26px 0 10px;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  background: var(--surface-0);
  color: var(--tx-mid);
  font-size: 12.5px;
  font-family: inherit;
  outline: none;
  cursor: pointer;
  transition: border-color 0.14s;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2396938B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
}
.uf-select:focus { border-color: var(--accent); }

.uf-reset {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  background: var(--surface-1);
  color: var(--tx-low);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
  white-space: nowrap;
}
.uf-reset:hover { background: var(--surface-2); color: var(--tx-mid); }

.user-count {
  font-size: 11.5px;
  color: var(--tx-low);
  margin: 0 0 10px;
}

/* ── User list ───────────────────────────────────────────────────── */
.user-list { display: flex; flex-direction: column; gap: 1px; }

.user-row {
  display: grid;
  grid-template-columns: 1fr auto auto auto auto;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: var(--surface-1);
  margin-bottom: 6px;
  transition: background 0.1s;
}
.user-row:hover { background: var(--surface-0); }
.user-row.inactive { opacity: 0.65; }

.user-id { display: flex; align-items: center; gap: 10px; min-width: 0; }

.user-avatar {
  width: 32px; height: 32px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--accent) 15%, transparent);
  color: var(--accent);
  font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
}
.user-avatar.av-inactive {
  background: var(--surface-2);
  color: var(--tx-low);
  border-color: var(--border-subtle);
}

.user-meta { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.user-name  { font-size: 13px; font-weight: 600; color: var(--tx-high); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-email { font-size: 11.5px; color: var(--tx-low); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.user-roles { display: flex; flex-wrap: wrap; gap: 4px; justify-content: flex-end; }

.role-pill {
  font-size: 10.5px; font-weight: 600;
  padding: 2px 8px; border-radius: 10px;
  background: var(--surface-2);
  color: var(--tx-mid);
  border: 1px solid var(--border-subtle);
  white-space: nowrap;
}
.no-role { font-size: 11.5px; color: var(--tx-low); font-style: italic; }

.user-status-col { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }

.pw-flag {
  display: inline-flex; align-items: center; gap: 3px;
  font-size: 10px; font-weight: 600; color: var(--warn-dot);
  background: color-mix(in srgb, var(--warn-dot) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--warn-dot) 20%, transparent);
  padding: 1px 6px; border-radius: 8px;
}

.user-login { font-size: 11.5px; color: var(--tx-low); white-space: nowrap; text-align: right; }

.user-actions { display: flex; gap: 2px; flex-shrink: 0; }

@media (max-width: 700px) {
  .user-row { grid-template-columns: 1fr auto auto; }
  .user-roles { display: none; }
  .user-login { display: none; }
}

/* ── Logs placeholder ────────────────────────────────────────────── */
.logs-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  border: 1px dashed var(--border-strong);
  border-radius: 12px;
  background: var(--surface-1);
  text-align: center;
  color: var(--tx-low);
}
.lp-title { font-size: 14px; font-weight: 600; color: var(--tx-mid); margin: 0 0 6px; }
.lp-desc  { font-size: 12.5px; color: var(--tx-low); margin: 0; max-width: 380px; line-height: 1.6; }
</style>
