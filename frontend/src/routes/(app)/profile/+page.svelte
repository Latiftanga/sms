<script lang="ts">
  import { onMount } from "svelte";
  import { auth, currentUser } from "$stores/auth";
  import { api } from "$api/client";
  import type { StaffMemberDetail, QualificationResponse, PromotionResponse } from "$api/types";
  import {
    Eye, EyeOff, Loader2, AlertCircle, CheckCircle2,
    Plus, Trash2, Pencil, X, Save, Upload, Camera,
  } from "@lucide/svelte";

  // ── Staff profile data ─────────────────────────────────────────
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

  // ── Tabs ────────────────────────────────────────────────────────
  type Tab = "personal" | "qualifications" | "promotions" | "security";
  let tab: Tab = "personal";

  // ── Personal info edit ─────────────────────────────────────────
  let editingPersonal = false;
  let personalForm = { gender: "", date_of_birth: "", phone: "", personal_email: "", address: "", emergency_contact_name: "", emergency_contact_phone: "" };
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
    for (const [k, v] of Object.entries(personalForm)) {
      payload[k] = v === "" ? null : v;
    }
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
    } finally {
      personalSaving = false;
    }
  }

  // ── Photo upload ───────────────────────────────────────────────
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
    } finally {
      photoUploading = false;
    }
  }

  // ── Qualifications ─────────────────────────────────────────────
  let showAddQual = false;
  let qualForm = { degree: "", institution: "", year: "" };
  let qualSaving = false;
  let qualError = "";
  let editingQual: string | null = null;
  let editQualForm = { degree: "", institution: "", year: "" };

  async function addQualification() {
    qualError = ""; qualSaving = true;
    if (!qualForm.degree || !qualForm.institution) { qualError = "Degree and institution are required."; qualSaving = false; return; }
    try {
      const { data } = await api.post<QualificationResponse>("/auth/me/qualifications", {
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
    } finally {
      qualSaving = false;
    }
  }

  function startEditQual(q: QualificationResponse) {
    editingQual = q.id;
    editQualForm = { degree: q.degree, institution: q.institution, year: q.year?.toString() ?? "" };
  }

  async function saveQual(qualId: string) {
    qualError = ""; qualSaving = true;
    try {
      const { data } = await api.patch<QualificationResponse>(`/auth/me/qualifications/${qualId}`, {
        degree: editQualForm.degree || undefined,
        institution: editQualForm.institution || undefined,
        year: editQualForm.year ? parseInt(editQualForm.year) : null,
      });
      staff = { ...staff!, qualifications: staff!.qualifications.map(q => q.id === qualId ? data : q) };
      editingQual = null;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      qualError = err?.response?.data?.detail ?? "Failed to update.";
    } finally {
      qualSaving = false;
    }
  }

  async function deleteQualification(qualId: string) {
    try {
      await api.delete(`/auth/me/qualifications/${qualId}`);
      staff = { ...staff!, qualifications: staff!.qualifications.filter(q => q.id !== qualId) };
    } catch { /* ignore */ }
  }

  // ── Promotions ─────────────────────────────────────────────────
  let showAddPromotion = false;
  let promForm = { rank: "", date_promoted: "" };
  let promSaving = false;
  let promError = "";

  async function addPromotion() {
    promError = ""; promSaving = true;
    if (!promForm.rank || !promForm.date_promoted) { promError = "Rank and date are required."; promSaving = false; return; }
    try {
      const { data } = await api.post<PromotionResponse>("/auth/me/promotions", {
        rank: promForm.rank,
        date_promoted: promForm.date_promoted,
      });
      staff = { ...staff!, promotions: [data, ...(staff?.promotions ?? [])] };
      promForm = { rank: "", date_promoted: "" };
      showAddPromotion = false;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      promError = err?.response?.data?.detail ?? "Failed to record promotion.";
    } finally {
      promSaving = false;
    }
  }

  async function deletePromotion(promId: string) {
    try {
      await api.delete(`/auth/me/promotions/${promId}`);
      staff = { ...staff!, promotions: staff!.promotions.filter(p => p.id !== promId) };
    } catch { /* ignore */ }
  }

  // ── Change password ────────────────────────────────────────────
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
    } finally {
      pwSaving = false;
    }
  }

  $: strength = next.length === 0 ? 0 : next.length < 8 ? 1 : next.length < 12 ? 2 : /[A-Z]/.test(next) && /[0-9]/.test(next) ? 4 : 3;
  $: strengthLabel = ["", "Too short", "Weak", "Good", "Strong"][strength];
  $: strengthColor = ["", "#ef4444", "#f59e0b", "#10b981", "#059669"][strength];

  $: displayName = staff ? `${staff.first_name} ${staff.last_name}`.trim() : ($currentUser?.full_name || $currentUser?.email?.split("@")[0] || "—");
  $: initials = displayName.split(" ").filter(Boolean).map((w: string) => w[0]).join("").toUpperCase().slice(0, 2) || "?";
  $: roleLabel = $currentUser?.system_role?.replace(/_/g, " ") ?? "—";
</script>

<svelte:head><title>My Profile — TTEK-SIS</title></svelte:head>

<div class="page">

  <!-- ── Hero ── -->
  <div class="hero-card">
    <div class="banner"></div>
    <div class="hero-body">
      <!-- Avatar with upload overlay -->
      <div class="avatar-wrap">
        {#if staff?.photo_url}
          <img src={staff.photo_url} alt={displayName} class="avatar-img" />
        {:else}
          <div class="avatar-initials">{initials}</div>
        {/if}
        {#if hasStaff}
          <button class="avatar-upload-btn" on:click={() => fileInput.click()} title="Change photo" disabled={photoUploading}>
            {#if photoUploading}<Loader2 size={12} class="spin" />{:else}<Camera size={12} />{/if}
          </button>
          <input bind:this={fileInput} type="file" accept="image/jpeg,image/png,image/webp" class="sr-only" on:change={handlePhotoChange} />
        {/if}
      </div>
      {#if photoError}<p class="photo-error">{photoError}</p>{/if}
      <h1 class="hero-name">{displayName}</h1>
      <span class="hero-badge">{roleLabel}</span>
      {#if staff?.designation}
        <span class="hero-sub">{staff.designation.replace(/_/g, " ")}</span>
      {/if}
    </div>

    <!-- Tabs -->
    <nav class="tabs">
      {#if hasStaff}
        <button class="tab" class:active={tab === "personal"} on:click={() => tab = "personal"}>Personal</button>
        <button class="tab" class:active={tab === "qualifications"} on:click={() => tab = "qualifications"}>Qualifications</button>
        <button class="tab" class:active={tab === "promotions"} on:click={() => tab = "promotions"}>Promotions</button>
      {/if}
      <button class="tab" class:active={tab === "security"} on:click={() => tab = "security"}>Security</button>
    </nav>
  </div>

  <!-- ── Tab content ── -->
  <div class="tab-content">

    <!-- ── Personal ── -->
    {#if tab === "personal"}
      {#if staffLoading}
        <div class="center-state"><Loader2 size={20} class="spin muted" /> Loading profile…</div>
      {:else if !hasStaff}
        <div class="center-state muted">No staff profile linked to this account.</div>
      {:else if staff}
        <div class="section-bar">
          <span class="section-title">Personal information</span>
          {#if !editingPersonal}
            <button class="btn-ghost" on:click={startEditPersonal}><Pencil size={13} /> Edit</button>
          {:else}
            <div class="btn-group">
              <button class="btn-ghost" on:click={() => { editingPersonal = false; personalError = ""; }}><X size={13} /> Cancel</button>
              <button class="btn-primary" on:click={savePersonal} disabled={personalSaving}>
                {#if personalSaving}<Loader2 size={13} class="spin" />{:else}<Save size={13} />{/if} Save
              </button>
            </div>
          {/if}
        </div>

        {#if personalError}<div class="alert err"><AlertCircle size={13} />{personalError}</div>{/if}
        {#if personalSuccess}<div class="alert ok"><CheckCircle2 size={13} />Saved successfully.</div>{/if}

        {#if !editingPersonal}
          <!-- Read mode -->
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">First name</span>
              <span class="info-val">{staff.first_name}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Last name</span>
              <span class="info-val">{staff.last_name}</span>
            </div>
            {#if staff.middle_name}
              <div class="info-item">
                <span class="info-label">Middle name</span>
                <span class="info-val">{staff.middle_name}</span>
              </div>
            {/if}
            <div class="info-item">
              <span class="info-label">Gender</span>
              <span class="info-val">{staff.gender ?? "—"}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Date of birth</span>
              <span class="info-val">{staff.date_of_birth ?? "—"}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Phone</span>
              <span class="info-val">{staff.phone ?? "—"}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Personal email</span>
              <span class="info-val">{staff.personal_email ?? "—"}</span>
            </div>
            <div class="info-item full">
              <span class="info-label">Address</span>
              <span class="info-val">{staff.address ?? "—"}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Emergency contact</span>
              <span class="info-val">{staff.emergency_contact_name ?? "—"}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Emergency phone</span>
              <span class="info-val">{staff.emergency_contact_phone ?? "—"}</span>
            </div>
          </div>
        {:else}
          <!-- Edit mode -->
          <div class="form-grid">
            <div class="field">
              <label>Gender</label>
              <select class="input" bind:value={personalForm.gender}>
                <option value="">— select —</option>
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
            <div class="field">
              <label>Date of birth</label>
              <input class="input" type="date" bind:value={personalForm.date_of_birth} />
            </div>
            <div class="field">
              <label>Phone</label>
              <input class="input" type="tel" bind:value={personalForm.phone} placeholder="+233 XX XXX XXXX" />
            </div>
            <div class="field">
              <label>Personal email</label>
              <input class="input" type="email" bind:value={personalForm.personal_email} placeholder="you@personal.com" />
            </div>
            <div class="field full">
              <label>Address</label>
              <input class="input" type="text" bind:value={personalForm.address} placeholder="Your home address" />
            </div>
            <div class="field">
              <label>Emergency contact name</label>
              <input class="input" type="text" bind:value={personalForm.emergency_contact_name} placeholder="Full name" />
            </div>
            <div class="field">
              <label>Emergency contact phone</label>
              <input class="input" type="tel" bind:value={personalForm.emergency_contact_phone} placeholder="+233 XX XXX XXXX" />
            </div>
          </div>
        {/if}

        <!-- Employment info (read-only) -->
        <div class="section-bar" style="margin-top:20px">
          <span class="section-title">Employment</span>
          <span class="badge-readonly">Read only</span>
        </div>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Staff ID</span>
            <span class="info-val">{staff.staff_id ?? "—"}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Category</span>
            <span class="info-val">{staff.category}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Employment type</span>
            <span class="info-val">{staff.employment_type.replace(/_/g, " ")}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Designation</span>
            <span class="info-val">{staff.designation?.replace(/_/g, " ") ?? "—"}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Date joined</span>
            <span class="info-val">{staff.date_joined ?? "—"}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Current rank</span>
            <span class="info-val">{staff.current_rank ?? "—"}</span>
          </div>
        </div>
      {/if}

    <!-- ── Qualifications ── -->
    {:else if tab === "qualifications"}
      <div class="section-bar">
        <span class="section-title">Academic qualifications</span>
        <button class="btn-ghost" on:click={() => { showAddQual = !showAddQual; qualError = ""; }}>
          <Plus size={13} /> Add
        </button>
      </div>

      {#if qualError}<div class="alert err"><AlertCircle size={13} />{qualError}</div>{/if}

      {#if showAddQual}
        <div class="inline-form">
          <div class="form-grid">
            <div class="field">
              <label>Degree / Certificate</label>
              <input class="input" bind:value={qualForm.degree} placeholder="e.g. B.Ed. Basic Education" />
            </div>
            <div class="field">
              <label>Institution</label>
              <input class="input" bind:value={qualForm.institution} placeholder="e.g. University of Education" />
            </div>
            <div class="field">
              <label>Year completed</label>
              <input class="input" type="number" bind:value={qualForm.year} placeholder="e.g. 2018" min="1970" max={new Date().getFullYear()} />
            </div>
          </div>
          <div class="inline-form-foot">
            <button class="btn-ghost sm" on:click={() => { showAddQual = false; qualError = ""; }}>Cancel</button>
            <button class="btn-primary sm" on:click={addQualification} disabled={qualSaving}>
              {#if qualSaving}<Loader2 size={12} class="spin" />{/if} Save
            </button>
          </div>
        </div>
      {/if}

      {#if !staff?.qualifications?.length}
        <p class="empty-hint">No qualifications recorded. Add your academic background above.</p>
      {:else}
        <div class="list">
          {#each staff.qualifications as q (q.id)}
            <div class="list-row">
              {#if editingQual === q.id}
                <div class="list-edit-grid">
                  <input class="input sm" bind:value={editQualForm.degree} placeholder="Degree" />
                  <input class="input sm" bind:value={editQualForm.institution} placeholder="Institution" />
                  <input class="input sm" type="number" bind:value={editQualForm.year} placeholder="Year" />
                  <div class="list-edit-actions">
                    <button class="icon-btn" on:click={() => saveQual(q.id)} title="Save"><Save size={13} /></button>
                    <button class="icon-btn muted" on:click={() => editingQual = null} title="Cancel"><X size={13} /></button>
                  </div>
                </div>
              {:else}
                <div class="list-body">
                  <span class="list-primary">{q.degree}</span>
                  <span class="list-secondary">{q.institution}{q.year ? ` · ${q.year}` : ""}</span>
                </div>
                <div class="list-actions">
                  <button class="icon-btn muted" on:click={() => startEditQual(q)} title="Edit"><Pencil size={13} /></button>
                  <button class="icon-btn danger" on:click={() => deleteQualification(q.id)} title="Remove"><Trash2 size={13} /></button>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}

    <!-- ── Promotions ── -->
    {:else if tab === "promotions"}
      <div class="section-bar">
        <span class="section-title">Rank / promotion history</span>
        <button class="btn-ghost" on:click={() => { showAddPromotion = !showAddPromotion; promError = ""; }}>
          <Plus size={13} /> Record
        </button>
      </div>

      {#if promError}<div class="alert err"><AlertCircle size={13} />{promError}</div>{/if}

      {#if showAddPromotion}
        <div class="inline-form">
          <div class="form-grid">
            <div class="field">
              <label>New rank</label>
              <input class="input" bind:value={promForm.rank} placeholder="e.g. Principal Superintendent" />
            </div>
            <div class="field">
              <label>Date promoted</label>
              <input class="input" type="date" bind:value={promForm.date_promoted} />
            </div>
          </div>
          <div class="inline-form-foot">
            <button class="btn-ghost sm" on:click={() => { showAddPromotion = false; promError = ""; }}>Cancel</button>
            <button class="btn-primary sm" on:click={addPromotion} disabled={promSaving}>
              {#if promSaving}<Loader2 size={12} class="spin" />{/if} Save
            </button>
          </div>
        </div>
      {/if}

      {#if !staff?.promotions?.length}
        <p class="empty-hint">No promotion records. Add your rank history above.</p>
      {:else}
        <div class="list">
          {#each staff.promotions as p (p.id)}
            <div class="list-row">
              <div class="list-body">
                <span class="list-primary">{p.rank}</span>
                <span class="list-secondary">Effective {p.date_promoted} · Recorded {p.date_recorded}</span>
              </div>
              <div class="list-actions">
                <button class="icon-btn danger" on:click={() => deletePromotion(p.id)} title="Remove"><Trash2 size={13} /></button>
              </div>
            </div>
          {/each}
        </div>
      {/if}

    <!-- ── Security ── -->
    {:else if tab === "security"}
      <div class="section-bar">
        <span class="section-title">Change password</span>
      </div>

      {#if pwError}<div class="alert err"><AlertCircle size={13} />{pwError}</div>{/if}
      {#if pwSuccess}<div class="alert ok"><CheckCircle2 size={13} />Password updated successfully.</div>{/if}

      <form on:submit|preventDefault={changePassword} novalidate class="pw-form">
        <div class="field">
          <label for="cur">Current password</label>
          <div class="pw-wrap">
            <input id="cur" class="input" type={showCurrent ? "text" : "password"}
              bind:value={current} autocomplete="current-password" placeholder="••••••••" />
            <button type="button" class="eye" on:click={() => showCurrent = !showCurrent}>
              {#if showCurrent}<EyeOff size={13} />{:else}<Eye size={13} />{/if}
            </button>
          </div>
        </div>
        <div class="pw-row">
          <div class="field">
            <label for="nxt">New password</label>
            <div class="pw-wrap">
              <input id="nxt" class="input" type={showNext ? "text" : "password"}
                bind:value={next} autocomplete="new-password" placeholder="At least 8 characters" />
              <button type="button" class="eye" on:click={() => showNext = !showNext}>
                {#if showNext}<EyeOff size={13} />{:else}<Eye size={13} />{/if}
              </button>
            </div>
            {#if next.length > 0}
              <div class="bar"><div class="bar-fill" style="width:{strength*25}%;background:{strengthColor}"></div></div>
              <span class="bar-label" style="color:{strengthColor}">{strengthLabel}</span>
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
            {#if pwSaving}<Loader2 size={13} class="spin" />{/if} Update password
          </button>
        </div>
      </form>
    {/if}

  </div>
</div>

<style>
  .page { max-width: 720px; display: flex; flex-direction: column; gap: 0; }

  /* ── Hero card ── */
  .hero-card {
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    border-radius: 14px 14px 0 0;
    border-bottom: none;
    overflow: hidden;
  }

  .banner {
    height: 72px;
    background: linear-gradient(
      135deg,
      color-mix(in srgb, var(--accent) 25%, var(--surface-1)) 0%,
      color-mix(in srgb, var(--accent) 8%, var(--surface-1)) 100%
    );
  }

  .hero-body {
    padding: 0 24px 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-top: -34px;
  }

  .avatar-wrap {
    position: relative;
    width: 68px;
    height: 68px;
    flex-shrink: 0;
  }

  .avatar-img, .avatar-initials {
    width: 68px; height: 68px; border-radius: 50%;
    border: 3px solid var(--surface-1);
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }

  .avatar-img { object-fit: cover; display: block; }

  .avatar-initials {
    background: var(--accent); color: #fff;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.375rem; font-weight: 700; letter-spacing: -0.5px;
  }

  .avatar-upload-btn {
    position: absolute; bottom: 0; right: 0;
    width: 24px; height: 24px; border-radius: 50%;
    background: var(--surface-0); border: 1.5px solid var(--border-subtle);
    color: var(--tx-mid); cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.12s;
  }
  .avatar-upload-btn:hover { background: var(--accent-subtle); color: var(--accent); }

  .photo-error {
    font-size: 0.75rem; color: #ef4444; margin: 4px 0 0; text-align: center;
  }

  .sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }

  .hero-name {
    margin: 10px 0 0;
    font-size: 1.0625rem; font-weight: 700; color: var(--tx-high); line-height: 1.2;
  }

  .hero-badge {
    margin-top: 5px; display: inline-block;
    padding: 2px 9px; border-radius: 99px;
    font-size: 0.6875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    background: var(--accent-subtle); color: var(--accent); border: 1px solid var(--accent-border);
  }

  .hero-sub {
    margin-top: 3px; font-size: 0.75rem; color: var(--tx-low);
    text-transform: capitalize;
  }

  /* ── Tabs ── */
  .tabs {
    display: flex; gap: 0;
    padding: 14px 24px 0;
    border-top: 1px solid var(--border-subtle);
    margin-top: 14px;
    overflow-x: auto;
    scrollbar-width: none;
  }
  .tabs::-webkit-scrollbar { display: none; }

  .tab {
    padding: 8px 14px;
    background: none; border: none; cursor: pointer;
    font-size: 0.8125rem; font-weight: 500; color: var(--tx-low);
    border-bottom: 2px solid transparent;
    white-space: nowrap;
    transition: color 0.12s, border-color 0.12s;
    margin-bottom: -1px;
  }
  .tab:hover { color: var(--tx-mid); }
  .tab.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }

  /* ── Tab content panel ── */
  .tab-content {
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    border-top: none;
    border-radius: 0 0 14px 14px;
    padding: 20px 24px 24px;
    min-height: 200px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  /* ── Section bar ── */
  .section-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border-subtle);
  }

  .section-title { font-size: 0.8125rem; font-weight: 600; color: var(--tx-high); }

  .badge-readonly {
    font-size: 0.6875rem; font-weight: 500; color: var(--tx-low);
    background: var(--surface-2); border: 1px solid var(--border-subtle);
    padding: 2px 7px; border-radius: 99px;
  }

  .btn-group { display: flex; gap: 6px; }

  /* ── Info grid (read view) ── */
  .info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
  }
  @media (max-width: 480px) { .info-grid { grid-template-columns: 1fr; } }

  .info-item {
    display: flex; flex-direction: column; gap: 2px;
    padding: 10px 0;
    border-bottom: 1px solid var(--border-subtle);
    padding-right: 16px;
  }
  .info-item.full { grid-column: span 2; }

  .info-label { font-size: 0.6875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; color: var(--tx-low); }
  .info-val   { font-size: 0.875rem; color: var(--tx-high); }

  /* ── Form grid (edit view) ── */
  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  @media (max-width: 480px) { .form-grid { grid-template-columns: 1fr; } }

  .field { display: flex; flex-direction: column; gap: 4px; }
  .field.full { grid-column: span 2; }
  .field label { font-size: 0.75rem; font-weight: 500; color: var(--tx-mid); }

  .input {
    width: 100%; box-sizing: border-box;
    height: 34px; padding: 0 10px;
    border: 1px solid var(--border-strong); border-radius: 7px;
    font-size: 0.875rem; background: var(--surface-0); color: var(--tx-high);
    font-family: inherit; outline: none;
    transition: border-color 0.12s, box-shadow 0.12s;
  }
  .input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 13%, transparent);
  }
  .input::placeholder { color: var(--tx-placeholder); }
  .input.sm { height: 30px; font-size: 0.8125rem; }

  select.input { padding: 0 8px; cursor: pointer; }

  /* ── Alerts ── */
  .alert {
    display: flex; align-items: center; gap: 7px;
    padding: 8px 11px; border-radius: 8px; font-size: 0.8125rem;
  }
  .alert.err { color: #ef4444; background: color-mix(in srgb, #ef4444 8%, transparent); border: 1px solid color-mix(in srgb, #ef4444 20%, transparent); }
  .alert.ok  { color: #10b981; background: color-mix(in srgb, #10b981 10%, transparent); border: 1px solid color-mix(in srgb, #10b981 25%, transparent); }

  /* ── Inline form (add qual / promo) ── */
  .inline-form {
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
    border-radius: 9px;
    padding: 14px;
    display: flex; flex-direction: column; gap: 12px;
  }
  .inline-form-foot { display: flex; justify-content: flex-end; gap: 8px; }

  /* ── List (quals / promos) ── */
  .list { display: flex; flex-direction: column; }

  .list-row {
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    padding: 11px 0;
    border-bottom: 1px solid var(--border-subtle);
  }
  .list-row:last-child { border-bottom: none; }

  .list-body { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
  .list-primary  { font-size: 0.875rem; font-weight: 500; color: var(--tx-high); }
  .list-secondary { font-size: 0.75rem; color: var(--tx-low); }

  .list-actions { display: flex; gap: 4px; flex-shrink: 0; }

  .list-edit-grid {
    display: grid; grid-template-columns: 1fr 1fr 80px 64px;
    gap: 8px; flex: 1;
  }

  .list-edit-actions { display: flex; gap: 4px; align-items: center; }

  /* ── Buttons ── */
  .btn-primary {
    height: 30px; padding: 0 13px;
    border-radius: 7px; border: none; cursor: pointer;
    background: var(--accent); color: #fff;
    font-size: 0.8125rem; font-weight: 600; font-family: inherit;
    display: flex; align-items: center; gap: 5px;
    transition: opacity 0.12s;
  }
  .btn-primary.sm { height: 26px; padding: 0 10px; font-size: 0.75rem; }
  .btn-primary:hover:not(:disabled) { opacity: 0.88; }
  .btn-primary:disabled { opacity: 0.55; cursor: not-allowed; }

  .btn-ghost {
    height: 28px; padding: 0 10px;
    border-radius: 7px; border: 1px solid var(--border-strong);
    background: transparent; color: var(--tx-mid); cursor: pointer;
    font-size: 0.8125rem; font-weight: 500; font-family: inherit;
    display: flex; align-items: center; gap: 5px;
    transition: background 0.12s, color 0.12s;
  }
  .btn-ghost.sm { height: 26px; font-size: 0.75rem; }
  .btn-ghost:hover { background: var(--surface-2); color: var(--tx-high); }

  .icon-btn {
    width: 28px; height: 28px; border-radius: 6px;
    border: 1px solid transparent; background: transparent;
    color: var(--tx-low); cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.12s, color 0.12s;
  }
  .icon-btn:hover { background: var(--surface-2); color: var(--tx-mid); }
  .icon-btn.danger:hover { background: color-mix(in srgb, #ef4444 10%, transparent); color: #ef4444; }
  .icon-btn.muted { color: var(--tx-low); }

  /* ── Password form ── */
  .pw-form { display: flex; flex-direction: column; gap: 14px; max-width: 480px; }

  .pw-row {
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  }
  @media (max-width: 480px) { .pw-row { grid-template-columns: 1fr; } }

  .pw-wrap { position: relative; }
  .pw-wrap .input { padding-right: 34px; }
  .eye {
    position: absolute; right: 9px; top: 50%; transform: translateY(-50%);
    background: none; border: none; cursor: pointer; color: var(--tx-low);
    padding: 0; display: flex; align-items: center;
  }
  .eye:hover { color: var(--tx-mid); }

  .bar { height: 2px; background: var(--border-subtle); border-radius: 99px; overflow: hidden; margin-top: 5px; }
  .bar-fill { height: 100%; border-radius: 99px; transition: width 0.3s, background 0.3s; }
  .bar-label { font-size: 0.6875rem; font-weight: 500; margin-top: 2px; }

  .form-foot { display: flex; justify-content: flex-end; }

  /* ── Misc ── */
  .center-state { display: flex; align-items: center; gap: 10px; padding: 24px 0; color: var(--tx-low); font-size: 0.875rem; }
  .empty-hint { font-size: 0.875rem; color: var(--tx-low); padding: 16px 0; margin: 0; text-align: center; }
  .muted { color: var(--tx-low); }

  :global(.spin) { animation: spin 0.7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
