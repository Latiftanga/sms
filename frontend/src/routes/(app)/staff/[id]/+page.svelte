<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { api } from "$api/client";
  import { toast } from "$stores/toast";
  import Button from "$components/ui/Button.svelte";
  import Badge from "$components/ui/Badge.svelte";
  import Spinner from "$components/ui/Spinner.svelte";
  import Modal from "$components/ui/Modal.svelte";
  import {
    ArrowLeft, Pencil, Save, X, UserCheck, Upload,
    GraduationCap, TrendingUp, Shield, Plus, Trash2,
    Check, AlertCircle, Copy, Eye, EyeOff, Loader2, Camera,
  } from "@lucide/svelte";
  import type { StaffMemberDetail, Qualification, Promotion, AccountCreateResponse } from "$api/types";
  import { confirmDialog } from "$stores/confirm";

  const staffId = $page.params.id;

  // ── Data ──────────────────────────────────────────────────────────
  let member: StaffMemberDetail | null = null;
  let loading = true;
  let loadError = "";

  function apiError(e: unknown): string {
    const err = e as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail ?? "Something went wrong.";
  }

  async function load() {
    loading = true; loadError = "";
    try {
      const { data } = await api.get<StaffMemberDetail>(`/staff/${staffId}`);
      member = data;
    } catch (e) {
      loadError = apiError(e);
    } finally {
      loading = false;
    }
  }

  onMount(load);

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

  // ── Account creation ──────────────────────────────────────────────
  let showAccountModal = false;
  let accountEmail = "";
  let accountCreating = false;
  let accountError = "";
  let accountResult: AccountCreateResponse | null = null;
  let tempPwVisible = false;
  let copied = false;

  function openAccountModal() {
    accountEmail = member?.personal_email ?? "";
    accountError = ""; accountResult = null; tempPwVisible = false;
    showAccountModal = true;
  }

  async function createAccount() {
    if (!accountEmail) { accountError = "Email is required."; return; }
    accountCreating = true; accountError = "";
    try {
      const { data } = await api.post<AccountCreateResponse>(`/staff/${staffId}/account`, { email: accountEmail });
      accountResult = data;
      member = { ...member!, has_account: true };
      toast.success("Account created");
    } catch (e) {
      accountError = apiError(e);
    } finally {
      accountCreating = false;
    }
  }

  async function copyTempPw() {
    if (!accountResult) return;
    await navigator.clipboard.writeText(accountResult.temp_password);
    copied = true;
    setTimeout(() => copied = false, 2000);
  }

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
</script>

<svelte:head>
  <title>{member ? `${member.first_name} ${member.last_name}` : "Staff"} — TTEK-SIS</title>
</svelte:head>

<div class="page">
  {#if loading}
    <div class="centered"><Spinner /></div>
  {:else if loadError}
    <div class="centered">
      <AlertCircle size={20} />
      <p>{loadError}</p>
      <Button size="sm" on:click={load}>Retry</Button>
    </div>
  {:else if member}

    <!-- Back -->
    <button class="back-btn" on:click={() => goto("/staff")}>
      <ArrowLeft size={14} /> Staff
    </button>

    <!-- Header card -->
    <div class="profile-header">
      <!-- Photo -->
      <div class="photo-wrap">
        <div class="photo-avatar" style="background:{CATEGORY_COLORS[member.category] ?? 'var(--accent)'}">
          {#if member.photo_url}
            <img src={member.photo_url} alt={member.first_name} class="photo-img" />
          {:else}
            {initials(member)}
          {/if}
        </div>
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
      <div class="profile-meta">
        <h1 class="profile-name">{member.first_name} {member.middle_name ?? ""} {member.last_name}</h1>
        <div class="profile-badges">
          <Badge variant={member.is_active ? "ok" : "neutral"}>{member.is_active ? "Active" : "Inactive"}</Badge>
          <Badge variant="accent">{member.category}</Badge>
          <Badge variant="neutral">{member.employment_type}</Badge>
        </div>
        {#if member.current_rank}
          <p class="profile-rank">{member.current_rank}</p>
        {/if}
        {#if member.designation}
          <p class="profile-desig">{member.designation}</p>
        {/if}
      </div>

      <!-- Header actions -->
      <div class="header-actions">
        {#if !member.has_account}
          <Button variant="ghost" size="sm" on:click={openAccountModal}>
            <UserCheck size={13} /> Create Account
          </Button>
        {/if}
        {#if !editing}
          <Button size="sm" on:click={startEdit}>
            <Pencil size={13} /> Edit Profile
          </Button>
        {/if}
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button class="tab" class:active={tab === "profile"} on:click={() => tab = "profile"}>Profile</button>
      <button class="tab" class:active={tab === "qualifications"} on:click={() => tab = "qualifications"}>
        Qualifications <span class="tab-count">{member.qualifications.length}</span>
      </button>
      <button class="tab" class:active={tab === "promotions"} on:click={() => tab = "promotions"}>
        GES Rank History <span class="tab-count">{member.promotions.length}</span>
      </button>
      <button class="tab" class:active={tab === "account"} on:click={() => tab = "account"}>Account</button>
    </div>

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
                <div class="edit-card-head">Personal Information</div>
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
                <div class="edit-card-head">Contact Details</div>
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
                <div class="edit-card-head">Employment</div>
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
                <div class="edit-card-head">GES Details</div>
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
        <!-- View mode -->
        <div class="info-grid">
          <div class="section-card">
            <div class="card-title">Personal Information</div>
            <dl class="info-list">
              <dt>Full name</dt><dd>{member.first_name} {member.middle_name ?? ""} {member.last_name}</dd>
              <dt>Gender</dt><dd>{member.gender ?? "—"}</dd>
              <dt>Date of birth</dt><dd>{fmt(member.date_of_birth)}</dd>
              <dt>Phone</dt><dd>{member.phone ?? "—"}</dd>
              <dt>Personal email</dt><dd>{member.personal_email ?? "—"}</dd>
              <dt>Address</dt><dd>{member.address ?? "—"}</dd>
            </dl>
          </div>

          <div class="section-card">
            <div class="card-title">Employment</div>
            <dl class="info-list">
              <dt>Category</dt><dd>{member.category}</dd>
              <dt>Employment type</dt><dd>{member.employment_type}</dd>
              <dt>Designation</dt><dd>{member.designation ?? "—"}</dd>
              <dt>Date joined</dt><dd>{fmt(member.date_joined)}</dd>
              <dt>School staff ID</dt><dd class="mono">{member.staff_id ?? "—"}</dd>
            </dl>
          </div>

          <div class="section-card">
            <div class="card-title">GES Details</div>
            <dl class="info-list">
              <dt>GES staff ID</dt><dd class="mono">{member.ges_staff_id ?? "—"}</dd>
              <dt>Registered no.</dt><dd class="mono">{member.registered_no ?? "—"}</dd>
              <dt>Licence no.</dt><dd class="mono">{member.licence_no ?? "—"}</dd>
              <dt>SSNIT no.</dt><dd class="mono">{member.ssnit_no ?? "—"}</dd>
            </dl>
          </div>

          <div class="section-card">
            <div class="card-title">Emergency Contact</div>
            <dl class="info-list">
              <dt>Name</dt><dd>{member.emergency_contact_name ?? "—"}</dd>
              <dt>Phone</dt><dd>{member.emergency_contact_phone ?? "—"}</dd>
            </dl>
          </div>
        </div>
      {/if}

    <!-- ── Qualifications tab ─────────────────────────────────────── -->
    {:else if tab === "qualifications"}
      <div class="section-card">
        <div class="card-title">
          Academic Qualifications
          {#if !addingQual}
            <Button size="sm" on:click={openQualForm}><Plus size={13} /> Add</Button>
          {/if}
        </div>

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
                        <button class="icon-btn" on:click={() => startEditQual(q)} title="Edit"><Pencil size={13} /></button>
                        <button class="icon-btn danger" on:click={() => removeQual(q.id)} title="Remove"><Trash2 size={13} /></button>
                      </td>
                    </tr>
                  {/if}
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>

    <!-- ── Promotions / Rank history tab ─────────────────────────── -->
    {:else if tab === "promotions"}
      <div class="section-card">
        <div class="card-title">
          GES Rank History
          {#if !addingProm}
            <Button size="sm" on:click={openPromForm}><Plus size={13} /> Record Promotion</Button>
          {/if}
        </div>
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
                        <button class="icon-btn" on:click={() => startEditProm(p)} title="Edit"><Pencil size={13} /></button>
                        <button class="icon-btn danger" on:click={() => removeProm(p.id)} title="Remove"><Trash2 size={13} /></button>
                      </td>
                    </tr>
                  {/if}
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>

    <!-- ── Account tab ────────────────────────────────────────────── -->
    {:else if tab === "account"}
      <div class="section-card">
        <div class="card-title">Login Account</div>

        {#if member.has_account}
          <div class="account-status ok">
            <Check size={16} /> This staff member has an active login account.
          </div>
        {:else}
          <div class="account-status warn">
            <AlertCircle size={16} />
            No login account yet. Create one to give this staff member access to the system.
          </div>
          <Button on:click={openAccountModal}><UserCheck size={13} /> Create Account</Button>
        {/if}
      </div>
    {/if}

  {/if}
</div>

<!-- ── Account creation modal ────────────────────────────────────── -->
<Modal bind:open={showAccountModal} title="Create Login Account" noFooter>
  <div class="form">
    {#if !accountResult}
      {#if accountError}<p class="form-error">{accountError}</p>{/if}
      <p class="modal-hint">
        A temporary password will be generated. The staff member must change it on first login.
      </p>
      <div class="field">
        <label for="ac-email">Login email *</label>
        <input id="ac-email" class="input" type="email" bind:value={accountEmail} placeholder="staff@school.edu.gh" />
      </div>
      <div class="form-actions">
        <Button variant="ghost" on:click={() => showAccountModal = false}>Cancel</Button>
        <Button loading={accountCreating} on:click={createAccount}>Create Account</Button>
      </div>
    {:else}
      <div class="account-created">
        <div class="created-header">
          <Check size={24} class="created-check" />
          <strong>Account created!</strong>
        </div>
        <p class="created-sub">
          Share these credentials with <strong>{member?.first_name}</strong>.
          The password must be changed on first login.
        </p>
        <dl class="creds">
          <dt>Email</dt>
          <dd>{accountResult.email}</dd>
          <dt>Temporary password</dt>
          <dd class="pw-row">
            <span class="mono">{tempPwVisible ? accountResult.temp_password : "•".repeat(accountResult.temp_password.length)}</span>
            <button class="icon-btn" on:click={() => tempPwVisible = !tempPwVisible} title={tempPwVisible ? "Hide" : "Show"}>
              {#if tempPwVisible}<EyeOff size={13} />{:else}<Eye size={13} />{/if}
            </button>
            <button class="icon-btn" on:click={copyTempPw} title="Copy">
              {#if copied}<Check size={13} class="copy-ok" />{:else}<Copy size={13} />{/if}
            </button>
          </dd>
        </dl>
      </div>
      <div class="form-actions">
        <Button on:click={() => showAccountModal = false}>Done</Button>
      </div>
    {/if}
  </div>
</Modal>

<style>
  .page { display: flex; flex-direction: column; gap: 20px; }

  .centered {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 12px; padding: 80px 24px;
    color: var(--tx-low);
  }

  /* ── Back ───────────────────────────────────── */
  .back-btn {
    display: inline-flex; align-items: center; gap: 6px;
    background: none; border: none; cursor: pointer;
    color: var(--tx-low); font-size: 0.875rem;
    padding: 0; transition: color 0.12s;
  }
  .back-btn:hover { color: var(--tx-high); }

  /* ── Profile header ─────────────────────────── */
  .profile-header {
    display: flex; align-items: flex-start; gap: 20px;
    background: var(--surface-0);
    border: 1px solid var(--border-subtle);
    border-radius: 14px; padding: 24px;
  }

  .photo-wrap { position: relative; flex-shrink: 0; }

  .photo-avatar {
    width: 80px; height: 80px; border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; font-weight: 800; color: #fff;
    overflow: hidden;
  }

  .photo-img { width: 100%; height: 100%; object-fit: cover; }

  .photo-btn {
    position: absolute; bottom: -6px; right: -6px;
    width: 26px; height: 26px; border-radius: 50%;
    background: var(--surface-0); border: 2px solid var(--border-subtle);
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; color: var(--tx-mid);
    transition: background 0.12s, border-color 0.12s;
  }
  .photo-btn:hover { background: var(--surface-1); border-color: var(--accent); }

  .profile-meta { flex: 1; display: flex; flex-direction: column; gap: 6px; }

  .profile-name {
    margin: 0; font-size: 1.25rem; font-weight: 700; color: var(--tx-high);
  }

  .profile-badges { display: flex; gap: 6px; flex-wrap: wrap; }

  .profile-rank { margin: 0; font-size: 0.875rem; color: var(--tx-mid); font-weight: 500; }
  .profile-desig { margin: 0; font-size: 0.8rem; color: var(--tx-low); }

  .header-actions { display: flex; gap: 8px; align-items: flex-start; flex-shrink: 0; }

  /* ── Tabs ────────────────────────────────────── */
  .tabs {
    display: flex; gap: 2px;
    border-bottom: 1.5px solid var(--border-subtle);
  }

  .tab {
    padding: 8px 16px;
    background: none; border: none; cursor: pointer;
    font-size: 0.875rem; color: var(--tx-low);
    border-bottom: 2px solid transparent;
    margin-bottom: -1.5px;
    display: flex; align-items: center; gap: 6px;
    transition: color 0.12s, border-color 0.12s;
  }
  .tab:hover { color: var(--tx-mid); }
  .tab.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }

  .tab-count {
    padding: 1px 6px; border-radius: 10px;
    background: var(--surface-1);
    font-size: 0.7rem; font-weight: 600;
    color: var(--tx-low);
  }
  .tab.active .tab-count { background: color-mix(in srgb, var(--accent) 12%, transparent); color: var(--accent); }

  /* ── Section cards ───────────────────────────── */
  .section-card {
    background: var(--surface-0);
    border: 1px solid var(--border-subtle);
    border-radius: 12px; padding: 20px 24px;
    display: flex; flex-direction: column; gap: 16px;
  }

  .card-title {
    display: flex; align-items: center; justify-content: space-between;
    font-size: 0.9375rem; font-weight: 700; color: var(--tx-high);
  }
  .card-actions { display: flex; gap: 8px; }

  .card-hint { margin: -8px 0 0; font-size: 0.8125rem; color: var(--tx-low); }

  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }

  /* ── Info list ───────────────────────────────── */
  .info-list {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 8px 12px;
    margin: 0;
    font-size: 0.875rem;
  }

  .info-list dt { color: var(--tx-low); font-weight: 500; }
  .info-list dd { margin: 0; color: var(--tx-high); word-break: break-word; }
  .info-list dd.mono { font-family: monospace; font-size: 0.8125rem; }

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
  .account-status.ok {
    background: color-mix(in srgb, #10b981 8%, transparent);
    color: #10b981; border: 1px solid color-mix(in srgb, #10b981 25%, transparent);
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

  /* ── Form elements ───────────────────────────── */
  .form { display: flex; flex-direction: column; gap: 14px; }

  .form-error {
    margin: 0; padding: 9px 12px; border-radius: 8px;
    font-size: 0.8125rem; color: #ef4444;
    background: color-mix(in srgb, #ef4444 8%, transparent);
    border: 1px solid color-mix(in srgb, #ef4444 20%, transparent);
  }

  .form-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 4px; }

  .modal-hint { margin: 0; font-size: 0.875rem; color: var(--tx-low); }

  /* ── Account created ─────────────────────────── */
  .account-created { display: flex; flex-direction: column; gap: 12px; }

  .created-header {
    display: flex; align-items: center; gap: 10px;
    font-size: 1rem; color: var(--tx-high);
  }
  .created-header :global(.created-check) { color: #10b981; }

  .created-sub { margin: 0; font-size: 0.875rem; color: var(--tx-low); }

  .creds {
    display: grid; grid-template-columns: 120px 1fr;
    gap: 8px 12px; margin: 0;
    background: var(--surface-1); padding: 14px 16px;
    border-radius: 8px; border: 1px solid var(--border-subtle);
    font-size: 0.875rem;
  }
  .creds dt { color: var(--tx-low); font-weight: 500; }
  .creds dd { margin: 0; color: var(--tx-high); }

  .pw-row { display: flex; align-items: center; gap: 6px; }
  .pw-row .mono { font-family: monospace; letter-spacing: 0.04em; }

  .icon-btn :global(.copy-ok) { color: #10b981; }

  :global(.spin) { animation: spin 0.75s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
