<script lang="ts">
  import { onMount } from "svelte";
  import { auth, currentUser } from "$stores/auth";
  import { schoolBranding } from "$stores/school";
  import { api } from "$api/client";
  import type { StaffMemberDetail, Qualification, Promotion } from "$api/types";
  import {
    Eye, EyeOff, Loader2, AlertCircle, CheckCircle2,
    Plus, Trash2, Pencil, X, Save, Camera,
    GraduationCap, Award, Shield, FileText, Paperclip,
    ExternalLink, User, BookOpen, TrendingUp,
  } from "@lucide/svelte";

  // ── Helpers ─────────────────────────────────────────────────────
  function fmtDate(iso: string | null | undefined): string {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("en-GH", {
      day: "numeric", month: "short", year: "numeric",
    });
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

  // ── Staff profile ────────────────────────────────────────────────
  let staff: StaffMemberDetail | null = null;
  let staffLoading = true;
  let hasStaff = false;

  onMount(async () => {
    try {
      const { data } = await api.get<StaffMemberDetail>("/auth/me/staff");
      staff = data;
      hasStaff = true;
    } catch {
      hasStaff = false;
    } finally {
      staffLoading = false;
    }
  });

  // ── Tabs ─────────────────────────────────────────────────────────
  type Tab = "personal" | "qualifications" | "promotions" | "security";
  let tab: Tab = "personal";

  // ── Personal edit ────────────────────────────────────────────────
  let editingPersonal = false;
  let personalForm = { gender: "", date_of_birth: "", phone: "", personal_email: "",
                       address: "", emergency_contact_name: "", emergency_contact_phone: "" };
  let personalSaving = false;
  let personalError = "";
  let personalSuccess = false;

  function startEditPersonal() {
    if (!staff) return;
    personalForm = {
      gender: staff.gender ?? "",
      date_of_birth: staff.date_of_birth ?? "",
      phone: staff.phone ?? "",
      personal_email: staff.personal_email ?? "",
      address: staff.address ?? "",
      emergency_contact_name: staff.emergency_contact_name ?? "",
      emergency_contact_phone: staff.emergency_contact_phone ?? "",
    };
    editingPersonal = true;
  }

  async function savePersonal() {
    personalError = ""; personalSaving = true;
    const payload: Record<string, string | null> = {};
    for (const [k, v] of Object.entries(personalForm)) payload[k] = v === "" ? null : v;
    try {
      const { data } = await api.patch<StaffMemberDetail>("/auth/me/staff", payload);
      staff = { ...staff!, ...data };
      auth.patchUser({ full_name: `${staff.first_name} ${staff.last_name}`.trim() });
      editingPersonal = false;
      personalSuccess = true;
      setTimeout(() => { personalSuccess = false; }, 4000);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      personalError = err?.response?.data?.detail ?? "Failed to save changes.";
    } finally { personalSaving = false; }
  }

  // ── Photo upload ─────────────────────────────────────────────────
  let photoUploading = false;
  let photoError = "";
  let fileInput: HTMLInputElement;

  async function handlePhotoChange(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    photoError = ""; photoUploading = true;
    const form = new FormData();
    form.append("file", file);
    try {
      const { data } = await api.post<StaffMemberDetail>("/auth/me/photo", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      staff = { ...staff!, photo_url: data.photo_url };
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      photoError = err?.response?.data?.detail ?? "Upload failed.";
    } finally { photoUploading = false; }
  }

  // ── Qualifications ───────────────────────────────────────────────
  let showAddQual = false;
  let qualForm = { degree: "", institution: "", year: "" };
  let qualSaving = false;
  let qualError = "";
  let editingQual: string | null = null;
  let editQualForm = { degree: "", institution: "", year: "" };

  async function addQualification() {
    qualError = ""; qualSaving = true;
    if (!qualForm.degree || !qualForm.institution) {
      qualError = "Degree and institution are required."; qualSaving = false; return;
    }
    try {
      const { data } = await api.post<Qualification>("/auth/me/qualifications", {
        degree: qualForm.degree,
        institution: qualForm.institution,
        year: qualForm.year ? parseInt(qualForm.year) : null,
      });
      staff = { ...staff!, qualifications: [...(staff?.qualifications ?? []), data] };
      qualForm = { degree: "", institution: "", year: "" };
      showAddQual = false;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      qualError = err?.response?.data?.detail ?? "Failed to add qualification.";
    } finally { qualSaving = false; }
  }

  function startEditQual(q: Qualification) {
    editingQual = q.id;
    editQualForm = { degree: q.degree, institution: q.institution, year: q.year?.toString() ?? "" };
  }

  async function saveQual(qualId: string) {
    qualError = ""; qualSaving = true;
    try {
      const { data } = await api.patch<Qualification>(`/auth/me/qualifications/${qualId}`, {
        degree: editQualForm.degree || undefined,
        institution: editQualForm.institution || undefined,
        year: editQualForm.year ? parseInt(editQualForm.year) : null,
      });
      staff = { ...staff!, qualifications: staff!.qualifications.map(q => q.id === qualId ? data : q) };
      editingQual = null;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      qualError = err?.response?.data?.detail ?? "Failed to update.";
    } finally { qualSaving = false; }
  }

  async function deleteQualification(qualId: string) {
    try {
      await api.delete(`/auth/me/qualifications/${qualId}`);
      staff = { ...staff!, qualifications: staff!.qualifications.filter(q => q.id !== qualId) };
    } catch { /* ignore */ }
  }

  // ── Promotions ───────────────────────────────────────────────────
  let showAddPromotion = false;
  let promForm = { rank: "", date_promoted: "" };
  let promSaving = false;
  let promError = "";
  let docUploading: Record<string, boolean> = {};
  let docError = "";
  let docInputs: Record<string, HTMLInputElement> = {};

  async function addPromotion() {
    promError = ""; promSaving = true;
    if (!promForm.rank || !promForm.date_promoted) {
      promError = "Rank and date are required."; promSaving = false; return;
    }
    try {
      const { data } = await api.post<Promotion>("/auth/me/promotions", {
        rank: promForm.rank, date_promoted: promForm.date_promoted,
      });
      staff = { ...staff!, promotions: [data, ...(staff?.promotions ?? [])] };
      promForm = { rank: "", date_promoted: "" };
      showAddPromotion = false;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      promError = err?.response?.data?.detail ?? "Failed to record promotion.";
    } finally { promSaving = false; }
  }

  async function deletePromotion(promId: string) {
    try {
      await api.delete(`/auth/me/promotions/${promId}`);
      staff = { ...staff!, promotions: staff!.promotions.filter(p => p.id !== promId) };
    } catch { /* ignore */ }
  }

  async function uploadPromotionDocument(promId: string, file: File) {
    docError = "";
    docUploading = { ...docUploading, [promId]: true };
    const form = new FormData();
    form.append("file", file);
    try {
      const { data } = await api.post<Promotion>(
        `/auth/me/promotions/${promId}/document`, form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      staff = { ...staff!, promotions: staff!.promotions.map(p => p.id === promId ? data : p) };
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      docError = err?.response?.data?.detail ?? "Upload failed.";
    } finally { docUploading = { ...docUploading, [promId]: false }; }
  }

  function handleDocChange(promId: string, e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) uploadPromotionDocument(promId, file);
  }

  // ── Password ─────────────────────────────────────────────────────
  let current = "", next = "", confirm = "";
  let showCurrent = false, showNext = false;
  let pwSaving = false, pwError = "", pwSuccess = false;

  async function changePassword() {
    pwError = ""; pwSuccess = false;
    if (!current || !next || !confirm) { pwError = "All fields are required."; return; }
    if (next.length < 8) { pwError = "New password must be at least 8 characters."; return; }
    if (next !== confirm) { pwError = "Passwords do not match."; return; }
    pwSaving = true;
    try {
      await api.post("/auth/change-password", { current_password: current, new_password: next });
      auth.patchUser({ must_change_password: false });
      current = ""; next = ""; confirm = "";
      pwSuccess = true;
      setTimeout(() => { pwSuccess = false; }, 5000);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      pwError = err?.response?.data?.detail ?? "Something went wrong.";
    } finally { pwSaving = false; }
  }

  $: strength = next.length === 0 ? 0 : next.length < 8 ? 1 : next.length < 12 ? 2
    : /[A-Z]/.test(next) && /[0-9]/.test(next) ? 4 : 3;
  $: strengthLabel = ["", "Too short", "Weak", "Good", "Strong"][strength];
  $: strengthColor = ["", "#ef4444", "#f59e0b", "#10b981", "#059669"][strength];

  $: displayName = staff
    ? `${staff.first_name} ${staff.last_name}`.trim()
    : ($currentUser?.full_name || $currentUser?.email?.split("@")[0] || "—");
  $: initials = displayName.split(" ").filter(Boolean)
    .map((w: string) => w[0]).join("").toUpperCase().slice(0, 2) || "?";
  $: roleLabel = $currentUser?.system_role?.replace(/_/g, " ") ?? "—";
</script>

<svelte:head><title>My Profile — {$schoolBranding?.name ?? 'TTEK-SMS'}</title></svelte:head>

<div class="profile-wrap">

  <!-- ── Hero ──────────────────────────────────────────────────── -->
  <div class="hero-card">
    <div class="banner" aria-hidden="true"></div>

    <div class="hero-body">
      <!-- Avatar -->
      <div class="avatar-col">
        <div class="avatar-ring">
          {#if staff?.photo_url}
            <img src={staff.photo_url} alt={displayName} class="avatar-img" />
          {:else}
            <div class="avatar-initials">{initials}</div>
          {/if}
          {#if hasStaff}
            <button
              class="photo-btn"
              on:click={() => fileInput.click()}
              title="Change photo"
              disabled={photoUploading}
              aria-label="Change profile photo"
            >
              {#if photoUploading}
                <Loader2 size={11} class="spin" />
              {:else}
                <Camera size={11} />
              {/if}
            </button>
            <input
              bind:this={fileInput}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              class="sr-only"
              on:change={handlePhotoChange}
            />
          {/if}
        </div>
        {#if photoError}
          <p class="photo-err">{photoError}</p>
        {/if}
      </div>

      <!-- Identity -->
      <div class="identity-col">
        <h1 class="hero-name">{displayName}</h1>
        <div class="hero-meta">
          <span class="role-chip">{roleLabel}</span>
          {#if staff?.designation}
            <span class="desig-chip">{humanise(staff.designation)}</span>
          {/if}
          {#if staff?.staff_id}
            <span class="id-chip">ID: {staff.staff_id}</span>
          {/if}
        </div>
        {#if staff?.current_rank}
          <p class="hero-rank">Current rank: <strong>{staff.current_rank}</strong></p>
        {/if}
      </div>
    </div>

    <!-- Tabs -->
    <nav class="tabs" aria-label="Profile sections">
      {#if hasStaff}
        <button class="tab" class:active={tab === "personal"}
          on:click={() => tab = "personal"}>
          <User size={13} />Personal
        </button>
        <button class="tab" class:active={tab === "qualifications"}
          on:click={() => tab = "qualifications"}>
          <BookOpen size={13} />Qualifications
        </button>
        <button class="tab" class:active={tab === "promotions"}
          on:click={() => tab = "promotions"}>
          <TrendingUp size={13} />Promotions
        </button>
      {/if}
      <button class="tab" class:active={tab === "security"}
        on:click={() => tab = "security"}>
        <Shield size={13} />Security
      </button>
    </nav>
  </div>

  <!-- ── Tab content ────────────────────────────────────────────── -->
  <div class="content-card">

    <!-- ─────────────── PERSONAL ─────────────────────────────────── -->
    {#if tab === "personal"}
      {#if staffLoading}
        <div class="loading-state">
          <Loader2 size={18} class="spin muted" />
          <span>Loading profile…</span>
        </div>
      {:else if !hasStaff}
        <div class="empty-state">
          <div class="empty-icon-wrap"><User size={24} /></div>
          <p class="empty-title">No staff profile linked</p>
          <p class="empty-body">Your account does not have a staff profile attached. Contact your administrator.</p>
        </div>
      {:else if staff}

        <!-- Personal section -->
        <div class="section">
          <div class="section-header">
            <h2 class="section-title">Personal information</h2>
            {#if !editingPersonal}
              <button class="btn-ghost" on:click={startEditPersonal}>
                <Pencil size={12} />Edit
              </button>
            {:else}
              <div class="btn-row">
                <button class="btn-ghost" on:click={() => { editingPersonal = false; personalError = ""; }}>
                  <X size={12} />Cancel
                </button>
                <button class="btn-primary" on:click={savePersonal} disabled={personalSaving}>
                  {#if personalSaving}<Loader2 size={12} class="spin" />{:else}<Save size={12} />{/if}
                  Save
                </button>
              </div>
            {/if}
          </div>

          {#if personalError}
            <div class="alert-bar err"><AlertCircle size={13} />{personalError}</div>
          {/if}
          {#if personalSuccess}
            <div class="alert-bar ok"><CheckCircle2 size={13} />Changes saved.</div>
          {/if}

          {#if !editingPersonal}
            <dl class="prop-sheet">
              <div class="prop-row">
                <dt>First name</dt>
                <dd>{staff.first_name}</dd>
              </div>
              {#if staff.middle_name}
                <div class="prop-row">
                  <dt>Middle name</dt>
                  <dd>{staff.middle_name}</dd>
                </div>
              {/if}
              <div class="prop-row">
                <dt>Last name</dt>
                <dd>{staff.last_name}</dd>
              </div>
              <div class="prop-row">
                <dt>Gender</dt>
                <dd>{humanise(staff.gender)}</dd>
              </div>
              <div class="prop-row">
                <dt>Date of birth</dt>
                <dd>{fmtDate(staff.date_of_birth)}</dd>
              </div>
              <div class="prop-row">
                <dt>Phone</dt>
                <dd>{staff.phone ?? "—"}</dd>
              </div>
              <div class="prop-row">
                <dt>Personal email</dt>
                <dd>{staff.personal_email ?? "—"}</dd>
              </div>
              <div class="prop-row">
                <dt>Address</dt>
                <dd>{staff.address ?? "—"}</dd>
              </div>
              <div class="prop-row">
                <dt>Emergency contact</dt>
                <dd>{staff.emergency_contact_name ?? "—"}</dd>
              </div>
              <div class="prop-row">
                <dt>Emergency phone</dt>
                <dd>{staff.emergency_contact_phone ?? "—"}</dd>
              </div>
            </dl>
          {:else}
            <div class="form-grid">
              <div class="field">
                <label for="gender">Gender</label>
                <select id="gender" class="input" bind:value={personalForm.gender}>
                  <option value="">— select —</option>
                  <option value="MALE">Male</option>
                  <option value="FEMALE">Female</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              <div class="field">
                <label for="dob">Date of birth</label>
                <input id="dob" class="input" type="date" bind:value={personalForm.date_of_birth} />
              </div>
              <div class="field">
                <label for="phone">Phone</label>
                <input id="phone" class="input" type="tel" bind:value={personalForm.phone} placeholder="+233 XX XXX XXXX" />
              </div>
              <div class="field">
                <label for="pemail">Personal email</label>
                <input id="pemail" class="input" type="email" bind:value={personalForm.personal_email} placeholder="you@personal.com" />
              </div>
              <div class="field span2">
                <label for="addr">Address</label>
                <input id="addr" class="input" type="text" bind:value={personalForm.address} placeholder="Home address" />
              </div>
              <div class="field">
                <label for="ecname">Emergency contact name</label>
                <input id="ecname" class="input" type="text" bind:value={personalForm.emergency_contact_name} placeholder="Full name" />
              </div>
              <div class="field">
                <label for="ecphone">Emergency contact phone</label>
                <input id="ecphone" class="input" type="tel" bind:value={personalForm.emergency_contact_phone} placeholder="+233 XX XXX XXXX" />
              </div>
            </div>
          {/if}
        </div>

        <!-- Employment section (read-only) -->
        <div class="section">
          <div class="section-header">
            <h2 class="section-title">Employment</h2>
            <span class="readonly-chip">Read only</span>
          </div>
          <dl class="prop-sheet">
            <div class="prop-row">
              <dt>Staff ID</dt>
              <dd>{staff.staff_id ?? "—"}</dd>
            </div>
            <div class="prop-row">
              <dt>Category</dt>
              <dd>
                <span class="badge {categoryClass(staff.category)}">{humanise(staff.category)}</span>
              </dd>
            </div>
            <div class="prop-row">
              <dt>Employment type</dt>
              <dd>
                <span class="badge {employmentClass(staff.employment_type)}">{humanise(staff.employment_type)}</span>
              </dd>
            </div>
            <div class="prop-row">
              <dt>Designation</dt>
              <dd>{humanise(staff.designation)}</dd>
            </div>
            <div class="prop-row">
              <dt>Date joined</dt>
              <dd>{fmtDate(staff.date_joined)}</dd>
            </div>
            <div class="prop-row">
              <dt>Current rank</dt>
              <dd>{staff.current_rank ?? "—"}</dd>
            </div>
          </dl>
        </div>
      {/if}

    <!-- ─────────────── QUALIFICATIONS ──────────────────────────── -->
    {:else if tab === "qualifications"}
      <div class="section">
        <div class="section-header">
          <h2 class="section-title">Academic qualifications</h2>
          <button class="btn-ghost" on:click={() => { showAddQual = !showAddQual; qualError = ""; }}>
            <Plus size={12} />Add
          </button>
        </div>

        {#if qualError}
          <div class="alert-bar err"><AlertCircle size={13} />{qualError}</div>
        {/if}

        {#if showAddQual}
          <div class="inline-form">
            <div class="form-grid">
              <div class="field span2">
                <label for="qdeg">Degree / Certificate *</label>
                <input id="qdeg" class="input" bind:value={qualForm.degree} placeholder="e.g. B.Ed. Basic Education" />
              </div>
              <div class="field">
                <label for="qinst">Institution *</label>
                <input id="qinst" class="input" bind:value={qualForm.institution} placeholder="e.g. University of Education" />
              </div>
              <div class="field">
                <label for="qyr">Year completed</label>
                <input id="qyr" class="input" type="number" bind:value={qualForm.year}
                  placeholder="e.g. 2018" min="1970" max={new Date().getFullYear()} />
              </div>
            </div>
            <div class="inline-foot">
              <button class="btn-ghost sm" on:click={() => { showAddQual = false; qualError = ""; }}>Cancel</button>
              <button class="btn-primary sm" on:click={addQualification} disabled={qualSaving}>
                {#if qualSaving}<Loader2 size={12} class="spin" />{/if} Save
              </button>
            </div>
          </div>
        {/if}

        {#if !staff?.qualifications?.length}
          <div class="empty-state">
            <div class="empty-icon-wrap"><GraduationCap size={24} /></div>
            <p class="empty-title">No qualifications on record</p>
            <p class="empty-body">Add your academic background — degrees, certificates, and diplomas — to build your professional profile.</p>
          </div>
        {:else}
          <div class="cred-list">
            {#each staff.qualifications as q (q.id)}
              {#if editingQual === q.id}
                <div class="cred-card editing">
                  <div class="form-grid">
                    <div class="field span2">
                      <label for="eq-deg-{q.id}">Degree / Certificate</label>
                      <input id="eq-deg-{q.id}" class="input" bind:value={editQualForm.degree} placeholder="Degree" />
                    </div>
                    <div class="field">
                      <label for="eq-inst-{q.id}">Institution</label>
                      <input id="eq-inst-{q.id}" class="input" bind:value={editQualForm.institution} placeholder="Institution" />
                    </div>
                    <div class="field">
                      <label for="eq-yr-{q.id}">Year</label>
                      <input id="eq-yr-{q.id}" class="input" type="number" bind:value={editQualForm.year} placeholder="Year" />
                    </div>
                  </div>
                  <div class="inline-foot">
                    <button class="btn-ghost sm" on:click={() => editingQual = null}><X size={12} />Cancel</button>
                    <button class="btn-primary sm" on:click={() => saveQual(q.id)} disabled={qualSaving}>
                      {#if qualSaving}<Loader2 size={12} class="spin" />{/if}<Save size={12} />Save
                    </button>
                  </div>
                </div>
              {:else}
                <div class="cred-card">
                  <div class="cred-icon"><GraduationCap size={15} /></div>
                  <div class="cred-body">
                    <span class="cred-degree">{q.degree}</span>
                    <span class="cred-meta">
                      {q.institution}{q.year ? ` · ${q.year}` : ""}
                    </span>
                  </div>
                  <div class="cred-actions">
                    <button class="icon-btn" on:click={() => startEditQual(q)} title="Edit">
                      <Pencil size={13} />
                    </button>
                    <button class="icon-btn danger" on:click={() => deleteQualification(q.id)} title="Remove">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              {/if}
            {/each}
          </div>
        {/if}
      </div>

    <!-- ─────────────── PROMOTIONS ──────────────────────────────── -->
    {:else if tab === "promotions"}
      <div class="section">
        <div class="section-header">
          <h2 class="section-title">Rank &amp; promotion history</h2>
          <button class="btn-ghost" on:click={() => { showAddPromotion = !showAddPromotion; promError = ""; }}>
            <Plus size={12} />Record
          </button>
        </div>

        {#if promError}
          <div class="alert-bar err"><AlertCircle size={13} />{promError}</div>
        {/if}
        {#if docError}
          <div class="alert-bar err"><AlertCircle size={13} />{docError}</div>
        {/if}

        {#if showAddPromotion}
          <div class="inline-form">
            <div class="form-grid">
              <div class="field">
                <label for="prank">New rank *</label>
                <input id="prank" class="input" bind:value={promForm.rank}
                  placeholder="e.g. Principal Superintendent" />
              </div>
              <div class="field">
                <label for="pdate">Date promoted *</label>
                <input id="pdate" class="input" type="date" bind:value={promForm.date_promoted} />
              </div>
            </div>
            <div class="inline-foot">
              <button class="btn-ghost sm" on:click={() => { showAddPromotion = false; promError = ""; }}>Cancel</button>
              <button class="btn-primary sm" on:click={addPromotion} disabled={promSaving}>
                {#if promSaving}<Loader2 size={12} class="spin" />{/if} Save
              </button>
            </div>
          </div>
        {/if}

        {#if !staff?.promotions?.length}
          <div class="empty-state">
            <div class="empty-icon-wrap"><Award size={24} /></div>
            <p class="empty-title">No promotions recorded</p>
            <p class="empty-body">Record your GES rank history here. Each entry can include the promotion letter as supporting evidence.</p>
          </div>
        {:else}
          <div class="timeline">
            {#each staff.promotions as p, i (p.id)}
              <div class="timeline-item">
                <div class="tl-gutter">
                  <div class="tl-dot" class:tl-dot-latest={i === 0}></div>
                  {#if i < staff.promotions.length - 1}
                    <div class="tl-line"></div>
                  {/if}
                </div>
                <div class="tl-body">
                  <div class="tl-head">
                    <span class="tl-rank">{p.rank}</span>
                    <span class="tl-year">{new Date(p.date_promoted).getFullYear()}</span>
                  </div>
                  <p class="tl-meta">
                    Effective {fmtDate(p.date_promoted)}
                    &nbsp;·&nbsp;
                    Recorded {fmtDate(p.date_recorded)}
                  </p>

                  <!-- Document attachment -->
                  <div class="tl-doc">
                    {#if p.document_url}
                      <a href={p.document_url} target="_blank" rel="noopener" class="doc-link">
                        <FileText size={12} />View letter
                        <ExternalLink size={10} class="doc-ext" />
                      </a>
                      <button
                        class="doc-replace"
                        on:click={() => docInputs[p.id]?.click()}
                        disabled={docUploading[p.id]}
                        title="Replace document"
                      >
                        {#if docUploading[p.id]}
                          <Loader2 size={11} class="spin" />
                        {:else}
                          Replace
                        {/if}
                      </button>
                    {:else}
                      <button
                        class="doc-attach"
                        on:click={() => docInputs[p.id]?.click()}
                        disabled={docUploading[p.id]}
                      >
                        {#if docUploading[p.id]}
                          <Loader2 size={11} class="spin" />Uploading…
                        {:else}
                          <Paperclip size={11} />Attach letter
                        {/if}
                      </button>
                    {/if}
                    <input
                      bind:this={docInputs[p.id]}
                      type="file"
                      accept="image/jpeg,image/png,image/webp,application/pdf"
                      class="sr-only"
                      on:change={(e) => handleDocChange(p.id, e)}
                    />
                  </div>
                </div>
                <button class="icon-btn danger tl-del" on:click={() => deletePromotion(p.id)} title="Remove">
                  <Trash2 size={13} />
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>

    <!-- ─────────────── SECURITY ─────────────────────────────────── -->
    {:else if tab === "security"}
      <div class="section">
        <div class="section-header">
          <h2 class="section-title">Change password</h2>
        </div>

        {#if pwError}
          <div class="alert-bar err"><AlertCircle size={13} />{pwError}</div>
        {/if}
        {#if pwSuccess}
          <div class="alert-bar ok"><CheckCircle2 size={13} />Password updated successfully.</div>
        {/if}

        <form on:submit|preventDefault={changePassword} novalidate class="pw-form">
          <div class="field">
            <label for="cur">Current password</label>
            <div class="pw-wrap">
              <input id="cur" class="input" type={showCurrent ? "text" : "password"}
                bind:value={current} autocomplete="current-password" placeholder="••••••••" />
              <button type="button" class="eye-btn" on:click={() => showCurrent = !showCurrent}
                aria-label={showCurrent ? "Hide" : "Show"}>
                {#if showCurrent}<EyeOff size={13} />{:else}<Eye size={13} />{/if}
              </button>
            </div>
          </div>

          <div class="form-grid">
            <div class="field">
              <label for="nxt">New password</label>
              <div class="pw-wrap">
                <input id="nxt" class="input" type={showNext ? "text" : "password"}
                  bind:value={next} autocomplete="new-password" placeholder="At least 8 characters" />
                <button type="button" class="eye-btn" on:click={() => showNext = !showNext}
                  aria-label={showNext ? "Hide" : "Show"}>
                  {#if showNext}<EyeOff size={13} />{:else}<Eye size={13} />{/if}
                </button>
              </div>
              {#if next.length > 0}
                <div class="strength-bar">
                  <div class="strength-fill" style="width:{strength * 25}%;background:{strengthColor}"></div>
                </div>
                <span class="strength-label" style="color:{strengthColor}">{strengthLabel}</span>
              {/if}
            </div>
            <div class="field">
              <label for="cfm">Confirm new password</label>
              <input id="cfm" class="input" type="password"
                bind:value={confirm} autocomplete="new-password" placeholder="••••••••" />
            </div>
          </div>

          <div class="form-foot">
            <button class="btn-primary" type="submit" disabled={pwSaving}>
              {#if pwSaving}<Loader2 size={13} class="spin" />{/if}
              Update password
            </button>
          </div>
        </form>
      </div>
    {/if}

  </div>
</div>

<style>
/* ── Layout ──────────────────────────────────────────────────────── */
.profile-wrap {
  max-width: 760px;
  display: flex;
  flex-direction: column;
}

/* ── Hero card ───────────────────────────────────────────────────── */
.hero-card {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-radius: 14px 14px 0 0;
  border-bottom: none;
  overflow: hidden;
}

.banner {
  height: 88px;
  background:
    repeating-linear-gradient(
      -45deg,
      color-mix(in srgb, var(--accent) 6%, transparent) 0px,
      color-mix(in srgb, var(--accent) 6%, transparent) 1px,
      transparent 1px,
      transparent 18px
    ),
    linear-gradient(
      135deg,
      color-mix(in srgb, var(--accent) 22%, var(--surface-2)) 0%,
      color-mix(in srgb, var(--accent) 6%, var(--surface-2)) 100%
    );
}

.hero-body {
  display: flex;
  align-items: flex-end;
  gap: 18px;
  padding: 0 28px 18px;
  margin-top: -44px;
}

/* Avatar */
.avatar-col { flex-shrink: 0; display: flex; flex-direction: column; align-items: center; }

.avatar-ring {
  position: relative;
  width: 80px;
  height: 80px;
}

.avatar-img,
.avatar-initials {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 3px solid var(--surface-1);
  box-shadow: 0 2px 10px rgba(0,0,0,0.12);
}

.avatar-img { object-fit: cover; display: block; }

.avatar-initials {
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.photo-btn {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--surface-0);
  border: 1.5px solid var(--border-subtle);
  color: var(--tx-low);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.12s, color 0.12s;
}
.photo-btn:hover:not(:disabled) { background: var(--accent-subtle); color: var(--accent); }
.photo-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.photo-err { font-size: 0.7rem; color: #ef4444; margin: 4px 0 0; text-align: center; }

/* Identity */
.identity-col {
  flex: 1;
  min-width: 0;
  padding-bottom: 4px;
}

.hero-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--tx-high);
  margin: 0 0 6px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.role-chip,
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

.role-chip {
  background: var(--accent-subtle);
  color: var(--accent);
  border: 1px solid var(--accent-border);
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

.hero-rank {
  margin: 6px 0 0;
  font-size: 0.75rem;
  color: var(--tx-low);
}
.hero-rank strong { color: var(--tx-mid); font-weight: 600; }

/* Responsive hero */
@media (max-width: 520px) {
  .hero-body { flex-direction: column; align-items: center; text-align: center; margin-top: -40px; }
  .hero-meta { justify-content: center; }
  .hero-rank { text-align: center; }
  .avatar-ring { width: 72px; height: 72px; }
  .avatar-img, .avatar-initials { width: 72px; height: 72px; }
}

/* ── Tabs ─────────────────────────────────────────────────────────── */
.tabs {
  display: flex;
  padding: 0 20px;
  border-top: 1px solid var(--border-subtle);
  gap: 2px;
  overflow-x: auto;
  scrollbar-width: none;
}
.tabs::-webkit-scrollbar { display: none; }

.tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--tx-low);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  white-space: nowrap;
  transition: color 0.12s, border-color 0.12s;
}
.tab :global(svg) { opacity: 0.6; }
.tab:hover { color: var(--tx-mid); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
.tab.active :global(svg) { opacity: 1; }

/* ── Content card ─────────────────────────────────────────────────── */
.content-card {
  background: var(--surface-1);
  border: 1px solid var(--border-subtle);
  border-top: none;
  border-radius: 0 0 14px 14px;
  min-height: 220px;
}

/* ── Section ──────────────────────────────────────────────────────── */
.section {
  padding: 22px 28px;
  border-bottom: 1px solid var(--border-subtle);
}
.section:last-child { border-bottom: none; }

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--tx-high);
  margin: 0;
}

.readonly-chip {
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--tx-low);
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  padding: 2px 8px;
  border-radius: 99px;
}

/* ── Property sheet ───────────────────────────────────────────────── */
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
.prop-row:hover { background: color-mix(in srgb, var(--surface-2) 60%, transparent); margin: 0 -8px; padding-left: 8px; padding-right: 8px; border-radius: 6px; }

.prop-row dt {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--tx-low);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.prop-row dd {
  font-size: 0.875rem;
  color: var(--tx-high);
  margin: 0;
}

@media (max-width: 480px) {
  .prop-row { grid-template-columns: 1fr; gap: 2px; }
}

/* ── Badges ───────────────────────────────────────────────────────── */
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

/* ── Credential cards ─────────────────────────────────────────────── */
.cred-list { display: flex; flex-direction: column; gap: 8px; }

.cred-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  background: var(--surface-0);
  border: 1px solid var(--border-subtle);
  border-left: 3px solid var(--accent);
  border-radius: 8px;
  transition: box-shadow 0.12s;
}
.cred-card:hover { box-shadow: var(--shadow-xs); }
.cred-card.editing { border-left-color: var(--border-strong); flex-direction: column; align-items: stretch; }

.cred-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: var(--accent-subtle);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.cred-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cred-degree {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--tx-high);
}

.cred-meta {
  font-size: 0.75rem;
  color: var(--tx-low);
}

.cred-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.12s;
}
.cred-card:hover .cred-actions,
.cred-card:focus-within .cred-actions { opacity: 1; }

/* ── Promotion timeline ───────────────────────────────────────────── */
.timeline { display: flex; flex-direction: column; }

.timeline-item {
  display: flex;
  gap: 0;
  position: relative;
}

.tl-gutter {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 28px;
  flex-shrink: 0;
  padding-top: 2px;
}

.tl-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--border-strong);
  border: 2px solid var(--surface-1);
  box-shadow: 0 0 0 2px var(--border-strong);
  flex-shrink: 0;
  z-index: 1;
  transition: background 0.12s, box-shadow 0.12s;
}

.tl-dot.tl-dot-latest {
  background: var(--accent);
  box-shadow: 0 0 0 2px var(--accent);
}

.tl-line {
  flex: 1;
  width: 2px;
  background: var(--border-subtle);
  margin: 4px 0;
  min-height: 20px;
}

.tl-body {
  flex: 1;
  min-width: 0;
  padding: 0 0 22px 14px;
}

.tl-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 3px;
}

.tl-rank {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--tx-high);
}

.tl-year {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--tx-low);
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  padding: 1px 7px;
  border-radius: 99px;
}

.tl-meta {
  font-size: 0.75rem;
  color: var(--tx-low);
  margin: 0 0 8px;
}

.tl-doc {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.doc-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--accent);
  text-decoration: none;
  padding: 3px 9px;
  border-radius: 6px;
  background: var(--accent-subtle);
  border: 1px solid var(--accent-border);
  transition: opacity 0.1s;
}
.doc-link:hover { opacity: 0.8; }
:global(.doc-ext) { opacity: 0.6; }

.doc-replace {
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--tx-low);
  background: none;
  border: none;
  cursor: pointer;
  padding: 3px 4px;
  text-decoration: underline;
  transition: color 0.1s;
}
.doc-replace:hover { color: var(--tx-mid); }

.doc-attach {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--tx-low);
  background: var(--surface-2);
  border: 1px dashed var(--border-strong);
  border-radius: 6px;
  padding: 3px 9px;
  cursor: pointer;
  transition: color 0.1s, border-color 0.1s, background 0.1s;
}
.doc-attach:hover:not(:disabled) {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--accent-subtle);
}
.doc-attach:disabled { opacity: 0.6; cursor: not-allowed; }

.tl-del {
  align-self: flex-start;
  margin-top: 0;
  opacity: 0;
  transition: opacity 0.12s;
}
.timeline-item:hover .tl-del { opacity: 1; }

/* ── Forms ────────────────────────────────────────────────────────── */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
@media (max-width: 520px) { .form-grid { grid-template-columns: 1fr; } }

.field { display: flex; flex-direction: column; gap: 4px; }
.field.span2 { grid-column: span 2; }
@media (max-width: 520px) { .field.span2 { grid-column: span 1; } }

.field label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--tx-mid);
}

.input {
  width: 100%;
  box-sizing: border-box;
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--border-strong);
  border-radius: 7px;
  font-size: 0.875rem;
  background: var(--surface-0);
  color: var(--tx-high);
  font-family: inherit;
  outline: none;
  transition: border-color 0.12s, box-shadow 0.12s;
}
.input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent);
}
.input::placeholder { color: var(--tx-placeholder, var(--tx-low)); opacity: 0.7; }
select.input { cursor: pointer; }

/* ── Inline form ──────────────────────────────────────────────────── */
.inline-form {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.inline-foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* ── Buttons ──────────────────────────────────────────────────────── */
.btn-primary {
  height: 32px;
  padding: 0 14px;
  border-radius: 7px;
  border: none;
  cursor: pointer;
  background: var(--accent);
  color: #fff;
  font-size: 0.8125rem;
  font-weight: 600;
  font-family: inherit;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: opacity 0.12s;
}
.btn-primary.sm { height: 28px; padding: 0 11px; font-size: 0.75rem; }
.btn-primary:hover:not(:disabled) { opacity: 0.88; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-ghost {
  height: 30px;
  padding: 0 11px;
  border-radius: 7px;
  border: 1px solid var(--border-strong);
  background: transparent;
  color: var(--tx-mid);
  cursor: pointer;
  font-size: 0.8125rem;
  font-weight: 500;
  font-family: inherit;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: background 0.12s, color 0.12s;
}
.btn-ghost.sm { height: 28px; font-size: 0.75rem; }
.btn-ghost:hover { background: var(--surface-2); color: var(--tx-high); }

.btn-row { display: flex; gap: 6px; }

.icon-btn {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--tx-low);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.12s, color 0.12s;
}
.icon-btn:hover { background: var(--surface-2); color: var(--tx-mid); }
.icon-btn.danger:hover {
  background: color-mix(in srgb, #ef4444 10%, transparent);
  color: #ef4444;
}

/* ── Alerts ───────────────────────────────────────────────────────── */
.alert-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 8px;
  font-size: 0.8125rem;
  margin-bottom: 14px;
}
.alert-bar.err {
  color: #ef4444;
  background: color-mix(in srgb, #ef4444 8%, transparent);
  border: 1px solid color-mix(in srgb, #ef4444 20%, transparent);
}
.alert-bar.ok {
  color: #059669;
  background: color-mix(in srgb, #10b981 10%, transparent);
  border: 1px solid color-mix(in srgb, #10b981 25%, transparent);
}

/* ── Empty states ─────────────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 40px 24px;
  gap: 8px;
}

.empty-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: var(--surface-2);
  color: var(--tx-low);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
  border: 1px solid var(--border-subtle);
}

.empty-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--tx-high);
  margin: 0;
}

.empty-body {
  font-size: 0.8125rem;
  color: var(--tx-low);
  line-height: 1.55;
  margin: 0;
  max-width: 360px;
}

/* ── Loading ──────────────────────────────────────────────────────── */
.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 36px 28px;
  font-size: 0.875rem;
  color: var(--tx-low);
}

/* ── Password form ────────────────────────────────────────────────── */
.pw-form { display: flex; flex-direction: column; gap: 16px; max-width: 500px; }

.pw-wrap { position: relative; }
.pw-wrap .input { padding-right: 36px; }

.eye-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--tx-low);
  padding: 0;
  display: flex;
  align-items: center;
  transition: color 0.1s;
}
.eye-btn:hover { color: var(--tx-mid); }

.strength-bar {
  height: 3px;
  background: var(--surface-2);
  border-radius: 99px;
  overflow: hidden;
  margin-top: 6px;
}
.strength-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.3s ease, background 0.3s ease;
}
.strength-label {
  font-size: 0.6875rem;
  font-weight: 500;
  margin-top: 3px;
  display: block;
}

.form-foot { display: flex; justify-content: flex-end; }

/* ── Utility ──────────────────────────────────────────────────────── */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  white-space: nowrap;
}

:global(.spin) { animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
