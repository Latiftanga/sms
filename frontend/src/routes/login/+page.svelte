<script lang="ts">
  import { auth } from "$stores/auth";
  import { schoolBranding } from "$stores/school";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { Loader2, Eye, EyeOff, Sun, Moon, Monitor } from "@lucide/svelte";

  let email = "";
  let password = "";
  let loading = false;
  let error = "";
  let showPassword = false;

  // ── Theme ──────────────────────────────────────────────────────
  type ThemeMode = "light" | "dark" | "system";
  let themeMode: ThemeMode = "system";
  let systemDark = false;

  onMount(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    systemDark = mq.matches;
    const handler = (e: MediaQueryListEvent) => { systemDark = e.matches; };
    mq.addEventListener("change", handler);

    const saved = localStorage.getItem("sis-theme") as ThemeMode | null;
    themeMode = saved ?? "system";

    return () => mq.removeEventListener("change", handler);
  });

  $: isDark = themeMode === "dark" || (themeMode === "system" && systemDark);
  $: if (typeof document !== "undefined") {
    document.documentElement.classList.toggle("dark", isDark);
  }

  function cycleTheme() {
    const cycle: ThemeMode[] = ["light", "dark", "system"];
    themeMode = cycle[(cycle.indexOf(themeMode) + 1) % cycle.length];
    localStorage.setItem("sis-theme", themeMode);
  }

  $: themeLabel = themeMode === "dark" ? "Dark" : themeMode === "light" ? "Light" : "System";

  // ── Login ──────────────────────────────────────────────────────
  async function handleLogin(e: SubmitEvent) {
    e.preventDefault();
    error = "";
    if (!email.trim()) { error = "Email address is required."; return; }
    if (!password)     { error = "Password is required."; return; }
    loading = true;
    try {
      await auth.login(email, password);
      const user = $auth.user;
      await goto(user?.must_change_password ? "/change-password" : "/dashboard");
    } catch {
      error = $auth.error ?? "Invalid email or password.";
    } finally {
      loading = false;
    }
  }

  $: accentColor = $schoolBranding?.accent_color ?? "#185FA5";
  $: schoolName  = $schoolBranding?.name ?? "School Information System";
  $: schoolMotto = $schoolBranding?.motto ?? null;
  $: logoUrl     = $schoolBranding?.logo_url ?? null;
</script>

<svelte:head>
  <title>Sign in — {schoolName}</title>
</svelte:head>

<div class="shell">
  <!-- Theme toggle -->
  <button class="theme-btn" on:click={cycleTheme} title="Theme: {themeLabel}" aria-label="Switch theme ({themeLabel})">
    {#if themeMode === "light"}<Sun size={14} />
    {:else if themeMode === "dark"}<Moon size={14} />
    {:else}<Monitor size={14} />{/if}
    <span class="theme-label">{themeLabel}</span>
  </button>

  <div class="card">

    <!-- School identity -->
    <div class="identity">
      {#if logoUrl}
        <img src={logoUrl} alt="{schoolName} logo" class="logo-img" />
      {:else}
        <div class="logo-initial" style="background:{accentColor}">
          {schoolName.charAt(0).toUpperCase()}
        </div>
      {/if}
      <h1 class="school-name">{schoolName}</h1>
      {#if schoolMotto}
        <p class="motto">"{schoolMotto}"</p>
      {/if}
    </div>

    <div class="divider"></div>

    <!-- Form -->
    <form on:submit={handleLogin} novalidate>

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
          class:invalid={!!error}
        />
      </div>

      <div class="field">
        <label for="password">Password</label>
        <div class="pw-wrap">
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            bind:value={password}
            required
            autocomplete="current-password"
            placeholder="••••••••"
            class:invalid={!!error}
          />
          <button
            type="button"
            class="pw-toggle"
            on:click={() => showPassword = !showPassword}
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {#if showPassword}<EyeOff size={14} />{:else}<Eye size={14} />{/if}
          </button>
        </div>
      </div>

      <button type="submit" class="submit" disabled={loading} style="background:{accentColor}">
        {#if loading}
          <Loader2 size={15} class="spin" /> Signing in…
        {:else}
          Sign in
        {/if}
      </button>

      <a href="/forgot-password" class="forgot-link">Forgot password?</a>

    </form>
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
    position: relative;
  }

  /* Theme toggle — top-right corner */
  .theme-btn {
    position: fixed;
    top: 16px;
    right: 16px;
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 6px 10px;
    border-radius: 8px;
    border: 1px solid var(--border-subtle);
    background: var(--surface-0);
    color: var(--tx-mid);
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.12s, border-color 0.12s, color 0.12s;
    z-index: 10;
  }

  .theme-btn:hover {
    background: var(--surface-1);
    color: var(--tx-high);
    border-color: var(--border-strong);
  }

  .theme-label { line-height: 1; }

  .card {
    width: 100%;
    max-width: 380px;
    background: var(--surface-0);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 36px 32px 32px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.07);
  }

  /* Identity block */
  .identity {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 10px;
    margin-bottom: 24px;
  }

  .logo-img {
    width: 72px;
    height: 72px;
    object-fit: contain;
    border-radius: 14px;
    border: 1px solid var(--border-subtle);
  }

  .logo-initial {
    width: 72px;
    height: 72px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    font-weight: 800;
    color: #fff;
    letter-spacing: -1px;
  }

  .school-name {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--tx-high);
    line-height: 1.25;
  }

  .motto {
    margin: 0;
    font-size: 0.775rem;
    color: var(--tx-low);
    font-style: italic;
    line-height: 1.4;
  }

  .divider {
    height: 1px;
    background: var(--border-subtle);
    margin-bottom: 24px;
  }

  /* Form */
  form {
    display: flex;
    flex-direction: column;
    gap: 16px;
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
    transition: border-color 0.14s, box-shadow 0.14s;
    width: 100%;
    box-sizing: border-box;
  }

  .field input::placeholder { color: var(--tx-low); }

  .field input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 14%, transparent);
    background: var(--surface-0);
  }

  .field input.invalid {
    border-color: color-mix(in srgb, #ef4444 50%, transparent);
  }

  /* Password row */
  .pw-wrap { position: relative; }

  .pw-wrap input { padding-right: 40px; }

  .pw-toggle {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    cursor: pointer;
    color: var(--tx-low);
    display: flex;
    align-items: center;
    padding: 0;
    transition: color 0.12s;
  }

  .pw-toggle:hover { color: var(--tx-mid); }

  /* Submit */
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
    margin-top: 4px;
    transition: filter 0.14s, opacity 0.14s;
  }

  .submit:hover:not(:disabled) { filter: brightness(1.1); }
  .submit:disabled { opacity: 0.6; cursor: not-allowed; }

  .forgot-link {
    display: block;
    text-align: center;
    font-size: 0.8125rem;
    color: var(--tx-low);
    text-decoration: none;
    transition: color 0.12s;
  }

  .forgot-link:hover { color: var(--accent); }

  :global(.spin) { animation: spin 0.75s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
