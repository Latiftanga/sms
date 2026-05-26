<script lang="ts">
  import { auth } from "$stores/auth";
  import { goto } from "$app/navigation";

  let email = "";
  let password = "";
  let loading = false;
  let error = "";

  async function handleLogin(e: SubmitEvent) {
    e.preventDefault();
    error = "";
    loading = true;
    try {
      await auth.login(email, password);
      await goto("/dashboard");
    } catch {
      error = $auth.error ?? "Login failed. Please try again.";
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Sign in — TTEK-SIS</title>
</svelte:head>

<div class="flex min-h-screen flex-col items-center justify-center bg-neutral-950 px-4">
  <div class="w-full max-w-sm">
    <!-- Logo -->
    <div class="mb-8 text-center">
      <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-lg font-bold text-white">
        TS
      </div>
      <h1 class="text-2xl font-bold tracking-tight text-white">TTEK-SIS</h1>
      <p class="mt-1 text-sm text-neutral-400">Sign in to your school account</p>
    </div>

    <!-- Form -->
    <form on:submit={handleLogin} class="space-y-4">
      {#if error}
        <div class="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      {/if}

      <div>
        <label for="email" class="mb-1.5 block text-sm font-medium text-neutral-300">
          Email address
        </label>
        <input
          id="email"
          type="email"
          bind:value={email}
          required
          autocomplete="email"
          class="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-3 text-base text-white placeholder-neutral-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          placeholder="you@school.edu.gh"
        />
      </div>

      <div>
        <label for="password" class="mb-1.5 block text-sm font-medium text-neutral-300">
          Password
        </label>
        <input
          id="password"
          type="password"
          bind:value={password}
          required
          autocomplete="current-password"
          class="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-3 text-base text-white placeholder-neutral-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          placeholder="••••••••"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        class="w-full rounded-lg bg-blue-600 px-4 py-3 text-base font-semibold text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {#if loading}
          <span class="inline-flex items-center gap-2">
            <span class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
            Signing in…
          </span>
        {:else}
          Sign in
        {/if}
      </button>
    </form>
  </div>
</div>
