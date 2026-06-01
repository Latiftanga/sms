<script lang="ts">
  import { auth } from "$stores/auth";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { schoolBranding } from "$stores/school";
  import { LogOut, Building2, Users2, Settings2, BarChart3 } from "@lucide/svelte";

  // Redirect non-superadmins away from this page
  onMount(() => {
    if ($auth.user && $auth.user.system_role !== "SUPERADMIN") {
      goto("/dashboard");
    }
  });

  async function handleLogout() {
    await auth.logout();
    goto("/login");
  }

  const COMING_SOON = [
    { icon: Building2, label: "Schools",      desc: "Manage registered schools, subscriptions and settings" },
    { icon: Users2,    label: "Users",         desc: "Platform-level user management and access control"     },
    { icon: BarChart3, label: "Analytics",     desc: "Platform-wide usage metrics and school health"         },
    { icon: Settings2, label: "Configuration", desc: "Global defaults, feature flags and billing"            },
  ];
</script>

<svelte:head>
  <title>Platform Administration — {$schoolBranding?.name ?? 'TTEK-SMS'}</title>
</svelte:head>

<div class="shell">

  <header class="topbar">
    <div class="brand">
      <div class="brand-mark">T</div>
      <span class="brand-name">TTEK-SMS Platform</span>
    </div>
    <button class="logout-btn" on:click={handleLogout} title="Sign out">
      <LogOut size={14} />
      Sign out
    </button>
  </header>

  <main class="content">
    <div class="hero">
      <div class="hero-badge">Platform Administration</div>
      <h1 class="hero-title">Platform dashboard coming soon</h1>
      <p class="hero-sub">
        You're signed in as a platform administrator. The school management
        console for managing registered schools, users, and subscriptions
        is being built and will be available here.
      </p>
    </div>

    <div class="cards">
      {#each COMING_SOON as item}
        <div class="card">
          <div class="card-icon">
            <svelte:component this={item.icon} size={18} />
          </div>
          <div class="card-body">
            <p class="card-label">{item.label}</p>
            <p class="card-desc">{item.desc}</p>
          </div>
          <span class="card-chip">Coming soon</span>
        </div>
      {/each}
    </div>
  </main>

</div>

<style>
  .shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--bg, #F2F0EC);
  }

  /* ── Topbar ───────────────────────────────────────────────────────── */
  .topbar {
    height: 52px;
    background: var(--surface-0, #F8F6F1);
    border-bottom: 1px solid var(--border-subtle, #E6E3DC);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 28px;
    flex-shrink: 0;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .brand-mark {
    width: 28px;
    height: 28px;
    border-radius: 7px;
    background: var(--accent, #185FA5);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
  }

  .brand-name {
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--tx-high, #1A1917);
  }

  .logout-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 7px;
    border: 1px solid var(--border-subtle, #E6E3DC);
    background: transparent;
    color: var(--tx-low, #96938B);
    font-size: 0.8125rem;
    cursor: pointer;
    transition: background 0.12s, color 0.12s;
  }
  .logout-btn:hover {
    background: color-mix(in srgb, #ef4444 10%, transparent);
    color: #ef4444;
    border-color: color-mix(in srgb, #ef4444 25%, transparent);
  }

  /* ── Content ──────────────────────────────────────────────────────── */
  .content {
    flex: 1;
    max-width: 680px;
    margin: 0 auto;
    padding: 64px 24px;
    display: flex;
    flex-direction: column;
    gap: 40px;
    width: 100%;
  }

  /* ── Hero ─────────────────────────────────────────────────────────── */
  .hero {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .hero-badge {
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    background: var(--accent-subtle, color-mix(in srgb, #185FA5 10%, #fff));
    color: var(--accent, #185FA5);
    border: 1px solid var(--accent-border, color-mix(in srgb, #185FA5 20%, #fff));
    width: fit-content;
  }

  .hero-title {
    margin: 0;
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--tx-high, #1A1917);
    line-height: 1.2;
  }

  .hero-sub {
    margin: 0;
    font-size: 0.9375rem;
    color: var(--tx-low, #96938B);
    line-height: 1.6;
    max-width: 520px;
  }

  /* ── Cards ────────────────────────────────────────────────────────── */
  .cards {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 18px;
    background: var(--surface-1, #FEFCF8);
    border: 1px solid var(--border-subtle, #E6E3DC);
    border-radius: 12px;
  }

  .card-icon {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: var(--surface-2, #F3F1EC);
    color: var(--tx-low, #96938B);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .card-body {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .card-label {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--tx-high, #1A1917);
  }

  .card-desc {
    margin: 0;
    font-size: 0.8125rem;
    color: var(--tx-low, #96938B);
  }

  .card-chip {
    font-size: 0.6875rem;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 99px;
    background: var(--surface-2, #F3F1EC);
    color: var(--tx-low, #96938B);
    border: 1px solid var(--border-subtle, #E6E3DC);
    white-space: nowrap;
    flex-shrink: 0;
  }
</style>
