<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { api } from "$api/client";
  import { schoolBranding } from "$stores/school";
  import { Eye, EyeOff, AlertCircle, Loader2, CheckCircle } from "@lucide/svelte";

  const token = $page.params.token;

  let email = "";
  let loading = true;
  let loadError = "";

  let password = "";
  let confirm = "";
  let showPw = false;
  let showConfirm = false;
  let submitting = false;
  let submitError = "";
  let done = false;
  let countdown = 3;

  onMount(async () => {
    // Apply saved theme
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const saved = localStorage.getItem("sis-theme");
    const isDark = saved === "dark" || ((!saved || saved === "system") && mq.matches);
    document.documentElement.classList.toggle("dark", isDark);
    const handler = (e: MediaQueryListEvent) => {
      if (!saved || saved === "system") document.documentElement.classList.toggle("dark", e.matches);
    };
    mq.addEventListener("change", handler);

    try {
      const { data } = await api.get<{ email: string }>(`/auth/reset-password/${token}`);
      email = data.email;
    } catch (e: unknown) {
      const err = e as { response?: { status?: number } };
      loadError = err?.response?.status === 410
        ? "This reset link has expired — they're valid for 2 hours. Request a new one from the login page."
        : "This reset link is invalid or has already been used. Request a new one if you still need access.";
    } finally {
      loading = false;
    }

    return () => mq.removeEventListener("change", handler);
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
      await api.post(`/auth/reset-password/${token}`, { password });
      done = true;
      const timer = setInterval(() => {
        countdown -= 1;
        if (countdown <= 0) { clearInterval(timer); goto("/login"); }
      }, 1000);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string }; status?: number } };
      submitError = err?.response?.status === 410
        ? "This link has expired. Request a new one."
        : err?.response?.data?.detail ?? "Something went wrong. Please try again.";
    } finally {
      submitting = false;
    }
  }

  $: accentColor = $schoolBranding?.accent_color ?? "#185FA5";
  $: schoolName  = $schoolBranding?.name ?? "TTEK-SMS";
  $: logoUrl     = $schoolBranding?.logo_url ?? null;
</script>

<svelte:head>
  <title>Reset password — {schoolName}</title>
</svelte:head>

<div class="shell">
  <div class="card">

    <div class="brand">
      {#if logoUrl}
        <img src={logoUrl} alt="{schoolName} logo" class="brand-logo" />
      {:else}
        <div class="brand-mark" style="background:{accentColor}">{schoolName.charAt(0).toUpperCase()}</div>
      {/if}
      <span class="brand-name">{schoolName}</span>
    </div>

    {#if loading}
      <div class="state-center">
        <Loader2 size={24} class="spin" />
        <span>Validating link…</span>
      </div>

    {:else if loadError}
      <div class="state-center error-state">
        <AlertCircle size={28} />
        <p class="state-msg">{loadError}</p>
        <a href="/forgot-password" class="link">Request a new link</a>
      </div>

    {:else if done}
      <div class="state-center success-state">
        <CheckCircle size={32} />
        <p class="state-title">Password updated</p>
        <p class="state-msg">Your password has been reset successfully.</p>
        <p class="redirect-note">Taking you to sign in in {countdown}…</p>
        <a href="/login" class="btn-primary" style="background:{accentColor}">Sign in now</a>
      </div>

    {:else}
      <div class="form-header">
        <h1>Set a new password</h1>
        <p>For <strong>{email}</strong></p>
      </div>

      <form on:submit|preventDefault={submit}>
        {#if submitError}
          <div class="err-box"><AlertCircle size={13} /> {submitError}</div>
        {/if}

        <div class="field">
          <label for="pw">New password</label>
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

        <button type="submit" class="btn-primary" disabled={submitting} style="background:{accentColor}">
          {#if submitting}<Loader2 size={14} class="spin" />{/if}
          Reset password
        </button>
      </form>
    {/if}

    {#if !done}
      <a href="/login" class="back-link">← Back to sign in</a>
    {/if}

  </div>
</div>

<style>
  :global(body) { margin: 0; }

  .shell {
    min-height: 100dvh;
    display: flex; align-items: center; justify-content: center;
    background: var(--bg); padding: 24px 16px;
  }

  .card {
    width: 100%; max-width: 420px;
    background: var(--surface-0);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 36px 32px;
    display: flex; flex-direction: column; gap: 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.07);
  }

  .brand {
    display: flex; align-items: center; gap: 10px;
  }
  .brand-mark {
    width: 32px; height: 32px; border-radius: 8px;
    color: #fff; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 1rem;
  }
  .brand-logo {
    width: 32px; height: 32px; border-radius: 8px;
    object-fit: contain; border: 1px solid var(--border-subtle);
    flex-shrink: 0;
  }
  .brand-name { font-weight: 600; font-size: 0.9375rem; color: var(--tx-high); }

  .form-header { display: flex; flex-direction: column; gap: 4px; }
  .form-header h1 { margin: 0; font-size: 1.25rem; font-weight: 700; color: var(--tx-high); }
  .form-header p { margin: 0; font-size: 0.875rem; color: var(--tx-mid); }

  form { display: flex; flex-direction: column; gap: 16px; }

  .field { display: flex; flex-direction: column; gap: 6px; }
  .field label { font-size: 0.8125rem; font-weight: 500; color: var(--tx-mid); }

  .input-wrap { position: relative; }
  .input {
    width: 100%; box-sizing: border-box;
    height: 38px; padding: 0 36px 0 12px;
    border: 1px solid var(--border-strong);
    border-radius: 8px; font-size: 0.9375rem;
    background: var(--surface-1); color: var(--tx-high);
    font-family: inherit;
    transition: border-color 0.12s, box-shadow 0.12s;
  }
  .input:focus {
    outline: none; border-color: var(--accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 15%, transparent);
  }
  .input::placeholder { color: var(--tx-low); }

  .eye-btn {
    position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
    background: none; border: none; cursor: pointer;
    color: var(--tx-low); padding: 2px; display: flex; align-items: center;
  }

  .strength-bar {
    height: 3px; background: var(--border-subtle);
    border-radius: 99px; overflow: hidden; margin-top: 4px;
  }
  .strength-fill { height: 100%; border-radius: 99px; transition: width 0.3s, background 0.3s; }
  .strength-label { font-size: 0.75rem; font-weight: 500; }

  .btn-primary {
    height: 40px; border-radius: 9px; border: none; cursor: pointer;
    color: #fff; font-size: 0.9375rem; font-weight: 600; font-family: inherit;
    display: flex; align-items: center; justify-content: center; gap: 8px;
    transition: filter 0.12s, opacity 0.12s;
    text-decoration: none;
  }
  .btn-primary:hover:not(:disabled) { filter: brightness(1.1); }
  .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

  .err-box {
    display: flex; align-items: center; gap: 6px;
    padding: 9px 12px; border-radius: 8px;
    font-size: 0.8125rem; color: #ef4444;
    background: color-mix(in srgb, #ef4444 8%, transparent);
    border: 1px solid color-mix(in srgb, #ef4444 20%, transparent);
  }

  .state-center {
    display: flex; flex-direction: column; align-items: center;
    gap: 12px; padding: 16px 0; text-align: center;
    color: var(--tx-mid); font-size: 0.9375rem;
  }
  .error-state { color: #ef4444; }
  .success-state { color: #10b981; }
  .state-title { margin: 0; font-size: 1.1rem; font-weight: 700; color: var(--tx-high); }
  .state-msg { margin: 0; color: var(--tx-mid); font-size: 0.875rem; line-height: 1.5; }
  .redirect-note { margin: 0; font-size: 0.8125rem; color: var(--tx-low); }

  .link { color: var(--accent); font-size: 0.875rem; text-decoration: none; }
  .link:hover { text-decoration: underline; }

  .back-link {
    display: block; text-align: center;
    font-size: 0.8125rem; color: var(--tx-low);
    text-decoration: none; transition: color 0.12s;
  }
  .back-link:hover { color: var(--tx-mid); }

  :global(.spin) { animation: spin 0.7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
