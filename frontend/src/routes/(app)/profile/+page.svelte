<script lang="ts">
  import { auth, currentUser } from "$stores/auth";
  import { api } from "$api/client";
  import { KeyRound, User, AlertCircle, CheckCircle2, Eye, EyeOff, Loader2 } from "@lucide/svelte";

  // ── Change password ────────────────────────────────────────────
  let current = "";
  let next = "";
  let confirm = "";
  let showCurrent = false;
  let showNext = false;
  let saving = false;
  let pwError = "";
  let pwSuccess = false;

  async function changePassword() {
    pwError = ""; pwSuccess = false;
    if (!current || !next || !confirm) { pwError = "All fields are required."; return; }
    if (next.length < 8) { pwError = "New password must be at least 8 characters."; return; }
    if (next !== confirm) { pwError = "Passwords do not match."; return; }
    saving = true;
    try {
      await api.post("/auth/change-password", { current_password: current, new_password: next });
      auth.patchUser({ must_change_password: false });
      current = ""; next = ""; confirm = "";
      pwSuccess = true;
      setTimeout(() => { pwSuccess = false; }, 4000);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      pwError = err?.response?.data?.detail ?? "Something went wrong.";
    } finally {
      saving = false;
    }
  }

  $: strength = next.length === 0 ? 0
    : next.length < 8 ? 1
    : next.length < 12 ? 2
    : /[A-Z]/.test(next) && /[0-9]/.test(next) ? 4 : 3;
  $: strengthLabel = ["", "Too short", "Weak", "Good", "Strong"][strength];
  $: strengthColor = ["", "#ef4444", "#f59e0b", "#10b981", "#059669"][strength];
</script>

<svelte:head><title>My Profile — TTEK-SIS</title></svelte:head>

<div class="page">

  <!-- Identity card -->
  <section class="card">
    <div class="card-header">
      <div class="card-icon"><User size={18} /></div>
      <div>
        <h2 class="card-title">Account</h2>
        <p class="card-sub">Your identity and login details</p>
      </div>
    </div>

    <div class="info-grid">
      <div class="info-row">
        <span class="info-label">Name</span>
        <span class="info-value">{$currentUser?.full_name ?? "—"}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Email</span>
        <span class="info-value">{$currentUser?.email ?? "—"}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Role</span>
        <span class="info-value">{$currentUser?.system_role ?? "—"}</span>
      </div>
    </div>
  </section>

  <!-- Change password card -->
  <section class="card">
    <div class="card-header">
      <div class="card-icon"><KeyRound size={18} /></div>
      <div>
        <h2 class="card-title">Change password</h2>
        <p class="card-sub">Use a strong password — at least 8 characters</p>
      </div>
    </div>

    <form on:submit|preventDefault={changePassword} novalidate>

      {#if pwError}
        <div class="alert alert-err"><AlertCircle size={13} />{pwError}</div>
      {/if}
      {#if pwSuccess}
        <div class="alert alert-ok"><CheckCircle2 size={13} />Password updated successfully.</div>
      {/if}

      <div class="fields">
        <div class="field">
          <label for="pro-current">Current password</label>
          <div class="pw-wrap">
            <input
              id="pro-current" class="input"
              type={showCurrent ? "text" : "password"}
              bind:value={current}
              autocomplete="current-password"
              placeholder="Your current password"
            />
            <button type="button" class="eye-btn" on:click={() => showCurrent = !showCurrent}>
              {#if showCurrent}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
            </button>
          </div>
        </div>

        <div class="field">
          <label for="pro-new">New password</label>
          <div class="pw-wrap">
            <input
              id="pro-new" class="input"
              type={showNext ? "text" : "password"}
              bind:value={next}
              autocomplete="new-password"
              placeholder="At least 8 characters"
            />
            <button type="button" class="eye-btn" on:click={() => showNext = !showNext}>
              {#if showNext}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
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
          <label for="pro-confirm">Confirm new password</label>
          <input
            id="pro-confirm" class="input"
            type="password"
            bind:value={confirm}
            autocomplete="new-password"
            placeholder="Repeat new password"
          />
        </div>
      </div>

      <div class="form-footer">
        <button class="btn-primary" type="submit" disabled={saving}>
          {#if saving}<Loader2 size={14} class="spin" />{/if}
          Update password
        </button>
      </div>

    </form>
  </section>

</div>

<style>
  .page {
    max-width: 560px;
    display: flex; flex-direction: column; gap: 20px;
  }

  .card {
    background: var(--surface-0);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 20px 24px;
    display: flex; flex-direction: column; gap: 18px;
  }

  .card-header {
    display: flex; align-items: flex-start; gap: 12px;
  }

  .card-icon {
    width: 36px; height: 36px; border-radius: 9px;
    background: var(--accent-subtle); color: var(--accent);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }

  .card-title { margin: 0; font-size: 0.9375rem; font-weight: 700; color: var(--tx-high); }
  .card-sub   { margin: 2px 0 0; font-size: 0.8125rem; color: var(--tx-low); }

  .info-grid { display: flex; flex-direction: column; gap: 0; }

  .info-row {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid var(--border-subtle);
  }
  .info-row:last-child { border-bottom: none; }

  .info-label {
    width: 80px; flex-shrink: 0;
    font-size: 0.8125rem; font-weight: 500; color: var(--tx-low);
  }
  .info-value { font-size: 0.875rem; color: var(--tx-high); }

  .alert {
    display: flex; align-items: center; gap: 7px;
    padding: 9px 12px; border-radius: 8px;
    font-size: 0.8125rem;
  }
  .alert-err {
    color: #ef4444;
    background: color-mix(in srgb, #ef4444 8%, transparent);
    border: 1px solid color-mix(in srgb, #ef4444 20%, transparent);
  }
  .alert-ok {
    color: #10b981;
    background: color-mix(in srgb, #10b981 10%, transparent);
    border: 1px solid color-mix(in srgb, #10b981 25%, transparent);
  }

  .fields { display: flex; flex-direction: column; gap: 14px; }

  .field { display: flex; flex-direction: column; gap: 5px; }
  .field label { font-size: 0.8125rem; font-weight: 500; color: var(--tx-mid); }

  .pw-wrap { position: relative; }
  .pw-wrap .input { padding-right: 38px; }

  .eye-btn {
    position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
    background: none; border: none; cursor: pointer;
    color: var(--tx-low); display: flex; align-items: center; padding: 0;
  }
  .eye-btn:hover { color: var(--tx-mid); }

  .input {
    width: 100%; box-sizing: border-box;
    height: 38px; padding: 0 12px;
    border: 1px solid var(--border-strong);
    border-radius: 8px; font-size: 0.9rem;
    background: var(--surface-1); color: var(--tx-high);
    font-family: inherit;
    transition: border-color 0.12s, box-shadow 0.12s;
    outline: none;
  }
  .input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 14%, transparent);
  }
  .input::placeholder { color: var(--tx-low); }

  .strength-bar {
    height: 3px; background: var(--border-subtle);
    border-radius: 99px; overflow: hidden; margin-top: 4px;
  }
  .strength-fill { height: 100%; border-radius: 99px; transition: width 0.3s, background 0.3s; }
  .strength-label { font-size: 0.75rem; font-weight: 500; }

  .form-footer { display: flex; justify-content: flex-end; }

  .btn-primary {
    height: 36px; padding: 0 18px;
    border-radius: 8px; border: none; cursor: pointer;
    background: var(--accent); color: #fff;
    font-size: 0.875rem; font-weight: 600; font-family: inherit;
    display: flex; align-items: center; gap: 7px;
    transition: opacity 0.12s;
  }
  .btn-primary:hover:not(:disabled) { opacity: 0.88; }
  .btn-primary:disabled { opacity: 0.55; cursor: not-allowed; }

  :global(.spin) { animation: spin 0.75s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
