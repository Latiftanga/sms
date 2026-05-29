<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { api } from "$api/client";
  import { auth } from "$lib/stores/auth";
  import { Eye, EyeOff, AlertCircle, Loader2 } from "@lucide/svelte";

  const token = $page.params.token;

  let staffName = "";
  let email = "";
  let loading = true;
  let loadError = "";

  let password = "";
  let confirm = "";
  let showPw = false;
  let showConfirm = false;
  let submitting = false;
  let submitError = "";

  onMount(async () => {
    try {
      const { data } = await api.get<{ staff_name: string; email: string }>(`/auth/invite/${token}`);
      staffName = data.staff_name;
      email = data.email;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string }; status?: number } };
      loadError = err?.response?.status === 410
        ? "This invite link has expired. Ask your admin to send a new one."
        : "This invite link is invalid or has already been used.";
    } finally {
      loading = false;
    }
  });

  $: strength = password.length === 0 ? 0
    : password.length < 8 ? 1
    : password.length < 12 ? 2
    : /[A-Z]/.test(password) && /[0-9]/.test(password) ? 4 : 3;

  $: strengthLabel = ["", "Too short", "Weak", "Good", "Strong"][strength];
  $: strengthColor = ["", "#ef4444", "#f59e0b", "#10b981", "#059669"][strength];

  async function submit() {
    submitError = "";
    if (!password) { submitError = "Password is required."; return; }
    if (password.length < 8) { submitError = "Password must be at least 8 characters."; return; }
    if (password !== confirm) { submitError = "Passwords do not match."; return; }
    submitting = true;
    try {
      await api.post(`/auth/invite/${token}`, { password });
      await auth.login(email, password);
      goto("/dashboard");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string }; status?: number } };
      submitError = err?.response?.status === 410
        ? "This invite has expired. Ask your admin to send a new one."
        : err?.response?.data?.detail ?? "Something went wrong. Please try again.";
    } finally {
      submitting = false;
    }
  }
</script>

<svelte:head>
  <title>Set up your account — TTEK SIS</title>
</svelte:head>

<div class="invite-page">
  <div class="invite-card">

    <div class="brand">
      <div class="brand-mark">T</div>
      <span class="brand-name">TTEK SIS</span>
    </div>

    {#if loading}
      <div class="state-center">
        <Loader2 size={24} class="spin" />
        <span>Validating invite…</span>
      </div>

    {:else if loadError}
      <div class="state-center error-state">
        <AlertCircle size={28} class="error-icon" />
        <p class="error-msg">{loadError}</p>
        <a href="/login" class="back-link">Back to sign in</a>
      </div>

    {:else}
      <div class="invite-header">
        <h1>Welcome{staffName ? `, ${staffName.split(" ")[0]}` : ""}!</h1>
        <p class="invite-sub">Set a password for <strong>{email}</strong> to activate your account.</p>
      </div>

      <form class="invite-form" on:submit|preventDefault={submit}>
        {#if submitError}
          <p class="form-error"><AlertCircle size={13} /> {submitError}</p>
        {/if}

        <div class="field">
          <label for="pw">Password</label>
          <div class="input-wrap">
            <input
              id="pw"
              class="input"
              type={showPw ? "text" : "password"}
              bind:value={password}
              placeholder="At least 8 characters"
              autocomplete="new-password"
            />
            <button type="button" class="eye-btn" on:click={() => showPw = !showPw} tabindex="-1">
              {#if showPw}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
            </button>
          </div>
          {#if password.length > 0}
            <div class="strength-bar">
              <div class="strength-fill" style="width:{strength * 25}%;background:{strengthColor}"></div>
            </div>
            <span class="strength-label" style="color:{strengthColor}">{strengthLabel}</span>
          {/if}
        </div>

        <div class="field">
          <label for="confirm">Confirm password</label>
          <div class="input-wrap">
            <input
              id="confirm"
              class="input"
              type={showConfirm ? "text" : "password"}
              bind:value={confirm}
              placeholder="Repeat your password"
              autocomplete="new-password"
            />
            <button type="button" class="eye-btn" on:click={() => showConfirm = !showConfirm} tabindex="-1">
              {#if showConfirm}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
            </button>
          </div>
        </div>

        <button type="submit" class="btn-primary" class:loading={submitting} disabled={submitting}>
          {#if submitting}<Loader2 size={14} class="spin" />{/if}
          Activate account
        </button>
      </form>

      <p class="footer-note">Already set up? <a href="/login">Sign in</a></p>
    {/if}

  </div>
</div>

<style>
  :global(body) { margin: 0; }

  .invite-page {
    min-height: 100dvh;
    display: flex; align-items: center; justify-content: center;
    background: var(--bg, #F2F0EC);
    padding: 24px 16px;
  }

  .invite-card {
    width: 100%; max-width: 420px;
    background: var(--surface-1, #fff);
    border: 1px solid var(--border-subtle, #e5e2db);
    border-radius: 16px;
    padding: 36px 32px;
    display: flex; flex-direction: column; gap: 24px;
  }

  /* ── Brand ── */
  .brand {
    display: flex; align-items: center; gap: 10px;
  }
  .brand-mark {
    width: 32px; height: 32px; border-radius: 8px;
    background: var(--accent, #6366f1); color: #fff;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 1rem;
  }
  .brand-name { font-weight: 600; font-size: 0.9375rem; color: var(--tx-high, #1a1a1a); }

  /* ── Header ── */
  .invite-header { display: flex; flex-direction: column; gap: 6px; }
  .invite-header h1 { margin: 0; font-size: 1.375rem; font-weight: 700; color: var(--tx-high, #1a1a1a); }
  .invite-sub { margin: 0; font-size: 0.875rem; color: var(--tx-mid, #666); line-height: 1.5; }

  /* ── Form ── */
  .invite-form { display: flex; flex-direction: column; gap: 16px; }

  .field { display: flex; flex-direction: column; gap: 6px; }
  .field label { font-size: 0.8125rem; font-weight: 500; color: var(--tx-mid, #555); }

  .input-wrap { position: relative; }
  .input {
    width: 100%; box-sizing: border-box;
    height: 38px; padding: 0 36px 0 12px;
    border: 1px solid var(--border-strong, #d0cdc7);
    border-radius: 8px; font-size: 0.9375rem;
    background: var(--surface-0, #f8f6f1);
    color: var(--tx-high, #1a1a1a);
    transition: border-color 0.12s, box-shadow 0.12s;
    font-family: inherit;
  }
  .input:focus { outline: none; border-color: var(--accent, #6366f1); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent, #6366f1) 15%, transparent); }

  .eye-btn {
    position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
    background: none; border: none; cursor: pointer; color: var(--tx-low, #999);
    padding: 2px; display: flex; align-items: center;
  }

  /* ── Strength ── */
  .strength-bar {
    height: 3px; background: var(--border-subtle, #e5e2db);
    border-radius: 99px; overflow: hidden; margin-top: 4px;
  }
  .strength-fill { height: 100%; border-radius: 99px; transition: width 0.3s, background 0.3s; }
  .strength-label { font-size: 0.75rem; font-weight: 500; }

  /* ── Submit button ── */
  .btn-primary {
    height: 40px; border-radius: 9px; border: none; cursor: pointer;
    background: var(--accent, #6366f1); color: #fff;
    font-size: 0.9375rem; font-weight: 600; font-family: inherit;
    display: flex; align-items: center; justify-content: center; gap: 8px;
    transition: background 0.12s, opacity 0.12s;
    margin-top: 4px;
  }
  .btn-primary:hover:not(:disabled) { background: color-mix(in srgb, var(--accent, #6366f1) 85%, #000); }
  .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

  /* ── Form error ── */
  .form-error {
    display: flex; align-items: center; gap: 6px;
    padding: 9px 12px; border-radius: 8px;
    font-size: 0.8125rem; color: #ef4444;
    background: color-mix(in srgb, #ef4444 8%, transparent);
    border: 1px solid color-mix(in srgb, #ef4444 20%, transparent);
  }

  /* ── States ── */
  .state-center {
    display: flex; flex-direction: column; align-items: center;
    gap: 12px; padding: 24px 0; text-align: center;
    color: var(--tx-mid, #666); font-size: 0.9375rem;
  }
  :global(.state-center .spin) { color: var(--tx-low, #aaa); }

  .error-state :global(.error-icon) { color: #ef4444; }
  .error-msg { margin: 0; color: var(--tx-mid, #666); }
  .back-link { color: var(--accent, #6366f1); font-size: 0.875rem; text-decoration: none; }
  .back-link:hover { text-decoration: underline; }

  /* ── Footer ── */
  .footer-note { margin: 0; font-size: 0.8125rem; color: var(--tx-low, #999); text-align: center; }
  .footer-note a { color: var(--accent, #6366f1); text-decoration: none; }
  .footer-note a:hover { text-decoration: underline; }

  /* ── Animations ── */
  :global(.spin) { animation: spin 0.7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
