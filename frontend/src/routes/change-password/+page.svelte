<script lang="ts">
  import { auth, isAuthenticated } from "$stores/auth";
  import { api } from "$api/client";
  import { goto } from "$app/navigation";
  import { KeyRound, Eye, EyeOff, AlertCircle } from "@lucide/svelte";

  let current = "";
  let next = "";
  let confirm = "";
  let showCurrent = false;
  let showNext = false;
  let saving = false;
  let error = "";

  // Redirect to login if not authenticated
  $: if (!$auth.loading && !$isAuthenticated) {
    goto("/login");
  }

  // If they don't actually need to change, redirect to dashboard
  $: if (!$auth.loading && $auth.user && !$auth.user.must_change_password) {
    goto("/dashboard");
  }

  function apiError(e: unknown): string {
    const err = e as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail ?? "Something went wrong.";
  }

  async function submit() {
    error = "";
    if (!current || !next || !confirm) { error = "All fields are required."; return; }
    if (next.length < 8) { error = "New password must be at least 8 characters."; return; }
    if (next !== confirm) { error = "Passwords do not match."; return; }
    saving = true;
    try {
      await api.post("/auth/change-password", { current_password: current, new_password: next });
      auth.patchUser({ must_change_password: false });
      goto("/dashboard");
    } catch (e) {
      error = apiError(e);
    } finally {
      saving = false;
    }
  }
</script>

<svelte:head><title>Set New Password — TTEK-SIS</title></svelte:head>

<div class="page">
  <div class="card">
    <div class="card-icon">
      <KeyRound size={22} />
    </div>
    <h1 class="title">Set a new password</h1>
    <p class="sub">Your account has a temporary password. Choose a permanent one to continue.</p>

      <form on:submit|preventDefault={submit} novalidate>
        <div class="field">
          <label for="cp-current">Temporary password</label>
          <div class="pw-wrap">
            <input
              id="cp-current" class="input"
              type={showCurrent ? "text" : "password"}
              bind:value={current}
              autocomplete="current-password"
              placeholder="Your temporary password"
            />
            <button type="button" class="eye-btn" on:click={() => showCurrent = !showCurrent}>
              {#if showCurrent}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
            </button>
          </div>
        </div>

        <div class="field">
          <label for="cp-new">New password</label>
          <div class="pw-wrap">
            <input
              id="cp-new" class="input"
              type={showNext ? "text" : "password"}
              bind:value={next}
              autocomplete="new-password"
              placeholder="At least 8 characters"
            />
            <button type="button" class="eye-btn" on:click={() => showNext = !showNext}>
              {#if showNext}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
            </button>
          </div>
        </div>

        <div class="field">
          <label for="cp-confirm">Confirm new password</label>
          <input
            id="cp-confirm" class="input"
            type="password"
            bind:value={confirm}
            autocomplete="new-password"
            placeholder="Repeat new password"
          />
        </div>

        {#if error}
          <div class="err-box"><AlertCircle size={13} />{error}</div>
        {/if}

        <button class="submit-btn" type="submit" disabled={saving}>
          {#if saving}Saving…{:else}Set password{/if}
        </button>
      </form>
  </div>
</div>

<style>
  .page {
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    background: var(--surface-1);
    padding: 24px;
  }

  .card {
    width: 100%; max-width: 400px;
    background: var(--surface-0);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 32px;
    display: flex; flex-direction: column; gap: 16px;
    box-shadow: var(--shadow-sm);
  }

  .card-icon {
    width: 44px; height: 44px; border-radius: 12px;
    background: var(--accent-subtle);
    color: var(--accent);
    display: flex; align-items: center; justify-content: center;
  }

  .title {
    margin: 0; font-size: 1.1rem; font-weight: 700; color: var(--tx-high);
  }

  .sub {
    margin: -8px 0 0; font-size: 0.875rem; color: var(--tx-low); line-height: 1.5;
  }

  form { display: flex; flex-direction: column; gap: 12px; }

  .field { display: flex; flex-direction: column; gap: 5px; }
  .field label { font-size: 0.8125rem; font-weight: 600; color: var(--tx-mid); }

  .pw-wrap { position: relative; }
  .pw-wrap .input { padding-right: 38px; width: 100%; }

  .eye-btn {
    position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
    background: none; border: none; cursor: pointer;
    color: var(--tx-low); display: flex; align-items: center;
    padding: 0;
  }
  .eye-btn:hover { color: var(--tx-mid); }

  .err-box {
    display: flex; align-items: center; gap: 7px;
    padding: 9px 12px; border-radius: 8px;
    background: var(--err-bg); color: var(--err-text);
    border: 1px solid color-mix(in srgb, var(--err-text) 18%, transparent);
    font-size: 0.8125rem;
  }

  .submit-btn {
    width: 100%; height: 40px; border-radius: 8px;
    background: var(--accent); color: #fff;
    border: none; cursor: pointer;
    font-size: 0.9375rem; font-weight: 600;
    transition: opacity 0.12s;
    margin-top: 4px;
  }
  .submit-btn:hover:not(:disabled) { opacity: 0.88; }
  .submit-btn:disabled { opacity: 0.55; cursor: not-allowed; }
</style>
