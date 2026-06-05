<script lang="ts">
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { api } from "$api/client";
  import { toast } from "$stores/toast";
  import Button from "$components/ui/Button.svelte";
  import Badge from "$components/ui/Badge.svelte";
  import {
    ArrowLeft, Pencil, Save, X, UserCheck, Upload,
    GraduationCap, TrendingUp, Shield, Plus, Trash2,
    Check, AlertCircle, Copy, Loader2, Camera,
    User, Briefcase, Phone, Info,
  } from "@lucide/svelte";
  import type { StaffMemberDetail, Qualification, Promotion, InviteResponse, UserRole, StaffPermissionsResponse, Role } from "$api/types";
  import type { PageData } from "./+page";
  import { confirmDialog } from "$stores/confirm";
  import { auth } from "$lib/stores/auth";
  import { schoolBranding } from "$stores/school";

  export let data: PageData;

  $: canManageStaff      = $auth.user?.system_role === "SUPERADMIN" || $auth.user?.permissions?.manage_staff === true;
  $: canManageUsers      = $auth.user?.system_role === "SUPERADMIN" || $auth.user?.permissions?.manage_users === true;
  $: canManagePromotions = $auth.user?.system_role === "SUPERADMIN" || $auth.user?.permissions?.manage_promotions === true;

  const staffId = $page.params.id;

  // ── Data — ready before mount via +page.ts ────────────────────────
  let member: StaffMemberDetail = data.member;
  $: if (data.member.id !== member.id) { member = data.member; tab = "profile"; staffPerms = null; }

  function apiError(e: unknown): string {
    const err = e as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail ?? "Something went wrong.";
  }

  // ── Tab ───────────────────────────────────────────────────────────
  let tab: "profile" | "qualifications" | "promotions" | "account" = "profile";

  // ── Inline edit ───────────────────────────────────────────────────
  let editing = false;
  let saving = false;
  let saveError = "";
  let editForm: Record<string, unknown> = {};

  function startEdit() {
    if (!member) return;
    editForm = {
      first_name: member.first_name, middle_name: member.middle_name ?? "",
      last_name: member.last_name, gender: member.gender ?? "",
      date_of_birth: member.date_of_birth ?? "", phone: member.phone ?? "",
      personal_email: member.personal_email ?? "", address: member.address ?? "",
      emergency_contact_name: member.emergency_contact_name ?? "",
      emergency_contact_phone: member.emergency_contact_phone ?? "",
      category: member.category, employment_type: member.employment_type,
      designation: member.designation ?? "", date_joined: member.date_joined ?? "",
      staff_id: member.staff_id ?? "", ges_staff_id: member.ges_staff_id ?? "",
      registered_no: member.registered_no ?? "", licence_no: member.licence_no ?? "",
      ssnit_no: member.ssnit_no ?? "",
    };
    editing = true;
  }

  function cancelEdit() { editing = false; saveError = ""; }

  async function saveProfile() {
    saving = true; saveError = "";
    const payload: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(editForm)) {
      payload[k] = v === "" ? null : v;
    }
    try {
      const { data } = await api.patch<StaffMemberDetail>(`/staff/${staffId}`, payload);
      member = { ...member!, ...data };
      editing = false;
      toast.success("Profile updated");
    } catch (e) {
      saveError = apiError(e);
    } finally {
      saving = false;
    }
  }

  // ── Photo upload ──────────────────────────────────────────────────
  let photoUploading = false;

  async function handlePhotoChange(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    photoUploading = true;
    try {
      const fd = new FormData(); fd.append("file", file);
      const { data } = await api.post<StaffMemberDetail>(`/staff/${staffId}/photo`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      member = { ...member!, photo_url: data.photo_url };
      toast.success("Photo updated");
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      photoUploading = false;
    }
  }

  // ── Qualifications ────────────────────────────────────────────────
  let addingQual = false;
  let qualForm = { degree: "", institution: "", year: "" };
  let qualSaving = false;
  let qualError = "";

  let editingQualId: string | null = null;
  let qualEditForm = { degree: "", institution: "", year: "" };
  let qualEditSaving = false;
  let qualEditError = "";

  function openQualForm() { qualForm = { degree: "", institution: "", year: "" }; qualError = ""; addingQual = true; }
  function cancelQual() { addingQual = false; qualError = ""; }

  function startEditQual(q: Qualification) {
    editingQualId = q.id;
    qualEditForm = { degree: q.degree, institution: q.institution, year: q.year?.toString() ?? "" };
    qualEditError = "";
  }
  function cancelEditQual() { editingQualId = null; qualEditError = ""; }

  async function saveQual() {
    if (!qualForm.degree || !qualForm.institution) { qualError = "Degree and institution are required."; return; }
    qualSaving = true; qualError = "";
    try {
      const payload: Record<string, unknown> = { degree: qualForm.degree, institution: qualForm.institution };
      if (qualForm.year) payload.year = parseInt(qualForm.year);
      const { data } = await api.post<Qualification>(`/staff/${staffId}/qualifications`, payload);
      member = { ...member!, qualifications: [...(member?.qualifications ?? []), data] };
      addingQual = false;
      toast.success("Qualification added");
    } catch (e) {
      qualError = apiError(e);
    } finally {
      qualSaving = false;
    }
  }

  async function saveEditQual() {
    if (!qualEditForm.degree || !qualEditForm.institution) { qualEditError = "Degree and institution are required."; return; }
    qualEditSaving = true; qualEditError = "";
    try {
      const payload: Record<string, unknown> = { degree: qualEditForm.degree, institution: qualEditForm.institution };
      if (qualEditForm.year) payload.year = parseInt(qualEditForm.year);
      const { data } = await api.patch<Qualification>(`/staff/${staffId}/qualifications/${editingQualId}`, payload);
      member = { ...member!, qualifications: (member?.qualifications ?? []).map(q => q.id === data.id ? data : q) };
      editingQualId = null;
      toast.success("Qualification updated");
    } catch (e) {
      qualEditError = apiError(e);
    } finally {
      qualEditSaving = false;
    }
  }

  async function removeQual(id: string) {
    const ok = await confirmDialog.show({
      title: "Remove qualification",
      message: "This record will be permanently deleted.",
      variant: "danger",
      confirmLabel: "Remove",
    });
    if (!ok) return;
    try {
      await api.delete(`/staff/${staffId}/qualifications/${id}`);
      member = { ...member!, qualifications: (member?.qualifications ?? []).filter(q => q.id !== id) };
      toast.success("Removed");
    } catch (e) {
      toast.error(apiError(e));
    }
  }

  // ── Promotions ────────────────────────────────────────────────────
  let addingProm = false;
  let promForm = { rank: "", date_promoted: "" };
  let promSaving = false;
  let promError = "";

  let editingPromId: string | null = null;
  let promEditForm = { rank: "", date_promoted: "" };
  let promEditSaving = false;
  let promEditError = "";

  const TEACHING_RANKS = [
    "Director General", "Deputy Director General", "Director I", "Director II",
    "Deputy Director", "Assistant Director I",
    "Principal Supt Professional",
    "Senior Superintendent I Professional", "Senior Superintendent II Professional",
    "Senior Supervisor Instructor", "Supervisor Instructor",
    "Superintendent I Professional", "Principal Technical Instructor",
    "Superintendent I", "Senior Technical Instructor",
    "Superintendent II", "Technical Instructor I", "Technical Instructor II",
    "Senior Craft Instructor", "Trainee Teacher", "Craft Instructor", "Pupil Teacher",
  ];

  const NON_TEACHING_RANKS = [
    // Accountants
    "Chief Accountant", "Chief Accountant II", "Deputy Chief Accountant", "Deputy Chief Accountant II",
    "Principal Accountant (Chartered)", "Principal Accountant (Unit Head)", "Principal Accountant (Basic Grade)",
    "Senior Accountant", "Accountant", "Assistant Accountant",
    // Admin
    "Chief Admin Officer", "Chief Admin Officer II", "Deputy Chief Admin Officer", "Deputy Chief Admin Officer II",
    "Principal Admin Officer (Chartered)", "Principal Admin Officer (Unit Head)", "Principal Admin Officer (Basic Grade)",
    "Senior Admin Officer", "Administrative Officer", "Assistant Admin Officer",
    "Senior Clerk", "Clerk Grade I", "Clerk Grade II",
    // Domestic / Bursar
    "Chief Domestic Bursar", "Deputy Chief Domestic Bursar", "Principal Domestic Bursar",
    "Senior Domestic Bursar", "Domestic Bursar", "Assistant Domestic Bursar",
    "Senior Matron", "Matron", "Chief Cook", "Cook", "Assistant Cook",
    "Head Steward", "Steward", "Head Laundry Man", "Laundry Man",
    "Head Pantry Hand", "Pantry Hand", "House Moth", "Snr House Mother", "House Mother",
    // Library
    "Chief Librarian", "Deputy Chief Librarian", "Principal Library", "Senior Library",
    "Library", "Assistant Library", "Senior Library Assistant", "Library Assistant", "Junior Library Assistant",
    // Laboratory
    "Chief Laboratory Technician", "Deputy Chief Lab Technician", "Principal Lab Technician",
    "Senior Lab Technician", "Laboratory Technician", "Assistant Lab Technician",
    "Senior Lab Assistant", "Laboratory Assistant GD I", "Laboratory Assistant GD II",
    // Secretarial
    "Principal Private Secretary", "Senior Private Secretary", "Private Secretary",
    "Stenographer Secretary", "Stenographer GD I", "Stenographer GD II",
    "Principal Typist", "Senior Typist", "Typist Grade I", "Typist Grade II", "Ungraded Typist",
    // Printing
    "Senior Rota Print Operator", "Rota Print Operator", "Rota Print",
    // Technical
    "Chief Technical Officer", "Deputy Chief Tech. Officer", "Principal Technical Officer",
    "Senior Technical Officer", "Technical Officer", "Asst. Technical Officer",
    "Senior Technical Assistant", "Technical Assistant Grade I", "Technical Assistant Grade II",
    // Workshop
    "Workshop Supervisor", "Foreman", "Junior Foreman", "Artisan",
    "Supervisory Tradesman", "Tradesman GD I", "Tradesman GD II",
    // Farm
    "Senior Farm Supervisor", "Farm Supervisor", "Farm Assistant", "Senior Farm Hand", "Farm Hand",
    // Misc
    "Receptionist", "Telephonist", "Telephone Operator", "Chief Messenger", "Messenger",
    // Supply / Stores
    "Chief Supply Officer", "Deputy Chief Supply Officer", "Principal Supply Officer",
    "Senior Supply Officer", "Supply Officer", "Principal Storekeeper",
    "Senior Storekeeper", "Storekeeper", "Assistant Storekeeper", "Store Assistant",
    // Porters
    "Head Porter", "Principal Porter", "Senior Porter", "Porter", "Asst. Porter", "Junior Porter",
    // Caretakers
    "Supervising Caretaker", "Senior Caretaker", "Caretaker",
    // Watchmen / Gatemen
    "Head Watchman/Gateman", "Senior Watchman/Gateman", "Night Watchman/Gateman", "Day Watchman/Gateman",
    // Drivers
    "Yard Foreman", "Chief Driver", "Principal Driver", "Senior Driver",
    "Driver GD I/ Driver Mechanic", "Driver GD II", "Tractor Operator",
  ];

  $: rankList = member?.category === "TEACHING" ? TEACHING_RANKS : NON_TEACHING_RANKS;

  function openPromForm() { promForm = { rank: "", date_promoted: "" }; promError = ""; addingProm = true; }
  function cancelProm() { addingProm = false; promError = ""; }

  function startEditProm(p: Promotion) {
    editingPromId = p.id;
    promEditForm = { rank: p.rank, date_promoted: p.date_promoted };
    promEditError = "";
  }
  function cancelEditProm() { editingPromId = null; promEditError = ""; }

  async function saveEditProm() {
    if (!promEditForm.rank || !promEditForm.date_promoted) { promEditError = "Rank and date are required."; return; }
    promEditSaving = true; promEditError = "";
    try {
      const { data } = await api.patch<Promotion>(`/staff/${staffId}/promotions/${editingPromId}`, {
        rank: promEditForm.rank,
        date_promoted: promEditForm.date_promoted,
      });
      member = { ...member!, promotions: (member?.promotions ?? []).map(p => p.id === data.id ? data : p) };
      editingPromId = null;
      toast.success("Promotion updated");
    } catch (e) {
      promEditError = apiError(e);
    } finally {
      promEditSaving = false;
    }
  }

  async function saveProm() {
    if (!promForm.rank || !promForm.date_promoted) { promError = "Rank and date are required."; return; }
    promSaving = true; promError = "";
    try {
      const { data } = await api.post<Promotion>(`/staff/${staffId}/promotions`, {
        rank: promForm.rank,
        date_promoted: promForm.date_promoted,
      });
      member = { ...member!, promotions: [data, ...(member?.promotions ?? [])] };
      addingProm = false;
      toast.success("Promotion recorded");
    } catch (e) {
      promError = apiError(e);
    } finally {
      promSaving = false;
    }
  }

  async function removeProm(id: string) {
    const ok = await confirmDialog.show({
      title: "Remove promotion record",
      message: "This rank history entry will be permanently deleted.",
      variant: "danger",
      confirmLabel: "Remove",
    });
    if (!ok) return;
    try {
      await api.delete(`/staff/${staffId}/promotions/${id}`);
      member = { ...member!, promotions: (member?.promotions ?? []).filter(p => p.id !== id) };
      toast.success("Removed");
    } catch (e) {
      toast.error(apiError(e));
    }
  }

  // ── Invite flow ───────────────────────────────────────────────────
  let showInviteForm = false;
  let inviteSending = false;
  let inviteEmail = "";
  let inviteError = "";
  let inviteResult: InviteResponse | null = null;
  let inviteCopied = false;

  $: inviteUrl = inviteResult ? `${window.location.origin}/invite/${inviteResult.invite_token}` : "";

  function openInviteForm() {
    inviteEmail = member?.personal_email ?? "";
    inviteError = ""; inviteResult = null;
    showInviteForm = true;
  }
  function closeInviteForm() { showInviteForm = false; inviteResult = null; inviteError = ""; }

  async function sendInvite() {
    if (!inviteEmail) { inviteError = "Email is required."; return; }
    inviteSending = true; inviteError = "";
    try {
      const { data } = await api.post<InviteResponse>(`/staff/${staffId}/invite`, { email: inviteEmail });
      inviteResult = data;
      member = { ...member!, has_account: true, invite_pending: true };
      toast.success("Invite sent");
    } catch (e) {
      inviteError = apiError(e);
    } finally {
      inviteSending = false;
    }
  }

  async function copyInviteLink() {
    await navigator.clipboard.writeText(inviteUrl);
    inviteCopied = true;
    setTimeout(() => inviteCopied = false, 2500);
  }

  // ── Resend invite ─────────────────────────────────────────────────
  let reshowInviteForm = false;

  async function resendInvite() {
    if (!inviteEmail) return;
    reshowInviteForm = true; inviteError = "";
    try {
      const { data } = await api.post<InviteResponse>(`/staff/${staffId}/invite`, { email: inviteEmail });
      inviteResult = data;
      toast.success("Invite resent");
    } catch (e) {
      inviteError = apiError(e);
    } finally {
      reshowInviteForm = false;
    }
  }

  // ── Reactivate staff ──────────────────────────────────────────────
  let reactivating = false;

  async function reactivate() {
    const ok = await confirmDialog.show({
      title: "Reactivate staff member",
      message: `${member?.first_name} ${member?.last_name} will be restored to active status and their login account re-enabled.`,
      confirmLabel: "Reactivate",
    });
    if (!ok) return;
    reactivating = true;
    try {
      await api.post(`/staff/${staffId}/reactivate`);
      member = { ...member!, is_active: true };
      toast.success("Staff member reactivated");
    } catch (e) { toast.error(apiError(e)); }
    finally { reactivating = false; }
  }

  // ── Roles & permissions ───────────────────────────────────────────
  let staffPerms: StaffPermissionsResponse | null = null;
  let permsLoading = false;
  let allRoles: Role[] = [];
  let addingRole = false;
  let selectedRoleId = "";
  let roleAdding = false;

  async function loadPerms() {
    if (!member?.has_account) return;
    permsLoading = true;
    try {
      const [permsRes, rolesRes] = await Promise.all([
        api.get<StaffPermissionsResponse>(`/staff/${staffId}/permissions`),
        api.get<Role[]>("/settings/positions"),
      ]);
      staffPerms = permsRes.data;
      allRoles = rolesRes.data;
    } catch { /* ignore */ } finally {
      permsLoading = false;
    }
  }

  $: if (tab === "account" && member?.has_account && !staffPerms) {
    loadPerms();
  }

  $: assignedRoleIds = new Set(staffPerms?.roles.map(r => r.role.id) ?? []);
  $: availableRoles = allRoles.filter(r => !assignedRoleIds.has(r.id));

  async function addRole() {
    if (!selectedRoleId) return;
    roleAdding = true;
    try {
      await api.post(`/staff/${staffId}/roles`, { role_id: selectedRoleId });
      await loadPerms();
      addingRole = false; selectedRoleId = "";
      toast.success("Role assigned");
    } catch (e) {
      toast.error(apiError(e));
    } finally { roleAdding = false; }
  }

  async function removeRole(userRoleId: string) {
    const ok = await confirmDialog.show({
      title: "Remove role",
      message: "The role and its permissions will be revoked immediately.",
      variant: "danger", confirmLabel: "Remove",
    });
    if (!ok) return;
    try {
      await api.delete(`/staff/${staffId}/roles/${userRoleId}`);
      toast.success("Role removed");
      await loadPerms(); // refreshes roles + recomputes effective permissions
    } catch (e) { toast.error(apiError(e)); }
  }

  // ── Permission overrides ─────────────────────────────────────────
  const PERM_GROUPS: { label: string; keys: string[] }[] = [
    { label: "Students",     keys: ["view_students", "enroll_students", "transfer_students"] },
    { label: "Staff",        keys: ["view_staff", "manage_staff", "manage_promotions"] },
    { label: "Academics",    keys: ["view_scores", "enter_scores", "approve_scores", "manage_timetable"] },
    { label: "Attendance",   keys: ["mark_attendance", "view_attendance"] },
    { label: "Reports",      keys: ["generate_reports", "revoke_documents"] },
    { label: "Fees",         keys: ["view_fees", "record_payments", "manage_fee_structure", "waive_fees"] },
    { label: "Communication",keys: ["send_sms", "send_announcements"] },
    { label: "Houses",       keys: ["manage_houses", "manage_exeats", "night_roll_call"] },
    { label: "Settings",     keys: ["manage_school_config", "manage_academic_structure", "manage_users", "view_analytics"] },
  ];

  // Any permission the backend returns that isn't listed above lands here,
  // so new backend permissions are never silently invisible in the UI.
  const KNOWN_PERM_KEYS = new Set(PERM_GROUPS.flatMap(g => g.keys));
  $: unknownPermKeys = staffPerms
    ? Object.keys(staffPerms.permissions).filter(k => !KNOWN_PERM_KEYS.has(k))
    : [];
  $: allPermGroups = unknownPermKeys.length > 0
    ? [...PERM_GROUPS, { label: "Other", keys: unknownPermKeys }]
    : PERM_GROUPS;

  let savingPerms: Set<string> = new Set();
  let addingOverride = false;
  let newOverridePerm = "";
  let newOverrideGranted = true;

  async function saveNewOverride() {
    if (!newOverridePerm) return;
    await setOverride(newOverridePerm, newOverrideGranted);
    addingOverride = false;
    newOverridePerm = "";
  }

  async function setOverride(key: string, granted: boolean) {
    savingPerms = new Set([...savingPerms, key]);
    try {
      await api.post(`/staff/${staffId}/permissions`, { permission_key: key, granted });
      await loadPerms();
      toast.success(granted ? `${key.replace(/_/g, " ")} granted` : `${key.replace(/_/g, " ")} denied`);
    } catch (e) { toast.error(apiError(e)); }
    finally { savingPerms = new Set([...savingPerms].filter(k => k !== key)); }
  }

  async function clearOverride(key: string) {
    savingPerms = new Set([...savingPerms, key]);
    try {
      await api.delete(`/staff/${staffId}/permissions/${key}`);
      await loadPerms();
      toast.success(`Override removed — ${key.replace(/_/g, " ")} now follows role`);
    } catch (e) { toast.error(apiError(e)); }
    finally { savingPerms = new Set([...savingPerms].filter(k => k !== key)); }
  }

  // ── Account role preview ──────────────────────────────────────────
  const DESIG_ROLE_LABEL: Record<string, string> = {
    HEADTEACHER: "Headteacher", ASSISTANT_HEAD: "Assistant Headteacher",
    BURSAR: "Bursar", HOUSEMASTER: "Housemaster", SENIOR_HOUSEMASTER: "Senior Housemaster",
  };
  $: defaultRoleLabel = !member ? null
    : member.designation && DESIG_ROLE_LABEL[member.designation]
      ? DESIG_ROLE_LABEL[member.designation]
      : member.category === "TEACHING" ? "Class Teacher" : null;

  // ── Helpers ───────────────────────────────────────────────────────
  function initials(m: StaffMemberDetail) {
    return (m.first_name.charAt(0) + m.last_name.charAt(0)).toUpperCase();
  }

  const CATEGORY_COLORS: Record<string, string> = {
    TEACHING: "#3b82f6",
    "NON-TEACHING": "#8b5cf6",
  };

  function fmt(d: string | null | undefined) {
    if (!d) return "—";
    try { return new Date(d + "T00:00:00").toLocaleDateString("en-GH", { day: "numeric", month: "short", year: "numeric" }); }
    catch { return d; }
  }

  function humanise(s: string | null | undefined): string {
    if (!s) return "—";
    return s.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  }

  function categoryClass(cat: string) {
    return cat === "TEACHING" ? "badge-accent" : "badge-neutral";
  }

  function employmentClass(t: string) {
    return ({ PERMANENT: "badge-green", CONTRACT: "badge-orange",
               VOLUNTEER: "badge-blue",  GES_POSTED: "badge-purple" })[t] ?? "badge-neutral";
  }

  $: fullName = [member.first_name, member.middle_name, member.last_name].filter(Boolean).join(" ");
</script>

<svelte:head>
  <title>{fullName} — {$schoolBranding?.name ?? 'TTEK-SMS'}</title>
</svelte:head>

<div class="page">

    <!-- Back -->
    <button class="back-btn" on:click={() => goto("/staff")}>
      <ArrowLeft size={14} /> Staff
    </button>

    <!-- Hero card -->
    <div class="hero">
      <!-- Photo -->
      <div class="photo-wrap">
        <div class="photo-avatar" style="background:{CATEGORY_COLORS[member.category] ?? 'var(--accent)'}">
          {#if member.photo_url}
            <img src={member.photo_url} alt={member.first_name} class="photo-img" />
          {:else}
            {initials(member)}
          {/if}
        </div>
        <span class="status-dot" class:dot-active={member.is_active} title={member.is_active ? "Active" : "Inactive"}></span>
        <label class="photo-btn" title="Change photo">
          {#if photoUploading}
            <Loader2 size={12} class="spin" />
          {:else}
            <Camera size={12} />
          {/if}
          <input type="file" accept="image/*" on:change={handlePhotoChange} style="display:none" />
        </label>
      </div>

      <!-- Name + meta -->
      <div class="hero-body">
        <div class="hero-top">
          <div>
            <h1 class="hero-name">{fullName}</h1>
            <div class="hero-sub">
              {#if member.staff_id}
                <code class="staff-id-code">ID: {member.staff_id}</code>
              {/if}
              <span class="cat-pill cat-pill-{member.category}">{humanise(member.category)}</span>
              <span class="emp-pill emp-pill-{member.employment_type}">{humanise(member.employment_type)}</span>
              {#if member.designation}
                <span class="desig-pill">{humanise(member.designation)}</span>
              {/if}
            </div>
            {#if member.current_rank}
              <p class="current-rank-line">{member.current_rank}</p>
            {/if}
          </div>
          <div class="hero-actions">
            {#if !member.is_active && canManageStaff}
              <Button variant="ghost" size="sm" loading={reactivating} on:click={reactivate}>
                <UserCheck size={13} /> Reactivate
              </Button>
            {/if}
            {#if !member.has_account && canManageUsers}
              <Button variant="ghost" size="sm" on:click={openInviteForm}>
                <UserCheck size={13} /> Send Invite
              </Button>
            {/if}
            {#if !editing && canManageStaff}
              <Button size="sm" on:click={startEdit}>
                <Pencil size={13} /> Edit Profile
              </Button>
            {/if}
          </div>
        </div>

        <!-- Stat strip -->
        <div class="stat-strip">
          <div class="stat">
            <span class="stat-label">Status</span>
            <span class="stat-val" class:stat-active={member.is_active} class:stat-inactive={!member.is_active}>
              {member.is_active ? "Active" : "Inactive"}
            </span>
          </div>
          {#if member.date_joined}
            <div class="stat-div"></div>
            <div class="stat">
              <span class="stat-label">Date Joined</span>
              <span class="stat-val">{fmt(member.date_joined)}</span>
            </div>
          {/if}
          {#if member.phone}
            <div class="stat-div"></div>
            <div class="stat">
              <span class="stat-label">Phone</span>
              <span class="stat-val">{member.phone}</span>
            </div>
          {/if}
          {#if member.personal_email}
            <div class="stat-div"></div>
            <div class="stat">
              <span class="stat-label">Email</span>
              <span class="stat-val">{member.personal_email}</span>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <nav class="tab-nav">
      <button class="tn-item" class:tn-active={tab === "profile"} on:click={() => tab = "profile"}>
        <User size={13} /> Profile
      </button>
      <button class="tn-item" class:tn-active={tab === "qualifications"} on:click={() => tab = "qualifications"}>
        <GraduationCap size={13} /> Qualifications
        {#if member.qualifications.length > 0}<span class="tn-count">{member.qualifications.length}</span>{/if}
      </button>
      <button class="tn-item" class:tn-active={tab === "promotions"} on:click={() => tab = "promotions"}>
        <TrendingUp size={13} /> GES Rank History
        {#if member.promotions.length > 0}<span class="tn-count">{member.promotions.length}</span>{/if}
      </button>
      <button class="tn-item" class:tn-active={tab === "account"} on:click={() => tab = "account"}>
        <Shield size={13} /> Account
      </button>
    </nav>

    <!-- ── Profile tab ──────────────────────────────────────────── -->
    {#if tab === "profile"}
      {#if editing}
        <div class="edit-wrap">
          <div class="edit-toolbar">
            <span class="edit-title">Edit Profile</span>
            <div class="card-actions">
              <Button variant="ghost" size="sm" on:click={cancelEdit}>Cancel</Button>
              <Button size="sm" loading={saving} on:click={saveProfile}><Save size={13} /> Save</Button>
            </div>
          </div>
          {#if saveError}<p class="form-error">{saveError}</p>{/if}

          <div class="edit-cols">

            <!-- Left column -->
            <div class="edit-col">

              <div class="edit-card">
                <div class="edit-card-head"><div class="card-hicon"><User size={13} /></div>Personal Information</div>
                <div class="edit-card-body">
                  <div class="row-3">
                    <div class="field">
                      <label for="ef-first">First name</label>
                      <input id="ef-first" class="input" bind:value={editForm.first_name} />
                    </div>
                    <div class="field">
                      <label for="ef-mid">Middle name</label>
                      <input id="ef-mid" class="input" bind:value={editForm.middle_name} />
                    </div>
                    <div class="field">
                      <label for="ef-last">Last name</label>
                      <input id="ef-last" class="input" bind:value={editForm.last_name} />
                    </div>
                  </div>
                  <div class="row-2">
                    <div class="field">
                      <label for="ef-gender">Gender</label>
                      <select id="ef-gender" class="input" bind:value={editForm.gender}>
                        <option value="">— select —</option>
                        <option value="MALE">Male</option>
                        <option value="FEMALE">Female</option>
                        <option value="OTHER">Other</option>
                      </select>
                    </div>
                    <div class="field">
                      <label for="ef-dob">Date of birth</label>
                      <input id="ef-dob" class="input" type="date" bind:value={editForm.date_of_birth} />
                    </div>
                  </div>
                </div>
              </div>

              <div class="edit-card">
                <div class="edit-card-head"><div class="card-hicon"><Phone size={13} /></div>Contact Details</div>
                <div class="edit-card-body">
                  <div class="row-2">
                    <div class="field">
                      <label for="ef-phone">Phone number</label>
                      <input id="ef-phone" class="input" bind:value={editForm.phone} type="tel" />
                    </div>
                    <div class="field">
                      <label for="ef-email">Personal email</label>
                      <input id="ef-email" class="input" type="email" bind:value={editForm.personal_email} />
                    </div>
                  </div>
                  <div class="field">
                    <label for="ef-addr">Home address</label>
                    <input id="ef-addr" class="input" bind:value={editForm.address} />
                  </div>
                  <div class="edit-divider"></div>
                  <p class="edit-section-label">Emergency contact</p>
                  <div class="row-2">
                    <div class="field">
                      <label for="ef-ecn">Contact name</label>
                      <input id="ef-ecn" class="input" bind:value={editForm.emergency_contact_name} />
                    </div>
                    <div class="field">
                      <label for="ef-ecp">Contact phone</label>
                      <input id="ef-ecp" class="input" type="tel" bind:value={editForm.emergency_contact_phone} />
                    </div>
                  </div>
                </div>
              </div>

            </div>

            <!-- Right column -->
            <div class="edit-col">

              <div class="edit-card">
                <div class="edit-card-head"><div class="card-hicon"><Briefcase size={13} /></div>Employment</div>
                <div class="edit-card-body">
                  <div class="row-2">
                    <div class="field">
                      <label for="ef-cat">Category</label>
                      <select id="ef-cat" class="input" bind:value={editForm.category}>
                        <option value="TEACHING">Teaching</option>
                        <option value="NON-TEACHING">Non-Teaching</option>
                      </select>
                    </div>
                    <div class="field">
                      <label for="ef-emp">Employment type</label>
                      <select id="ef-emp" class="input" bind:value={editForm.employment_type}>
                        <option value="PERMANENT">Permanent</option>
                        <option value="CONTRACT">Contract</option>
                        <option value="VOLUNTEER">Volunteer</option>
                        <option value="GES_POSTED">GES Posted</option>
                      </select>
                    </div>
                  </div>
                  <div class="field">
                    <label for="ef-desig">Designation</label>
                    <select id="ef-desig" class="input" bind:value={editForm.designation}>
                      <option value="">— select —</option>
                      <option value="TEACHER">Teacher</option>
                      <option value="HEADTEACHER">Headteacher</option>
                      <option value="ASSISTANT_HEAD">Assistant Head</option>
                      <option value="BURSAR">Bursar</option>
                      <option value="HOUSEMASTER">Housemaster</option>
                      <option value="SENIOR_HOUSEMASTER">Senior Housemaster</option>
                    </select>
                  </div>
                  <div class="row-2">
                    <div class="field">
                      <label for="ef-sid">School staff ID</label>
                      <input id="ef-sid" class="input" bind:value={editForm.staff_id} />
                    </div>
                    <div class="field">
                      <label for="ef-joined">Date joined</label>
                      <input id="ef-joined" class="input" type="date" bind:value={editForm.date_joined} />
                    </div>
                  </div>
                </div>
              </div>

              <div class="edit-card">
                <div class="edit-card-head"><div class="card-hicon"><Shield size={13} /></div>GES Details</div>
                <div class="edit-card-body">
                  <div class="row-2">
                    <div class="field">
                      <label for="ef-ges">GES staff ID</label>
                      <input id="ef-ges" class="input" bind:value={editForm.ges_staff_id} />
                    </div>
                    <div class="field">
                      <label for="ef-reg">Registered no.</label>
                      <input id="ef-reg" class="input" bind:value={editForm.registered_no} />
                    </div>
                  </div>
                  <div class="row-2">
                    <div class="field">
                      <label for="ef-lic">Licence no.</label>
                      <input id="ef-lic" class="input" bind:value={editForm.licence_no} />
                    </div>
                    <div class="field">
                      <label for="ef-ssnit">SSNIT no.</label>
                      <input id="ef-ssnit" class="input" bind:value={editForm.ssnit_no} />
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      {:else}
        <!-- View mode — info-grid layout -->
        <div class="profile-card">

          <!-- Personal section -->
          <div class="prof-section">
            <p class="prof-section-label"><User size={11} /> Personal</p>
            <div class="prof-grid">
              <div class="prof-field">
                <span class="pf-label">First name</span>
                <span class="pf-val">{member.first_name}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">Middle name</span>
                <span class="pf-val">{member.middle_name ?? "—"}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">Last name</span>
                <span class="pf-val">{member.last_name}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">Gender</span>
                <span class="pf-val">{humanise(member.gender)}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">Date of birth</span>
                <span class="pf-val">{fmt(member.date_of_birth)}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">Address</span>
                <span class="pf-val">{member.address ?? "—"}</span>
              </div>
            </div>
          </div>

          <div class="prof-divider"></div>

          <!-- Employment section -->
          <div class="prof-section">
            <p class="prof-section-label"><Briefcase size={11} /> Employment</p>
            <div class="prof-grid">
              <div class="prof-field">
                <span class="pf-label">Category</span>
                <span class="pf-val">{humanise(member.category)}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">Employment type</span>
                <span class="pf-val">{humanise(member.employment_type)}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">Designation</span>
                <span class="pf-val">{humanise(member.designation)}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">Date joined</span>
                <span class="pf-val">{fmt(member.date_joined)}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">School staff ID</span>
                <span class="pf-val pf-mono">{member.staff_id ?? "—"}</span>
              </div>
            </div>
          </div>

          <div class="prof-divider"></div>

          <!-- GES Details section -->
          <div class="prof-section">
            <p class="prof-section-label"><Shield size={11} /> GES Details</p>
            <div class="prof-grid">
              <div class="prof-field">
                <span class="pf-label">GES staff ID</span>
                <span class="pf-val pf-mono">{member.ges_staff_id ?? "—"}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">Registered no.</span>
                <span class="pf-val pf-mono">{member.registered_no ?? "—"}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">Licence no.</span>
                <span class="pf-val pf-mono">{member.licence_no ?? "—"}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">SSNIT no.</span>
                <span class="pf-val pf-mono">{member.ssnit_no ?? "—"}</span>
              </div>
            </div>
          </div>

          <div class="prof-divider"></div>

          <!-- Emergency contact section -->
          <div class="prof-section">
            <p class="prof-section-label"><Phone size={11} /> Emergency Contact</p>
            <div class="prof-grid">
              <div class="prof-field">
                <span class="pf-label">Name</span>
                <span class="pf-val">{member.emergency_contact_name ?? "—"}</span>
              </div>
              <div class="prof-field">
                <span class="pf-label">Phone</span>
                <span class="pf-val">{member.emergency_contact_phone ?? "—"}</span>
              </div>
            </div>
          </div>

        </div>
      {/if}

    <!-- ── Qualifications tab ─────────────────────────────────────── -->
    {:else if tab === "qualifications"}
      <div class="section-card">
        <div class="card-header">
          <div class="card-hicon"><GraduationCap size={14} /></div>
          <span class="card-title">Academic Qualifications</span>
          {#if !addingQual && canManageStaff}
            <Button size="sm" on:click={openQualForm}><Plus size={13} /> Add</Button>
          {/if}
        </div>
        <div class="card-body">

        {#if addingQual}
          <div class="inline-form">
            {#if qualError}<p class="inline-form-error">{qualError}</p>{/if}
            <div class="inline-form-row">
              <div class="field">
                <label for="qf-deg">Degree / Certificate <span class="req">*</span></label>
                <input id="qf-deg" class="input" bind:value={qualForm.degree} placeholder="e.g. B.Ed. Basic Education" />
              </div>
              <div class="field">
                <label for="qf-inst">Institution <span class="req">*</span></label>
                <input id="qf-inst" class="input" bind:value={qualForm.institution} placeholder="e.g. University of Education" />
              </div>
              <div class="field field-year">
                <label for="qf-year">Year</label>
                <input id="qf-year" class="input" type="number" bind:value={qualForm.year} placeholder="2018" min="1960" max={new Date().getFullYear()} />
              </div>
            </div>
            <div class="inline-form-actions">
              <Button variant="ghost" size="sm" on:click={cancelQual}>Cancel</Button>
              <Button size="sm" loading={qualSaving} on:click={saveQual}>Save</Button>
            </div>
          </div>
        {/if}

        {#if member.qualifications.length === 0 && !addingQual}
          <p class="empty-note">No qualifications recorded yet.</p>
        {:else if member.qualifications.length > 0}
          <div class="qual-table-wrap">
            <table class="sub-table">
              <thead>
                <tr><th>Degree / Certificate</th><th>Institution</th><th>Year</th><th></th></tr>
              </thead>
              <tbody>
                {#each member.qualifications as q}
                  {#if editingQualId === q.id}
                    <tr class="edit-row">
                      <td>
                        {#if qualEditError}
                          <p class="row-edit-error">{qualEditError}</p>
                        {/if}
                        <input class="input" bind:value={qualEditForm.degree} placeholder="Degree / Certificate" />
                      </td>
                      <td><input class="input" bind:value={qualEditForm.institution} placeholder="Institution" /></td>
                      <td><input class="input" type="number" bind:value={qualEditForm.year} placeholder="Year" min="1960" /></td>
                      <td class="action-cell row-edit-actions">
                        <button class="icon-btn" on:click={cancelEditQual} title="Cancel"><X size={13} /></button>
                        <button class="icon-btn save-btn" on:click={saveEditQual} disabled={qualEditSaving} title="Save">
                          {#if qualEditSaving}<Loader2 size={13} class="spin" />{:else}<Check size={13} />{/if}
                        </button>
                      </td>
                    </tr>
                  {:else}
                    <tr>
                      <td class="bold">{q.degree}</td>
                      <td>{q.institution}</td>
                      <td>{q.year ?? "—"}</td>
                      <td class="action-cell">
                        {#if canManageStaff}
                          <button class="icon-btn" on:click={() => startEditQual(q)} title="Edit"><Pencil size={13} /></button>
                          <button class="icon-btn danger" on:click={() => removeQual(q.id)} title="Remove"><Trash2 size={13} /></button>
                        {/if}
                      </td>
                    </tr>
                  {/if}
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
        </div>
      </div>

    <!-- ── Promotions / Rank history tab ─────────────────────────── -->
    {:else if tab === "promotions"}
      <div class="section-card">
        <div class="card-header">
          <div class="card-hicon"><TrendingUp size={14} /></div>
          <span class="card-title">GES Rank History</span>
          {#if !addingProm && canManagePromotions}
            <Button size="sm" on:click={openPromForm}><Plus size={13} /> Record Promotion</Button>
          {/if}
        </div>
        <div class="card-body">
        <p class="card-hint">Promotion history — latest rank at the top. Each row is an immutable record.</p>

        {#if addingProm}
          <div class="inline-form">
            {#if promError}<p class="inline-form-error">{promError}</p>{/if}
            <div class="inline-form-row">
              <div class="field">
                <label for="pf-rank">Rank <span class="req">*</span></label>
                <select id="pf-rank" class="input" bind:value={promForm.rank}>
                  <option value="">— Select rank —</option>
                  {#each rankList as rank}
                    <option value={rank}>{rank}</option>
                  {/each}
                </select>
              </div>
              <div class="field field-date">
                <label for="pf-date">Date promoted <span class="req">*</span></label>
                <input id="pf-date" class="input" type="date" bind:value={promForm.date_promoted} />
              </div>
            </div>
            <div class="inline-form-actions">
              <Button variant="ghost" size="sm" on:click={cancelProm}>Cancel</Button>
              <Button size="sm" loading={promSaving} on:click={saveProm}>Save</Button>
            </div>
          </div>
        {/if}

        {#if member.promotions.length === 0 && !addingProm}
          <p class="empty-note">No rank history recorded yet.</p>
        {:else if member.promotions.length > 0}
          <div class="qual-table-wrap">
            <table class="sub-table">
              <thead>
                <tr><th>Rank</th><th>Date Promoted</th><th>Date Recorded</th><th></th></tr>
              </thead>
              <tbody>
                {#each member.promotions as p, i}
                  {#if editingPromId === p.id}
                    <tr class="edit-row">
                      <td colspan="2">
                        {#if promEditError}
                          <p class="row-edit-error">{promEditError}</p>
                        {/if}
                        <div class="prom-edit-fields">
                          <select class="input" bind:value={promEditForm.rank}>
                            <option value="">— Select rank —</option>
                            {#each rankList as rank}
                              <option value={rank}>{rank}</option>
                            {/each}
                          </select>
                          <input class="input" type="date" bind:value={promEditForm.date_promoted} />
                        </div>
                      </td>
                      <td class="text-muted">{fmt(p.date_recorded)}</td>
                      <td class="action-cell row-edit-actions">
                        <button class="icon-btn" on:click={cancelEditProm} title="Cancel"><X size={13} /></button>
                        <button class="icon-btn save-btn" on:click={saveEditProm} disabled={promEditSaving} title="Save">
                          {#if promEditSaving}<Loader2 size={13} class="spin" />{:else}<Check size={13} />{/if}
                        </button>
                      </td>
                    </tr>
                  {:else}
                    <tr class:current-rank={i === 0}>
                      <td class="bold">
                        {p.rank}
                        {#if i === 0}<span class="current-pill">Current</span>{/if}
                      </td>
                      <td>{fmt(p.date_promoted)}</td>
                      <td class="text-muted">{fmt(p.date_recorded)}</td>
                      <td class="action-cell">
                        {#if canManagePromotions}
                          <button class="icon-btn" on:click={() => startEditProm(p)} title="Edit"><Pencil size={13} /></button>
                          <button class="icon-btn danger" on:click={() => removeProm(p.id)} title="Remove"><Trash2 size={13} /></button>
                        {/if}
                      </td>
                    </tr>
                  {/if}
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
        </div>
      </div>

    <!-- ── Account tab ────────────────────────────────────────────── -->
    {:else if tab === "account"}
      <div class="section-card">
        <div class="card-header">
          <div class="card-hicon"><UserCheck size={14} /></div>
          <span class="card-title">Login Account</span>
          {#if !member.has_account && canManageUsers}
            <Button size="sm" on:click={openInviteForm}><UserCheck size={13} /> Send Invite</Button>
          {/if}
          {#if member.invite_pending && !inviteResult && canManageUsers}
            <Button variant="ghost" size="sm" on:click={openInviteForm}>Resend</Button>
          {/if}
        </div>
        <div class="card-body">

        <!-- No account yet -->
        {#if !member.has_account && !showInviteForm}
          <div class="account-status warn">
            <AlertCircle size={16} />
            No login account yet. Send an invite so {member.first_name} can set their own password.
          </div>
        {/if}

        <!-- Invite form -->
        {#if showInviteForm && !inviteResult}
          <div class="inline-form">
            {#if inviteError}<p class="inline-form-error">{inviteError}</p>{/if}
            <div class="role-preview-row">
              {#if defaultRoleLabel}
                <Info size={13} class="role-preview-icon" />
                <span>Account will be assigned the <strong>{defaultRoleLabel}</strong> role.</span>
              {:else}
                <AlertCircle size={13} class="role-preview-icon warn" />
                <span>No default role for this designation — assign one manually after they join.</span>
              {/if}
            </div>
            <p class="hint">{member.first_name} will receive a secure link to set their own password. The link expires in 7 days.</p>
            <div class="inline-form-row">
              <div class="field">
                <label for="inv-email">Login email <span class="req">*</span></label>
                <input id="inv-email" class="input" type="email" bind:value={inviteEmail} placeholder="staff@school.edu.gh" />
              </div>
            </div>
            <div class="inline-form-actions">
              <Button variant="ghost" size="sm" on:click={closeInviteForm}>Cancel</Button>
              <Button size="sm" loading={inviteSending} on:click={sendInvite}>Send Invite</Button>
            </div>
          </div>
        {/if}

        <!-- Invite sent result -->
        {#if inviteResult}
          <div class="invite-sent-panel">
            <div class="invite-sent-header">
              <Check size={16} class="invite-check" />
              <strong>Invite sent{inviteResult.sms_sent ? ` via SMS to ${member.phone}` : ""}!</strong>
            </div>
            <p class="hint">Share this link with <strong>{member.first_name}</strong>. It expires in 7 days.</p>
            <div class="invite-link-row">
              <span class="invite-link-text">{inviteUrl}</span>
              <button class="icon-btn" on:click={copyInviteLink} title="Copy link">
                {#if inviteCopied}<Check size={13} class="copy-ok" />{:else}<Copy size={13} />{/if}
              </button>
            </div>
            <div class="inline-form-actions">
              <Button size="sm" on:click={closeInviteForm}>Done</Button>
            </div>
          </div>
        {/if}

        <!-- Pending invite state -->
        {#if member.invite_pending && !inviteResult && !showInviteForm}
          <div class="invite-pending-panel">
            <Loader2 size={14} class="pending-spin" />
            <span>Invite sent — waiting for <strong>{member.first_name}</strong> to set their password.</span>
          </div>
        {/if}

        <!-- ── Roles & permissions (only when account is active) ── -->
        {#if member.has_account && !member.invite_pending}
          {#if permsLoading}
            <div class="perms-loading"><Loader2 size={14} class="spin" /> Loading roles…</div>
          {:else if staffPerms}

            <!-- Roles section -->
            <div class="roles-section">
              <div class="roles-header">
                <span class="roles-label"><Shield size={13} /> Assigned Roles</span>
                {#if canManageUsers && !addingRole && availableRoles.length > 0}
                  <button class="add-role-btn" on:click={() => { addingRole = true; selectedRoleId = ""; }}>
                    <Plus size={12} /> Add Role
                  </button>
                {/if}
              </div>

              <div class="role-chips">
                {#each staffPerms.roles as ur}
                  <span class="role-chip">
                    {ur.role.name}
                    {#if canManageUsers}
                      <button class="chip-remove" on:click={() => removeRole(ur.id)} title="Remove role">
                        <X size={11} />
                      </button>
                    {/if}
                  </span>
                {/each}
                {#if staffPerms.roles.length === 0}
                  <span class="no-roles">No roles assigned — this account has no permissions.</span>
                {/if}
              </div>

              {#if addingRole}
                <div class="add-role-row">
                  <select class="input" bind:value={selectedRoleId}>
                    <option value="">— Select a role —</option>
                    {#each availableRoles as r}
                      <option value={r.id}>{r.name}</option>
                    {/each}
                  </select>
                  <Button size="sm" loading={roleAdding} on:click={addRole} disabled={!selectedRoleId}>Assign</Button>
                  <Button variant="ghost" size="sm" on:click={() => { addingRole = false; selectedRoleId = ""; }}>Cancel</Button>
                </div>
              {/if}
            </div>

            <!-- Effective permissions — granted only, compact chips -->
            {@const grantedKeys = Object.entries(staffPerms.permissions).filter(([,v]) => v).map(([k]) => k)}
            <div class="perms-section">
              <p class="perms-label">Effective Permissions</p>
              {#if grantedKeys.length === 0}
                <p class="perms-empty">No permissions — assign a role above.</p>
              {:else}
                <div class="perm-chips-wrap">
                  {#each grantedKeys as key}
                    {@const hasOverride = staffPerms.overrides.some(o => o.permission_key === key && o.granted)}
                    <span class="eff-chip" class:overridden={hasOverride} title={hasOverride ? "Personal override" : "From role"}>
                      {key.replace(/_/g, " ")}
                    </span>
                  {/each}
                </div>
              {/if}
            </div>

            <!-- Personal overrides — only shown when relevant -->
            {@const overrideKeys = new Set(staffPerms.overrides.map(o => o.permission_key))}
            {#if staffPerms.overrides.length > 0 || addingOverride}
              <div class="perms-section">
                <div class="perms-section-header">
                  <p class="perms-label">Personal Overrides</p>
                  {#if staffPerms.overrides.length > 0}
                    <span class="overrides-badge">{staffPerms.overrides.length}</span>
                  {/if}
                </div>
                <p class="perms-hint">These override the role's defaults for this person only.</p>

                {#each staffPerms.overrides as ov}
                  {@const saving = savingPerms.has(ov.permission_key)}
                  <div class="perm-row2">
                    <span class="perm-key2">{ov.permission_key.replace(/_/g, " ")}</span>
                    <span class="perm-override-badge" class:grant={ov.granted} class:deny={!ov.granted}>
                      {ov.granted ? "Granted" : "Denied"}
                    </span>
                    {#if canManageUsers}
                      <button class="perm-clear-btn" disabled={saving} on:click={() => clearOverride(ov.permission_key)}>
                        {saving ? "…" : "Clear"}
                      </button>
                    {/if}
                  </div>
                {/each}

                {#if addingOverride}
                  <div class="add-override-form">
                    <select class="input input-sm" bind:value={newOverridePerm}>
                      <option value="">— Pick a permission —</option>
                      {#each allPermGroups as group}
                        <optgroup label={group.label}>
                          {#each group.keys.filter(k => !overrideKeys.has(k)) as key}
                            <option value={key}>{key.replace(/_/g, " ")}</option>
                          {/each}
                        </optgroup>
                      {/each}
                    </select>
                    <div class="add-override-actions">
                      <button class="perm-act-btn grant" class:selected={newOverrideGranted}
                        on:click={() => newOverrideGranted = true}>+ Grant</button>
                      <button class="perm-act-btn deny" class:selected={!newOverrideGranted}
                        on:click={() => newOverrideGranted = false}>− Deny</button>
                      <Button size="sm" disabled={!newOverridePerm} loading={savingPerms.has(newOverridePerm)}
                        on:click={saveNewOverride}>Save</Button>
                      <Button variant="ghost" size="sm" on:click={() => { addingOverride = false; newOverridePerm = ""; }}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                {/if}
              </div>
            {/if}

            {#if canManageUsers && !addingOverride}
              <button class="add-override-btn" on:click={() => { addingOverride = true; newOverridePerm = ""; newOverrideGranted = true; }}>
                + Add permission override
              </button>
            {/if}

          {/if}

            <!-- Reset: resend invite -->
            {#if canManageUsers}
              <div class="reset-pw-section">
                <div class="reset-pw-row">
                  <div>
                    <p class="reset-pw-label">Resend invite</p>
                    <p class="reset-pw-hint">Send a new invite link if the staff member lost or never received the original.</p>
                  </div>
                  <Button variant="ghost" size="sm" loading={reshowInviteForm} on:click={() => { inviteEmail = member.personal_email ?? ""; openInviteForm(); }}>
                    Resend
                  </Button>
                </div>
              </div>
            {/if}

        {/if}
        </div>
      </div>
    {/if}

</div>



<style>
  .page { display: flex; flex-direction: column; gap: 16px; }

  /* ── Hero ─────────────────────────────────────── */
  .hero {
    position: relative;
    display: flex; align-items: flex-start; gap: 20px;
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    border-radius: 16px; padding: 24px 24px 20px;
    box-shadow: var(--shadow-xs); overflow: hidden;
  }
  .hero::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; background: var(--accent); border-radius: 16px 16px 0 0;
  }

  /* Photo wrap */
  .photo-wrap { position: relative; flex-shrink: 0; }
  .photo-avatar {
    width: 72px; height: 72px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.375rem; font-weight: 800; color: #fff;
    overflow: hidden;
    border: 3px solid var(--surface-0);
    box-shadow: 0 0 0 1px var(--border-subtle);
  }
  .photo-img { width: 100%; height: 100%; object-fit: cover; }
  .status-dot {
    position: absolute; bottom: 2px; right: 24px;
    width: 14px; height: 14px; border-radius: 50%;
    background: var(--tx-low); border: 2px solid var(--surface-1);
  }
  .status-dot.dot-active { background: #22c55e; }
  .photo-btn {
    position: absolute; bottom: -6px; right: -6px;
    width: 26px; height: 26px; border-radius: 50%;
    background: var(--surface-0); border: 2px solid var(--border-subtle);
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; color: var(--tx-mid);
    transition: background 0.12s, border-color 0.12s;
  }
  .photo-btn:hover { background: var(--surface-1); border-color: var(--accent); }

  /* Hero body */
  .hero-body { flex: 1; min-width: 0; }
  .hero-top {
    display: flex; align-items: flex-start; justify-content: space-between;
    gap: 12px; margin-bottom: 10px; flex-wrap: wrap;
  }
  .hero-name { margin: 0 0 6px; font-size: 22px; font-weight: 800; color: var(--tx-high); letter-spacing: -0.3px; line-height: 1.1; }
  .hero-sub { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .hero-actions { display: flex; gap: 8px; align-items: flex-start; flex-shrink: 0; }
  .current-rank-line { margin: 6px 0 0; font-size: 12.5px; font-weight: 500; color: var(--tx-mid); }

  .staff-id-code {
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 11.5px; font-weight: 600;
    background: var(--surface-2); color: var(--tx-mid);
    padding: 2px 8px; border-radius: 5px;
    border: 1px solid var(--border-subtle);
  }

  .cat-pill, .emp-pill, .desig-pill {
    display: inline-flex; align-items: center;
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.05em; padding: 3px 9px; border-radius: 99px;
    white-space: nowrap;
  }
  .desig-pill { background: var(--surface-2); color: var(--tx-mid); border: 1px solid var(--border-subtle); }
  .cat-pill-TEACHING    { background: color-mix(in srgb, #3b82f6 12%, transparent); color: #2563eb; border: 1px solid color-mix(in srgb, #3b82f6 25%, transparent); }
  .cat-pill-NON-TEACHING { background: color-mix(in srgb, #8b5cf6 12%, transparent); color: #7c3aed; border: 1px solid color-mix(in srgb, #8b5cf6 25%, transparent); }
  .emp-pill-PERMANENT   { background: color-mix(in srgb, #10b981 12%, transparent); color: #059669; border: 1px solid color-mix(in srgb, #10b981 25%, transparent); }
  .emp-pill-CONTRACT    { background: color-mix(in srgb, #f59e0b 12%, transparent); color: #d97706; border: 1px solid color-mix(in srgb, #f59e0b 25%, transparent); }
  .emp-pill-VOLUNTEER   { background: color-mix(in srgb, #3b82f6 12%, transparent); color: #2563eb; border: 1px solid color-mix(in srgb, #3b82f6 25%, transparent); }
  .emp-pill-GES_POSTED  { background: color-mix(in srgb, #8b5cf6 12%, transparent); color: #7c3aed; border: 1px solid color-mix(in srgb, #8b5cf6 25%, transparent); }

  /* Stat strip */
  .stat-strip {
    display: flex; align-items: center; flex-wrap: wrap;
    margin-top: 14px; padding-top: 14px;
    border-top: 1px solid var(--border-subtle);
  }
  .stat { display: flex; flex-direction: column; gap: 1px; padding: 0 16px 0 0; }
  .stat-label { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--tx-low); }
  .stat-val   { font-size: 13px; font-weight: 600; color: var(--tx-high); }
  .stat-active { color: #15803d; }
  .stat-inactive { color: var(--tx-low); }
  .stat-div { width: 1px; height: 24px; background: var(--border-subtle); margin: 0 16px 0 0; flex-shrink: 0; }

  /* ── Tab nav (pill style) ─────────────────────── */
  .tab-nav { display: flex; gap: 4px; flex-wrap: wrap; }
  .tn-item {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 7px 14px; border-radius: 8px;
    font-size: 13px; font-weight: 500;
    color: var(--tx-low); background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    cursor: pointer; transition: all 0.12s; white-space: nowrap;
  }
  .tn-item:hover { color: var(--tx-high); background: var(--surface-2); }
  .tn-item.tn-active {
    color: var(--accent); background: var(--accent-subtle);
    border-color: color-mix(in srgb, var(--accent) 25%, transparent);
  }
  .tn-count {
    background: var(--accent); color: var(--accent-fg, #fff);
    font-size: 10px; font-weight: 700;
    padding: 1px 6px; border-radius: 99px; min-width: 18px; text-align: center;
  }
  .tn-item:not(.tn-active) .tn-count { background: var(--surface-2); color: var(--tx-low); }

  /* ── Profile view (info-grid) ─────────────────── */
  .profile-card {
    background: var(--surface-1); border: 1px solid var(--border-subtle);
    border-radius: 12px; overflow: hidden; box-shadow: var(--shadow-xs);
  }
  .prof-section { padding: 20px 24px; }
  .prof-section-label {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--tx-low); margin: 0 0 16px;
  }
  .prof-divider { height: 1px; background: var(--border-subtle); }
  .prof-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px 24px;
  }
  @media (max-width: 680px) { .prof-grid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 400px) { .prof-grid { grid-template-columns: 1fr; } }
  .prof-field { display: flex; flex-direction: column; gap: 3px; }
  .pf-label { font-size: 10.5px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--tx-low); }
  .pf-val   { font-size: 13.5px; font-weight: 500; color: var(--tx-high); word-break: break-word; }
  .pf-mono  { font-family: "SF Mono", "Fira Code", monospace; font-size: 12.5px; }

  /* ── Back ───────────────────────────────────── */
  .back-btn {
    display: inline-flex; align-items: center; gap: 6px;
    background: none; border: none; cursor: pointer;
    color: var(--tx-low); font-size: 0.875rem;
    padding: 0; transition: color 0.12s;
  }
  .back-btn:hover { color: var(--tx-high); }

  /* (profile-header, tabs replaced by .hero + .tab-nav above) */

  /* ── Section cards ───────────────────────────── */
  .section-card {
    background: var(--surface-0);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    overflow: hidden;
  }

  .card-header {
    display: flex; align-items: center; gap: 10px;
    padding: 12px 18px;
    background: var(--surface-1);
    border-bottom: 1px solid var(--border-subtle);
  }

  .card-hicon {
    width: 28px; height: 28px; border-radius: 7px;
    background: var(--accent-subtle); color: var(--accent);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }

  .card-title {
    flex: 1;
    font-size: 0.875rem; font-weight: 600; color: var(--tx-high);
  }

  .card-actions { display: flex; gap: 8px; }

  .card-body {
    padding: 20px 24px;
    display: flex; flex-direction: column; gap: 16px;
  }

  .card-hint { margin: 0; font-size: 0.8125rem; color: var(--tx-low); }
  .hint { margin: 0; font-size: 0.8125rem; color: var(--tx-low); }

  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }

  /* ── Property sheet ──────────────────────────── */
  .prop-sheet {
    display: flex;
    flex-direction: column;
    margin: 0;
    padding: 0;
  }

  .prop-row {
    display: grid;
    grid-template-columns: 148px 1fr;
    gap: 12px;
    align-items: baseline;
    padding: 9px 0;
    border-bottom: 1px solid var(--border-subtle);
    transition: background 0.08s;
  }
  .prop-row:last-child { border-bottom: none; }
  .prop-row:hover {
    background: color-mix(in srgb, var(--surface-2) 60%, transparent);
    margin: 0 -8px;
    padding-left: 8px;
    padding-right: 8px;
    border-radius: 6px;
  }

  .prop-row dt {
    font-size: 0.6875rem;
    font-weight: 600;
    color: var(--tx-low);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .prop-row dd {
    margin: 0;
    font-size: 0.875rem;
    color: var(--tx-high);
    word-break: break-word;
  }

  .prop-row dd.mono { font-family: ui-monospace, monospace; font-size: 0.8125rem; }

  @media (max-width: 480px) {
    .prop-row { grid-template-columns: 1fr; gap: 2px; }
  }

  /* ── Inline badges ────────────────────────────── */
  .badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 9px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  .badge-accent  { background: var(--accent-subtle); color: var(--accent); border: 1px solid var(--accent-border); }
  .badge-neutral { background: var(--surface-2); color: var(--tx-mid); border: 1px solid var(--border-subtle); }
  .badge-green   { background: color-mix(in srgb, #10b981 12%, transparent); color: #059669; border: 1px solid color-mix(in srgb, #10b981 30%, transparent); }
  .badge-orange  { background: color-mix(in srgb, #f59e0b 12%, transparent); color: #d97706; border: 1px solid color-mix(in srgb, #f59e0b 30%, transparent); }
  .badge-blue    { background: color-mix(in srgb, #3b82f6 12%, transparent); color: #2563eb; border: 1px solid color-mix(in srgb, #3b82f6 30%, transparent); }
  .badge-purple  { background: color-mix(in srgb, #8b5cf6 12%, transparent); color: #7c3aed; border: 1px solid color-mix(in srgb, #8b5cf6 30%, transparent); }

  /* Employment / designation chips in profile header */
  .emp-chip,
  .desig-chip,
  .id-chip {
    display: inline-flex;
    align-items: center;
    padding: 2px 9px;
    border-radius: 99px;
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    white-space: nowrap;
  }
  .desig-chip {
    background: var(--surface-2);
    color: var(--tx-mid);
    border: 1px solid var(--border-subtle);
  }
  .id-chip {
    background: var(--surface-2);
    color: var(--tx-low);
    border: 1px solid var(--border-subtle);
    font-family: ui-monospace, monospace;
  }
  .emp-chip-PERMANENT { background: color-mix(in srgb, #10b981 12%, transparent); color: #059669; border: 1px solid color-mix(in srgb, #10b981 30%, transparent); }
  .emp-chip-CONTRACT  { background: color-mix(in srgb, #f59e0b 12%, transparent); color: #d97706; border: 1px solid color-mix(in srgb, #f59e0b 30%, transparent); }
  .emp-chip-VOLUNTEER { background: color-mix(in srgb, #3b82f6 12%, transparent); color: #2563eb; border: 1px solid color-mix(in srgb, #3b82f6 30%, transparent); }
  .emp-chip-GES_POSTED { background: color-mix(in srgb, #8b5cf6 12%, transparent); color: #7c3aed; border: 1px solid color-mix(in srgb, #8b5cf6 30%, transparent); }

  /* ── Sub table ───────────────────────────────── */
  .qual-table-wrap { overflow-x: auto; border-radius: 8px; border: 1px solid var(--border-subtle); }

  .sub-table {
    width: 100%; border-collapse: collapse; font-size: 0.875rem;
  }

  .sub-table th {
    text-align: left; padding: 9px 14px;
    font-size: 0.75rem; font-weight: 600; color: var(--tx-low);
    text-transform: uppercase; letter-spacing: 0.04em;
    background: var(--surface-1);
    border-bottom: 1px solid var(--border-subtle);
  }

  .sub-table td {
    padding: 11px 14px;
    border-bottom: 1px solid color-mix(in srgb, var(--border-subtle) 60%, transparent);
    color: var(--tx-high);
    vertical-align: middle;
  }
  .sub-table tr:last-child td { border-bottom: none; }

  .sub-table .bold { font-weight: 600; }
  .sub-table .text-muted { color: var(--tx-low); font-size: 0.8125rem; }

  .current-rank { background: color-mix(in srgb, var(--accent) 4%, transparent); }

  .current-pill {
    display: inline-block;
    padding: 2px 7px; border-radius: 10px;
    font-size: 0.7rem; font-weight: 600;
    background: color-mix(in srgb, var(--accent) 15%, transparent);
    color: var(--accent);
    margin-left: 8px;
  }

  .action-cell { text-align: right; width: 72px; white-space: nowrap; }
  .action-cell.row-edit-actions { width: 64px; }

  /* ── Row inline edit ─────────────────────────── */
  .edit-row td {
    background: color-mix(in srgb, var(--accent) 4%, var(--surface-0));
    padding-top: 8px; padding-bottom: 8px;
  }

  .row-edit-error {
    margin: 0 0 6px; font-size: 0.75rem; color: var(--err-text);
  }

  .prom-edit-fields {
    display: flex; gap: 8px;
  }
  .prom-edit-fields .input { min-width: 0; }
  .prom-edit-fields .input:last-child { max-width: 148px; flex-shrink: 0; }

  .save-btn { color: var(--accent) !important; }
  .save-btn:hover { background: color-mix(in srgb, var(--accent) 10%, transparent) !important; }

  .icon-btn {
    display: inline-flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 6px;
    background: none; border: none; cursor: pointer;
    color: var(--tx-low); transition: background 0.12s, color 0.12s;
  }
  .icon-btn:hover { background: var(--surface-1); color: var(--tx-mid); }
  .icon-btn.danger:hover { background: color-mix(in srgb, #ef4444 10%, transparent); color: #ef4444; }

  .empty-note { margin: 0; color: var(--tx-low); font-size: 0.875rem; padding: 8px 0; }

  /* ── Account status ──────────────────────────── */
  .account-status {
    display: flex; align-items: center; gap: 8px;
    padding: 12px 16px; border-radius: 8px;
    font-size: 0.875rem;
  }
  .account-status.warn {
    background: color-mix(in srgb, #f59e0b 8%, transparent);
    color: #d97706; border: 1px solid color-mix(in srgb, #f59e0b 25%, transparent);
  }

  /* ── Edit wrap ───────────────────────────────── */
  .edit-wrap { display: flex; flex-direction: column; gap: 14px; }

  .edit-toolbar {
    display: flex; align-items: center; justify-content: space-between;
  }

  .edit-title {
    font-size: 0.9375rem; font-weight: 700; color: var(--tx-high);
  }

  /* ── Edit layout ─────────────────────────────── */
  .edit-cols {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    align-items: start;
  }
  @media (max-width: 860px) { .edit-cols { grid-template-columns: 1fr; } }

  .edit-col { display: flex; flex-direction: column; gap: 16px; }

  .edit-card {
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    overflow: hidden;
  }

  .edit-card-head {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 16px;
    background: var(--surface-1);
    border-bottom: 1px solid var(--border-subtle);
    font-size: 0.8125rem; font-weight: 600; color: var(--tx-mid);
  }

  .edit-card-body {
    padding: 14px 16px;
    display: flex; flex-direction: column; gap: 12px;
  }

  .edit-divider { height: 1px; background: var(--border-subtle); }

  .edit-section-label {
    margin: 0; font-size: 0.75rem; font-weight: 600;
    color: var(--tx-low); text-transform: uppercase; letter-spacing: 0.06em;
  }

  .row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }

  @media (max-width: 600px) {
    .row-2, .row-3 { grid-template-columns: 1fr; }
  }

  /* ── Inline add form ─────────────────────────── */
  .inline-form {
    display: flex; flex-direction: column; gap: 10px;
    padding: 14px 16px;
    background: color-mix(in srgb, var(--accent) 4%, var(--surface-1));
    border: 1px solid color-mix(in srgb, var(--accent) 18%, var(--border-subtle));
    border-radius: 8px;
  }

  .inline-form-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    align-items: end;
  }

  .inline-form-row .field-year { max-width: 120px; }
  .inline-form-row .field-date { max-width: 180px; }

  @media (max-width: 640px) {
    .inline-form-row { grid-template-columns: 1fr; }
    .inline-form-row .field-year,
    .inline-form-row .field-date { max-width: none; }
  }

  .inline-form-actions {
    display: flex; gap: 8px; justify-content: flex-end;
  }

  .inline-form-error {
    margin: 0; font-size: 0.8125rem; color: var(--err-text);
  }

  /* ── Role preview ────────────────────────────── */
  .role-preview-row {
    display: flex; align-items: flex-start; gap: 7px;
    padding: 8px 10px; border-radius: 7px;
    background: color-mix(in srgb, var(--accent) 6%, var(--surface-1));
    border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
    font-size: 0.8125rem; color: var(--tx-mid); line-height: 1.4;
  }
  .role-preview-row :global(.role-preview-icon) { color: var(--accent); flex-shrink: 0; margin-top: 1px; }
  .role-preview-row :global(.role-preview-icon.warn) { color: var(--tx-low); }

  /* ── Form error ──────────────────────────────── */
  .form-error {
    margin: 0; padding: 9px 12px; border-radius: 8px;
    font-size: 0.8125rem; color: #ef4444;
    background: color-mix(in srgb, #ef4444 8%, transparent);
    border: 1px solid color-mix(in srgb, #ef4444 20%, transparent);
  }

  /* ── Invite panels ───────────────────────────── */
  .invite-sent-panel {
    display: flex; flex-direction: column; gap: 10px;
    padding: 14px 16px; border-radius: 10px;
    background: color-mix(in srgb, #10b981 6%, var(--surface-1));
    border: 1px solid color-mix(in srgb, #10b981 25%, transparent);
  }
  .invite-sent-header {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.9375rem; color: var(--tx-high);
  }
  .invite-sent-header :global(.invite-check) { color: #10b981; }

  .invite-link-row {
    display: flex; align-items: center; gap: 8px;
    background: var(--surface-0); border: 1px solid var(--border-subtle);
    border-radius: 7px; padding: 8px 10px;
  }
  .invite-link-text {
    flex: 1; font-size: 0.75rem; color: var(--tx-mid);
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-family: monospace;
  }

  .invite-pending-panel {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 12px; border-radius: 8px;
    background: color-mix(in srgb, var(--accent) 5%, var(--surface-1));
    border: 1px solid color-mix(in srgb, var(--accent) 15%, transparent);
    font-size: 0.875rem; color: var(--tx-mid);
  }
  .invite-pending-panel :global(.pending-spin) {
    color: var(--accent); flex-shrink: 0;
    animation: spin 1.2s linear infinite;
  }

  .icon-btn :global(.copy-ok) { color: #10b981; }

  /* ── Roles & permissions ─────────────────────── */
  .perms-loading {
    display: flex; align-items: center; gap: 8px;
    color: var(--tx-low); font-size: 0.875rem;
  }

  .roles-section {
    display: flex; flex-direction: column; gap: 10px;
    padding: 14px 16px;
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
  }

  .roles-header {
    display: flex; align-items: center; justify-content: space-between;
  }

  .roles-label {
    display: flex; align-items: center; gap: 6px;
    font-size: 0.8125rem; font-weight: 600; color: var(--tx-mid);
    text-transform: uppercase; letter-spacing: 0.05em;
  }

  .add-role-btn {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 4px 10px; border-radius: 6px;
    background: none; border: 1px solid var(--border-subtle);
    cursor: pointer; font-size: 0.8rem; color: var(--tx-mid);
    transition: background 0.12s, border-color 0.12s, color 0.12s;
  }
  .add-role-btn:hover {
    background: var(--surface-0);
    border-color: var(--accent);
    color: var(--accent);
  }

  .role-chips { display: flex; flex-wrap: wrap; gap: 6px; }

  .role-chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px; border-radius: 20px;
    background: color-mix(in srgb, var(--accent) 12%, transparent);
    color: var(--accent);
    border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
    font-size: 0.8125rem; font-weight: 600;
  }

  .chip-remove {
    display: inline-flex; align-items: center; justify-content: center;
    width: 16px; height: 16px; border-radius: 50%;
    background: none; border: none; cursor: pointer;
    color: inherit; opacity: 0.6;
    transition: opacity 0.12s, background 0.12s;
    padding: 0;
  }
  .chip-remove:hover { opacity: 1; background: color-mix(in srgb, var(--accent) 20%, transparent); }

  .no-roles {
    font-size: 0.8125rem; color: var(--tx-low); font-style: italic;
  }

  .add-role-row {
    display: flex; gap: 8px; align-items: center;
    padding-top: 4px;
  }
  .add-role-row .input { flex: 1; max-width: 280px; }

  .perms-section {
    display: flex; flex-direction: column; gap: 10px;
  }

  .perms-label {
    margin: 0;
    font-size: 0.75rem; font-weight: 600; color: var(--tx-low);
    text-transform: uppercase; letter-spacing: 0.05em;
  }

  .perms-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    gap: 4px 16px;
  }

  .perm-row {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.8125rem; padding: 3px 0;
  }

  .perm-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  }
  .perm-row.granted .perm-dot { background: #10b981; }
  .perm-row.denied .perm-dot { background: var(--border-subtle); }

  .perm-key {
    color: var(--tx-mid); text-transform: capitalize;
  }
  .perm-row.denied .perm-key { color: var(--tx-low); }

  /* ── Permission overrides ────────────────────────────────────── */
  .perms-section-header {
    display: flex; align-items: center; gap: 8px;
  }
  .perms-hint {
    margin: 0; font-size: 0.78rem; color: var(--tx-low); line-height: 1.4;
  }
  .perms-empty {
    margin: 0; font-size: 0.8125rem; color: var(--tx-low); font-style: italic;
  }
  .overrides-badge {
    font-size: 0.7rem; font-weight: 700; padding: 1px 7px;
    border-radius: 10px;
    background: color-mix(in srgb, #f59e0b 15%, transparent);
    color: #d97706;
    border: 1px solid color-mix(in srgb, #f59e0b 30%, transparent);
    min-width: 20px; text-align: center;
  }
  .perm-chips-wrap {
    display: flex; flex-wrap: wrap; gap: 5px;
  }
  .eff-chip {
    font-size: 0.72rem; padding: 3px 9px; border-radius: 10px;
    background: color-mix(in srgb, #10b981 12%, transparent);
    color: #059669;
    text-transform: capitalize;
    border: 1px solid color-mix(in srgb, #10b981 30%, transparent);
  }
  .eff-chip.overridden {
    background: color-mix(in srgb, #10b981 18%, transparent);
    border-color: color-mix(in srgb, #10b981 45%, transparent);
    font-weight: 600;
    box-shadow: 0 0 0 1px color-mix(in srgb, #10b981 50%, transparent) inset;
  }
  .perm-row2 {
    display: flex; align-items: center; gap: 8px;
    padding: 5px 0; font-size: 0.8125rem;
    border-top: 1px solid var(--border-subtle);
  }
  .perm-row2:first-of-type { border-top: none; }
  .perm-key2 {
    flex: 1; color: var(--tx-mid); text-transform: capitalize;
  }
  .perm-override-badge {
    font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: 10px;
  }
  .perm-override-badge.grant {
    background: color-mix(in srgb, #10b981 12%, transparent);
    color: #059669;
    border: 1px solid color-mix(in srgb, #10b981 30%, transparent);
  }
  .perm-override-badge.deny {
    background: color-mix(in srgb, #ef4444 10%, transparent);
    color: #dc2626;
    border: 1px solid color-mix(in srgb, #ef4444 25%, transparent);
  }
  .perm-clear-btn {
    font-size: 0.72rem; padding: 2px 8px;
    border: 1px solid var(--border-subtle); border-radius: 4px;
    background: transparent; color: var(--tx-low); cursor: pointer;
  }
  .perm-clear-btn:hover:not(:disabled) { background: var(--bg-subtle); }
  .perm-clear-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .add-override-btn {
    align-self: flex-start; font-size: 0.78rem; padding: 4px 10px;
    border: 1px dashed var(--border-subtle); border-radius: 6px;
    background: transparent; color: var(--tx-low); cursor: pointer;
  }
  .add-override-btn:hover { border-color: var(--accent); color: var(--accent); background: color-mix(in srgb, var(--accent) 6%, transparent); }
  .add-override-form {
    display: flex; flex-direction: column; gap: 8px;
    padding: 10px; background: var(--bg-subtle); border-radius: 6px; margin-top: 4px;
  }
  .input-sm { padding: 5px 8px; font-size: 0.8125rem; }
  .add-override-actions {
    display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  }
  .perm-act-btn {
    font-size: 0.72rem; padding: 3px 10px;
    border: 1px solid var(--border-subtle); border-radius: 4px;
    background: transparent; cursor: pointer; color: var(--tx-low);
  }
  .perm-act-btn.selected { font-weight: 600; }
  .perm-act-btn.grant.selected {
    border-color: #10b981;
    color: #059669;
    background: color-mix(in srgb, #10b981 12%, transparent);
  }
  .perm-act-btn.deny.selected {
    border-color: #ef4444;
    color: #dc2626;
    background: color-mix(in srgb, #ef4444 10%, transparent);
  }
  .perm-act-btn:hover:not(:disabled) { background: var(--surface-2); }
  .perm-act-btn.grant:hover:not(:disabled) { border-color: #10b981; color: #059669; }
  .perm-act-btn.deny:hover:not(:disabled)  { border-color: #ef4444; color: #dc2626; }

  /* ── Reset password ──────────────────────────────────────────── */
  .reset-pw-section {
    border-top: 1px solid var(--border-subtle);
    padding-top: 14px;
  }

  .reset-pw-row {
    display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;
  }

  .reset-pw-label {
    margin: 0 0 2px; font-size: 0.875rem; font-weight: 600; color: var(--tx-high);
  }

  .reset-pw-hint {
    margin: 0; font-size: 0.8rem; color: var(--tx-low); max-width: 380px;
  }

  :global(.spin) { animation: spin 0.75s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
