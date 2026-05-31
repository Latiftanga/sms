<script lang="ts">
  import { auth, currentUser } from "$stores/auth";
  import { api } from "$api/client";
  import { Mail, ShieldCheck, Eye, EyeOff, Loader2, AlertCircle, CheckCircle2, KeyRound } from "@lucide/svelte";

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
      setTimeout(() => { pwSuccess = false; }, 5000);
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

  $: displayName = $currentUser?.full_name || $currentUser?.email?.split("@")[0] || "—";
  $: initials = displayName.split(" ").filter(Boolean).map((w: string) => w[0]).join("").toUpperCase().slice(0, 2) || "?";
  $: roleLabel = $currentUser?.system_role?.replace(/_/g, " ") ?? "—";
</script>

<svelte:head><title>My Profile — TTEK-SIS</title></svelte:head>

<div class="page">

  <!-- ── Hero card ─────────────────────────────────── -->
  <div class="hero-card">
    <div class="hero-banner"></div>
    <div class="hero-body">
      <div class="hero-avatar">
        <span class="avatar-initials">{initials}</span>
      </div>
      <h1 class="hero-name">{displayName}</h1>
      <span class="hero-badge">{roleLabel}</span>
    </div>
  </div>

  <!-- ── Two-column grid ───────────────────────────── -->
  <div class="grid">

    <!-- Account info -->
    <div class="card">
      <div class="card-head">
        <span class="card-label">Account</span>
      </div>
      <div class="info-list">
        <div class="info-row">
          <div class="info-icon"><Mail size={13} /></div>
          <div class="info-body">
            <span class="info-label">Email</span>
            <span class="info-val">{$currentUser?.email ?? "—"}</span>
          </div>
        </div>
        <div class="info-row">
          <div class="info-icon"><ShieldCheck size={13} /></div>
          <div class="info-body">
            <span class="info-label">Access level</span>
            <span class="info-val">{roleLabel}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Change password -->
    <div class="card">
      <div class="card-head">
        <KeyRound size={13} class="card-head-icon" />
        <span class="card-label">Change password</span>
      </div>

      {#if pwError}
        <div class="alert err"><AlertCircle size={13} />{pwError}</div>
      {/if}
      {#if pwSuccess}
        <div class="alert ok"><CheckCircle2 size={13} />Password updated.</div>
      {/if}

      <form on:submit|preventDefault={changePassword} novalidate>
        <div class="form-stack">

          <div class="field">
            <label for="cur">Current password</label>
            <div class="pw">
              <input id="cur" class="input" type={showCurrent ? "text" : "password"}
                bind:value={current} autocomplete="current-password" placeholder="••••••••" />
              <button type="button" class="eye" on:click={() => showCurrent = !showCurrent}>
                {#if showCurrent}<EyeOff size={13} />{:else}<Eye size={13} />{/if}
              </button>
            </div>
          </div>

          <div class="field">
            <label for="nxt">New password</label>
            <div class="pw">
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
          <button class="btn" type="submit" disabled={saving}>
            {#if saving}<Loader2 size={13} class="spin" />{/if}
            Update password
          </button>
        </div>
      </form>
    </div>

  </div>
</div>

<style>
  .page {
    max-width: 720px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  /* ── Hero ── */
  .hero-card {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid var(--border-subtle);
    box-shadow: var(--shadow-sm);
  }

  .hero-banner {
    height: 80px;
    background: linear-gradient(
      135deg,
      color-mix(in srgb, var(--accent) 22%, var(--surface-1)) 0%,
      color-mix(in srgb, var(--accent) 10%, var(--surface-1)) 60%,
      var(--surface-1) 100%
    );
  }

  .hero-body {
    background: var(--surface-1);
    padding: 0 24px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-top: -32px;
  }

  .hero-avatar {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: var(--accent);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.375rem;
    font-weight: 700;
    border: 3px solid var(--surface-1);
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    flex-shrink: 0;
    letter-spacing: -0.5px;
  }

  .hero-name {
    margin: 12px 0 0;
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--tx-high);
    line-height: 1.2;
  }

  .hero-badge {
    margin-top: 6px;
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: var(--accent-subtle);
    color: var(--accent);
    border: 1px solid var(--accent-border);
  }

  /* ── Grid ── */
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    align-items: start;
  }

  @media (max-width: 560px) {
    .grid { grid-template-columns: 1fr; }
  }

  /* ── Cards ── */
  .card {
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--shadow-xs);
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .card-head {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 13px 16px 12px;
    border-bottom: 1px solid var(--border-subtle);
    background: var(--surface-2);
  }

  :global(.card-head-icon) { color: var(--tx-low); }

  .card-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--tx-low);
  }

  /* ── Info list ── */
  .info-list {
    display: flex;
    flex-direction: column;
  }

  .info-row {
    display: flex;
    align-items: flex-start;
    gap: 11px;
    padding: 13px 16px;
  }
  .info-row + .info-row {
    border-top: 1px solid var(--border-subtle);
  }

  .info-icon {
    width: 26px;
    height: 26px;
    border-radius: 7px;
    background: var(--accent-subtle);
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 1px;
  }

  .info-body {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .info-label {
    font-size: 0.6875rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--tx-low);
  }

  .info-val {
    font-size: 0.875rem;
    color: var(--tx-high);
    font-weight: 450;
    word-break: break-all;
  }

  /* ── Alerts ── */
  .alert {
    margin: 12px 16px 0;
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 8px 11px;
    border-radius: 8px;
    font-size: 0.8125rem;
  }
  .alert.err {
    color: #ef4444;
    background: color-mix(in srgb, #ef4444 8%, transparent);
    border: 1px solid color-mix(in srgb, #ef4444 20%, transparent);
  }
  .alert.ok {
    color: #10b981;
    background: color-mix(in srgb, #10b981 10%, transparent);
    border: 1px solid color-mix(in srgb, #10b981 25%, transparent);
  }

  /* ── Form ── */
  form {
    padding: 14px 16px 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .form-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .field label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--tx-mid);
  }

  .pw { position: relative; }
  .pw .input { padding-right: 34px; }

  .eye {
    position: absolute; right: 9px; top: 50%; transform: translateY(-50%);
    background: none; border: none; cursor: pointer;
    color: var(--tx-low); padding: 0; display: flex; align-items: center;
  }
  .eye:hover { color: var(--tx-mid); }

  .input {
    width: 100%; box-sizing: border-box;
    height: 34px; padding: 0 11px;
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
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 13%, transparent);
    background: var(--surface-1);
  }
  .input::placeholder { color: var(--tx-placeholder); }

  .bar {
    height: 2px; background: var(--border-subtle);
    border-radius: 99px; overflow: hidden; margin-top: 5px;
  }
  .bar-fill { height: 100%; border-radius: 99px; transition: width 0.3s, background 0.3s; }
  .bar-label { font-size: 0.6875rem; font-weight: 500; margin-top: 2px; }

  .form-foot { display: flex; justify-content: flex-end; }

  .btn {
    height: 32px; padding: 0 14px;
    border-radius: 7px; border: none; cursor: pointer;
    background: var(--accent); color: #fff;
    font-size: 0.8125rem; font-weight: 600; font-family: inherit;
    display: flex; align-items: center; gap: 6px;
    transition: opacity 0.12s;
  }
  .btn:hover:not(:disabled) { opacity: 0.88; }
  .btn:disabled { opacity: 0.55; cursor: not-allowed; }

  :global(.spin) { animation: spin 0.7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
