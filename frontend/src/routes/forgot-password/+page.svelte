<script lang="ts">
  import { schoolBranding } from "$stores/school";
  import { api } from "$lib/api/client";
  import { onMount } from "svelte";
  import { Loader2, ArrowLeft } from "@lucide/svelte";

  // Inherit theme so this page respects the saved preference
  onMount(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const saved = localStorage.getItem("sis-theme");
    const isDark =
      saved === "dark" || ((!saved || saved === "system") && mq.matches);
    document.documentElement.classList.toggle("dark", isDark);
    const handler = (e: MediaQueryListEvent) => {
      if (!saved || saved === "system")
        document.documentElement.classList.toggle("dark", e.matches);
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  });

  let email = "";
  let loading = false;
  let sent = false;
  let error = "";

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    loading = true; error = "";
    try {
      await api.post("/auth/forgot-password", { email });
    } catch {
      // Always show success to avoid user enumeration
    } finally {
      loading = false;
      sent = true;
    }
  }

  $: accentColor = $schoolBranding?.accent_color ?? "#185FA5";
  $: schoolName  = $schoolBranding?.name ?? "School Information System";
  $: logoUrl     = $schoolBranding?.logo_url ?? null;
</script>

<svelte:head>
  <title>Reset password — {schoolName}</title>
</svelte:head>

<div class="shell">
  <div class="card">

    <div class="identity">
      {#if logoUrl}
        <img src={logoUrl} alt="{schoolName} logo" class="logo-img" />
      {:else}
        <div class="logo-initial" style="background:{accentColor}">
          {schoolName.charAt(0).toUpperCase()}
        </div>
      {/if}
      <h1 class="school-name">{schoolName}</h1>
    </div>

    <div class="divider"></div>

    {#if sent}
      <div class="sent-state">
        <div class="sent-icon" style="color:{accentColor}">✓</div>
        <p class="sent-title">Check your phone</p>
        <p class="sent-body">
          If <strong>{email}</strong> has an account with a registered phone number,
          you'll receive a reset link via SMS. The link expires in 2 hours.
        </p>
        <p class="sent-hint">
          Didn't receive an SMS? Your phone number may not be on record.
          Contact your school administrator to update it or resend the link.
        </p>
      </div>
    {:else}
      <div class="form-heading">
        <p class="form-title">Reset your password</p>
        <p class="form-sub">Enter your account email. A reset link will be sent via SMS to the phone number registered with your account.</p>
      </div>

      <form on:submit={handleSubmit} novalidate>
        {#if error}
          <p class="error-msg" role="alert">{error}</p>
        {/if}

        <div class="field">
          <label for="email">Email address</label>
          <input
            id="email"
            type="email"
            bind:value={email}
            required
            autocomplete="email"
            placeholder="you@school.edu.gh"
          />
        </div>

        <button type="submit" class="submit" disabled={loading} style="background:{accentColor}">
          {#if loading}
            <Loader2 size={15} class="spin" /> Sending…
          {:else}
            Send reset link
          {/if}
        </button>
      </form>
    {/if}

    <a href="/login" class="back-link">
      <ArrowLeft size={13} /> Back to sign in
    </a>

  </div>
</div>

<style>
  .shell {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg);
    padding: 24px;
  }

  .card {
    width: 100%;
    max-width: 380px;
    background: var(--surface-0);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 36px 32px 28px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.07);
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .identity {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 10px;
  }

  .logo-img {
    width: 60px; height: 60px;
    object-fit: contain;
    border-radius: 12px;
    border: 1px solid var(--border-subtle);
  }

  .logo-initial {
    width: 60px; height: 60px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    font-weight: 800;
    color: #fff;
  }

  .school-name {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: var(--tx-high);
  }

  .divider {
    height: 1px;
    background: var(--border-subtle);
  }

  .form-heading { display: flex; flex-direction: column; gap: 4px; }

  .form-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: var(--tx-high);
  }

  .form-sub {
    margin: 0;
    font-size: 0.8125rem;
    color: var(--tx-low);
  }

  .error-msg {
    margin: 0;
    font-size: 0.8125rem;
    color: #ef4444;
    background: color-mix(in srgb, #ef4444 8%, transparent);
    border: 1px solid color-mix(in srgb, #ef4444 20%, transparent);
    border-radius: 8px;
    padding: 9px 12px;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .field label {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--tx-mid);
  }

  .field input {
    height: 40px;
    padding: 0 12px;
    border-radius: 8px;
    border: 1.5px solid var(--border-subtle);
    background: var(--surface-1);
    font-size: 0.9rem;
    color: var(--tx-high);
    outline: none;
    width: 100%;
    box-sizing: border-box;
    transition: border-color 0.14s, box-shadow 0.14s;
  }

  .field input::placeholder { color: var(--tx-low); }

  .field input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 14%, transparent);
    background: var(--surface-0);
  }

  .submit {
    height: 42px;
    border: none;
    border-radius: 8px;
    color: #fff;
    font-size: 0.9375rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    transition: filter 0.14s, opacity 0.14s;
  }

  .submit:hover:not(:disabled) { filter: brightness(1.1); }
  .submit:disabled { opacity: 0.6; cursor: not-allowed; }

  /* Success state */
  .sent-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 10px;
    padding: 8px 0;
  }

  .sent-icon {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
  }

  .sent-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: var(--tx-high);
  }

  .sent-body {
    margin: 0;
    font-size: 0.8125rem;
    color: var(--tx-low);
    line-height: 1.55;
  }

  .sent-hint {
    margin: 0;
    font-size: 0.75rem;
    color: var(--tx-low);
    line-height: 1.5;
    padding: 10px 12px;
    border-radius: 8px;
    background: var(--surface-2);
    border: 1px solid var(--border-subtle);
  }

  /* Back link */
  .back-link {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    font-size: 0.8125rem;
    color: var(--tx-low);
    text-decoration: none;
    transition: color 0.12s;
  }

  .back-link:hover { color: var(--tx-mid); }

  :global(.spin) { animation: spin 0.75s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
