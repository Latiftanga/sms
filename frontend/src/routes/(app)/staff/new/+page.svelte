<script lang="ts">
  import { goto } from "$app/navigation";
  import { api } from "$api/client";
  import { toast } from "$stores/toast";
  import Button from "$components/ui/Button.svelte";
  import { ArrowLeft, User, Phone, Briefcase, Shield } from "@lucide/svelte";

  // ── Form state ────────────────────────────────────────────────────
  let form = {
    // Personal
    first_name: "", middle_name: "", last_name: "",
    gender: "", date_of_birth: "",
    // Contact
    phone: "", personal_email: "", address: "",
    // Emergency
    emergency_contact_name: "", emergency_contact_phone: "",
    // Employment
    staff_id: "", category: "TEACHING", employment_type: "PERMANENT",
    designation: "", date_joined: "",
    // GES
    ges_staff_id: "", registered_no: "", licence_no: "", ssnit_no: "",
  };

  let saving = false;
  let errors: Record<string, string> = {};
  let apiError = "";

  function validate(): boolean {
    errors = {};
    if (!form.first_name.trim()) errors.first_name = "Required";
    if (!form.last_name.trim())  errors.last_name  = "Required";
    if (!form.category)          errors.category   = "Required";
    return Object.keys(errors).length === 0;
  }

  async function submit() {
    if (!validate()) return;
    saving = true; apiError = "";
    try {
      // Strip empty strings → null so the backend doesn't store blank strings
      const payload: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(form)) {
        payload[k] = v === "" ? null : v;
      }
      const { data } = await api.post<{ id: string }>("/staff", payload);
      toast.success("Staff member created");
      await goto(`/staff/${data.id}`);
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } } };
      apiError = err?.response?.data?.detail ?? "Something went wrong.";
    } finally {
      saving = false;
    }
  }
</script>

<svelte:head><title>Add Staff Member — TTEK-SIS</title></svelte:head>

<div class="page">

  <!-- Page header -->
  <div class="page-top">
    <div class="page-top-left">
      <button class="back" on:click={() => goto("/staff")}>
        <ArrowLeft size={14} /> Staff
      </button>
      <div class="page-heading">
        <h1 class="title">Add staff member</h1>
        <p class="subtitle">Complete the form below. All sections can be edited later from the staff profile.</p>
      </div>
    </div>
    <div class="page-top-actions">
      <Button type="button" variant="ghost" on:click={() => goto("/staff")}>Cancel</Button>
      <Button type="submit" form="new-staff-form" loading={saving}>Save staff member</Button>
    </div>
  </div>

  <form id="new-staff-form" on:submit|preventDefault={submit} novalidate>

    {#if apiError}
      <div class="api-error" role="alert">{apiError}</div>
    {/if}

    <div class="form-layout">

      <!-- ── Left column ─────────────────────────────────────────── -->
      <div class="col">

        <!-- Personal Information -->
        <div class="card">
          <div class="card-head">
            <div class="card-hicon"><User size={14} /></div>
            <span>Personal Information</span>
          </div>
          <div class="card-body">

            <div class="row-3">
              <div class="field" class:has-error={errors.first_name}>
                <label for="f-first">First name <span class="req">*</span></label>
                <input id="f-first" class="input" bind:value={form.first_name} placeholder="Kwame" autocomplete="off" />
                {#if errors.first_name}<span class="ferr">{errors.first_name}</span>{/if}
              </div>
              <div class="field">
                <label for="f-mid">Middle name</label>
                <input id="f-mid" class="input" bind:value={form.middle_name} placeholder="Asante" autocomplete="off" />
              </div>
              <div class="field" class:has-error={errors.last_name}>
                <label for="f-last">Last name <span class="req">*</span></label>
                <input id="f-last" class="input" bind:value={form.last_name} placeholder="Mensah" autocomplete="off" />
                {#if errors.last_name}<span class="ferr">{errors.last_name}</span>{/if}
              </div>
            </div>

            <div class="row-2">
              <div class="field">
                <label for="f-gender">Gender</label>
                <select id="f-gender" class="input" bind:value={form.gender}>
                  <option value="">— select —</option>
                  <option value="MALE">Male</option>
                  <option value="FEMALE">Female</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              <div class="field">
                <label for="f-dob">Date of birth</label>
                <input id="f-dob" class="input" type="date" bind:value={form.date_of_birth} />
              </div>
            </div>

          </div>
        </div>

        <!-- Contact Details -->
        <div class="card">
          <div class="card-head">
            <div class="card-hicon"><Phone size={14} /></div>
            <span>Contact Details</span>
          </div>
          <div class="card-body">

            <div class="row-2">
              <div class="field">
                <label for="f-phone">Phone number</label>
                <input id="f-phone" class="input" bind:value={form.phone} placeholder="0244 123 456" type="tel" />
              </div>
              <div class="field">
                <label for="f-email">Personal email</label>
                <input id="f-email" class="input" bind:value={form.personal_email} placeholder="kwame@gmail.com" type="email" />
              </div>
            </div>

            <div class="field">
              <label for="f-addr">Home address</label>
              <input id="f-addr" class="input" bind:value={form.address} placeholder="House no., street, town" />
            </div>

            <div class="divider"></div>
            <p class="section-label">Emergency contact</p>

            <div class="row-2">
              <div class="field">
                <label for="f-ecn">Contact name</label>
                <input id="f-ecn" class="input" bind:value={form.emergency_contact_name} placeholder="Full name" />
              </div>
              <div class="field">
                <label for="f-ecp">Contact phone</label>
                <input id="f-ecp" class="input" bind:value={form.emergency_contact_phone} placeholder="0201 987 654" type="tel" />
              </div>
            </div>

          </div>
        </div>

      </div>

      <!-- ── Right column ────────────────────────────────────────── -->
      <div class="col">

        <!-- Employment -->
        <div class="card">
          <div class="card-head">
            <div class="card-hicon"><Briefcase size={14} /></div>
            <span>Employment</span>
          </div>
          <div class="card-body">

            <div class="row-2">
              <div class="field" class:has-error={errors.category}>
                <label for="f-cat">Category <span class="req">*</span></label>
                <select id="f-cat" class="input" bind:value={form.category}>
                  <option value="TEACHING">Teaching</option>
                  <option value="NON-TEACHING">Non-Teaching</option>
                </select>
                {#if errors.category}<span class="ferr">{errors.category}</span>{/if}
              </div>
              <div class="field">
                <label for="f-emp">Employment type</label>
                <select id="f-emp" class="input" bind:value={form.employment_type}>
                  <option value="PERMANENT">Permanent</option>
                  <option value="CONTRACT">Contract</option>
                  <option value="VOLUNTEER">Volunteer</option>
                  <option value="GES_POSTED">GES Posted</option>
                </select>
              </div>
            </div>

            <div class="field">
              <label for="f-desig">Designation</label>
              <select id="f-desig" class="input" bind:value={form.designation}>
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
                <label for="f-sid">School staff ID</label>
                <input id="f-sid" class="input" bind:value={form.staff_id} placeholder="e.g. STF001" />
              </div>
              <div class="field">
                <label for="f-joined">Date joined</label>
                <input id="f-joined" class="input" type="date" bind:value={form.date_joined} />
              </div>
            </div>

          </div>
        </div>

        <!-- GES Details -->
        <div class="card">
          <div class="card-head">
            <div class="card-hicon"><Shield size={14} /></div>
            <span>GES Details <span class="optional-tag">optional</span></span>
          </div>
          <div class="card-body">
            <p class="card-hint">Only required for government-posted or GES-employed staff.</p>

            <div class="row-2">
              <div class="field">
                <label for="f-ges">GES staff ID</label>
                <input id="f-ges" class="input" bind:value={form.ges_staff_id} placeholder="GES number" />
              </div>
              <div class="field">
                <label for="f-reg">Registered no.</label>
                <input id="f-reg" class="input" bind:value={form.registered_no} placeholder="Registration no." />
              </div>
            </div>

            <div class="row-2">
              <div class="field">
                <label for="f-lic">Licence no.</label>
                <input id="f-lic" class="input" bind:value={form.licence_no} placeholder="Teaching licence" />
              </div>
              <div class="field">
                <label for="f-ssnit">SSNIT no.</label>
                <input id="f-ssnit" class="input" bind:value={form.ssnit_no} placeholder="SSNIT number" />
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>

  </form>
</div>

<style>
  .page {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  /* ── Page top ─────────────────────────────────── */
  .page-top {
    display: flex; align-items: flex-start;
    justify-content: space-between; gap: 16px;
  }

  .page-top-left { display: flex; flex-direction: column; gap: 6px; }

  .page-top-actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }

  .back {
    display: inline-flex; align-items: center; gap: 6px;
    background: none; border: none; cursor: pointer;
    color: var(--tx-low); font-size: 0.875rem; padding: 0;
    width: fit-content; transition: color 0.12s;
  }
  .back:hover { color: var(--tx-high); }

  .page-heading { display: flex; flex-direction: column; gap: 3px; }

  .title { margin: 0; font-size: 1.25rem; font-weight: 700; color: var(--tx-high); }
  .subtitle { margin: 0; font-size: 0.875rem; color: var(--tx-low); }

  /* ── API error ───────────────────────────────── */
  .api-error {
    padding: 10px 14px; border-radius: 8px;
    font-size: 0.875rem; color: #ef4444;
    background: color-mix(in srgb, #ef4444 8%, transparent);
    border: 1px solid color-mix(in srgb, #ef4444 20%, transparent);
  }

  /* ── Two-column layout ───────────────────────── */
  .form-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    align-items: start;
  }
  @media (max-width: 860px) {
    .form-layout { grid-template-columns: 1fr; }
  }

  .col { display: flex; flex-direction: column; gap: 20px; }

  /* ── Cards ───────────────────────────────────── */
  .card {
    background: var(--surface-0);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    overflow: hidden;
  }

  .card-head {
    display: flex; align-items: center; gap: 10px;
    padding: 12px 18px;
    border-bottom: 1px solid var(--border-subtle);
    font-size: 0.875rem; font-weight: 600; color: var(--tx-high);
    background: var(--surface-1);
  }

  .card-hicon {
    width: 28px; height: 28px; border-radius: 7px;
    background: var(--accent-subtle); color: var(--accent);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }

  .optional-tag {
    font-size: 0.7rem; font-weight: 500;
    color: var(--tx-low); margin-left: 4px;
    text-transform: uppercase; letter-spacing: 0.05em;
  }

  .card-body {
    padding: 18px 20px;
    display: flex; flex-direction: column; gap: 14px;
  }

  .card-hint {
    margin: 0; font-size: 0.8125rem; color: var(--tx-low);
    line-height: 1.5;
  }

  /* ── Divider + sub-label ─────────────────────── */
  .divider {
    height: 1px; background: var(--border-subtle); margin: 2px 0;
  }

  .section-label {
    margin: 0; font-size: 0.75rem; font-weight: 600;
    color: var(--tx-low); text-transform: uppercase; letter-spacing: 0.06em;
  }

  /* ── Rows ────────────────────────────────────── */
  .row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }

  @media (max-width: 600px) {
    .row-2, .row-3 { grid-template-columns: 1fr; }
  }

</style>
