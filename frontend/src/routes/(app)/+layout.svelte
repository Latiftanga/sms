<script lang="ts">
  import { goto } from "$app/navigation";
  import { page, navigating } from "$app/stores";
  import { auth, isAuthenticated, currentUser } from "$stores/auth";
  import { schoolBranding } from "$stores/school";
  import { Avatar, Toaster, ConfirmDialog } from "$components";
  import { PanelLeft, Bell, Sun, Moon, Monitor, LogOut, Settings } from "@lucide/svelte";
  import { onMount } from "svelte";
  import { NAV, type NavGroup } from "$lib/config/nav";

  // ── Sidebar state ──────────────────────────────────────────────
  let collapsed = false;
  let mobile = false;
  let mobileOpen = false;
  let logoFailed = false;
  $: if ($schoolBranding?.logo_url) logoFailed = false;

  // ── Theme ──────────────────────────────────────────────────────
  type ThemeMode = "light" | "dark" | "system";
  let themeMode: ThemeMode = "system";
  let systemDark = false;

  const MOBILE_BP = 768;

  function onResize() {
    const wasMobile = mobile;
    mobile = window.innerWidth < MOBILE_BP;
    if (mobile && !wasMobile) mobileOpen = false;
    if (!mobile && wasMobile) mobileOpen = false;
  }

  function toggleSidebar() {
    if (mobile) mobileOpen = !mobileOpen;
    else collapsed = !collapsed;
  }

  onMount(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    systemDark = mq.matches;
    const handler = (e: MediaQueryListEvent) => { systemDark = e.matches; };
    mq.addEventListener("change", handler);

    const saved = localStorage.getItem("sis-theme") as ThemeMode | null;
    themeMode = saved ?? "system";

    const savedAccent = localStorage.getItem("sis-accent");
    if (savedAccent) applyAccent(savedAccent);

    onResize();
    window.addEventListener("resize", onResize);
    return () => {
      mq.removeEventListener("change", handler);
      window.removeEventListener("resize", onResize);
    };
  });

  $: isDark = themeMode === "dark" || (themeMode === "system" && systemDark);
  $: if (typeof document !== "undefined") {
    document.documentElement.classList.toggle("dark", isDark);
  }

  function toggleTheme() {
    const cycle: ThemeMode[] = ["light", "dark", "system"];
    themeMode = cycle[(cycle.indexOf(themeMode) + 1) % cycle.length];
    localStorage.setItem("sis-theme", themeMode);
  }

  $: themeIcon  = themeMode === "dark" ? "moon" : themeMode === "light" ? "sun" : "system";
  $: themeLabel = themeMode === "dark" ? "Dark" : themeMode === "light" ? "Light" : "System";

  function applyAccent(hex: string) {
    document.documentElement.style.setProperty("--accent", hex);
  }

  async function handleLogout() {
    await auth.logout();
    goto("/login");
  }

  // ── Routing ────────────────────────────────────────────────────
  $: currentPath = $page.url.pathname;
  function active(path: string) {
    return currentPath === path || currentPath.startsWith(path + "/");
  }
  $: pageTitle = currentPath.split("/").filter(Boolean)[0]?.replace(/-/g, " ") ?? "Dashboard";

  // ── Auth guards ────────────────────────────────────────────────
  $: isSuperAdmin = $currentUser?.system_role === "SUPERADMIN";

  $: if (!$auth.loading && !$isAuthenticated) goto("/login");
  $: if (!$auth.loading && $auth.user?.must_change_password) goto("/change-password");

  // ── Dynamic nav ────────────────────────────────────────────────
  // Permissions are a flat Record<string, boolean> from /auth/me.
  // canSee returns true when the user holds ANY of the listed keys,
  // or when no keys are required (always-visible items like Dashboard).
  // SUPERADMIN bypasses all checks.
  $: perms = ($currentUser?.permissions ?? {}) as Record<string, boolean>;

  // Rebuild visible groups whenever permissions or role changes.
  // Groups with zero visible items are dropped entirely (no phantom dividers).
  // Inlined (not a helper fn) so Svelte tracks perms + isSuperAdmin as dependencies.
  $: visibleGroups = NAV
    .map((group: NavGroup) => ({
      ...group,
      items: group.items.filter(item => {
        if (isSuperAdmin) return true;
        if (!item.anyPermission?.length) return true;
        return item.anyPermission.some(k => perms[k] === true);
      }),
    }))
    .filter(group => group.items.length > 0);

  // ── Sidebar dimensions ─────────────────────────────────────────
  $: sidebarStyle = mobile
    ? `position:fixed;top:var(--topbar-h);left:0;height:calc(100% - var(--topbar-h));width:var(--sidebar-w);transform:translateX(${mobileOpen ? "0" : "-100%"});transition:transform 0.22s ease;z-index:50;`
    : `position:relative;width:${collapsed ? "54px" : "var(--sidebar-w)"};transition:width 0.2s ease;z-index:20;`;

  $: userName = $currentUser?.full_name || $currentUser?.email?.split("@")[0] || "—";
  $: userRole = $currentUser?.system_role ?? "—";
</script>

<div class="app-shell">

  {#if $navigating}
    <div class="nav-bar"></div>
  {/if}

  <!-- ── Full-bleed topbar (content constrained to max-width) ── -->
  <header class="topbar">
    <div class="topbar-inner">
      <button class="topbar-btn" on:click={toggleSidebar} aria-label="Toggle sidebar">
        <PanelLeft size={14} />
      </button>

      <div class="topbar-divider"></div>

      <span class="page-title">{pageTitle}</span>

      <div class="topbar-spacer"></div>

      <button class="topbar-btn" aria-label="Notifications">
        <Bell size={14} />
        <span class="notif-dot"></span>
      </button>

      <button class="topbar-btn" on:click={toggleTheme} aria-label={themeLabel} title={themeLabel}>
        {#if themeIcon === "sun"}<Sun size={14} />
        {:else if themeIcon === "moon"}<Moon size={14} />
        {:else}<Monitor size={14} />{/if}
      </button>
    </div>
  </header>

  <!-- ── App body: sidebar + content ─────────────────────────── -->
  <div class="app-body">

    <!-- Mobile backdrop -->
    {#if mobile && mobileOpen}
      <div
        class="mobile-backdrop"
        role="button"
        tabindex="-1"
        aria-label="Close sidebar"
        on:click={() => mobileOpen = false}
        on:keydown={(e) => e.key === "Escape" && (mobileOpen = false)}
      ></div>
    {/if}

    <!-- Sidebar -->
    <aside class="sidebar" class:collapsed={collapsed && !mobile} style={sidebarStyle}>

      <!-- Brand header -->
      <div class="sidebar-header">
        <div class="brand-icon">
          {#if $schoolBranding?.logo_url && !logoFailed}
            <img src={$schoolBranding.logo_url} alt="School logo" class="sidebar-logo-img"
              on:error={() => logoFailed = true} />
          {:else}
            {($schoolBranding?.name ?? "T").charAt(0).toUpperCase()}
          {/if}
        </div>
        {#if !collapsed || mobile}
          <div class="brand-name">
            <div class="brand-title">{$schoolBranding?.name ?? "TTEK-SMS"}</div>
            <div class="brand-sub">School Management</div>
          </div>
        {/if}
      </div>

      <!-- Nav — rendered from $lib/config/nav.ts, filtered by user permissions -->
      <!-- svelte-ignore a11y-click-events-have-key-events -->
      <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
      <nav class="sidebar-nav" on:click={() => { if (mobile) mobileOpen = false; }}>

        {#each visibleGroups as group, gi}
          {#if gi > 0}
            <div class="nav-divider"></div>
          {/if}

          <div class="nav-group">
            {#each group.items as item (item.href)}
              <a href={item.href} class="nav-item" class:active={active(item.href)}>
                <svelte:component
                  this={item.icon}
                  size={15}
                  style="flex-shrink:0; opacity:{active(item.href) ? '1' : '.6'}"
                />
                {#if !collapsed || mobile}<span>{item.label}</span>{/if}
              </a>
            {/each}
          </div>
        {/each}

      </nav>

      <!-- User footer -->
      <div class="sidebar-footer">
        <a href="/profile" class="user-card" class:active={active("/profile")}>
          <Avatar name={$currentUser?.email ?? "U"} size="sm" />
          {#if !collapsed || mobile}
            <div class="user-info">
              <div class="user-name">{userName}</div>
              <div class="user-role">{userRole}</div>
            </div>
          {/if}
        </a>
        {#if !collapsed || mobile}
          <div class="footer-actions">
            <button class="footer-btn" on:click={handleLogout} aria-label="Sign out" title="Sign out">
              <LogOut size={14} />
            </button>
          </div>
        {/if}
      </div>

    </aside>

    <!-- Page content -->
    <main class="page-content">
      <slot />
    </main>

  </div>
</div>

<Toaster />
<ConfirmDialog />

<style>
  /* ── Shell ───────────────────────────────────────────────────── */
  .app-shell {
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--bg);
  }

  /* App body sits below the topbar, constrained to same max-width */
  .app-body {
    flex: 1;
    display: flex;
    overflow: hidden;
    position: relative;
    max-width: 1280px;
    width: 100%;
    margin: 0 auto;
  }

  .mobile-backdrop {
    position: fixed;
    top: var(--topbar-h);
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.45);
    z-index: 49;
  }

  /* ── Sidebar static styles (dynamic positional come from style={}) ── */
  .sidebar {
    background: var(--surface-0);
    border-right: 1px solid var(--border-subtle);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    flex-shrink: 0;
  }

  /* Brand header */
  .sidebar-header {
    padding: 12px 12px 10px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid var(--border-subtle);
    flex-shrink: 0;
    overflow: hidden;
  }

  .sidebar.collapsed .sidebar-header {
    justify-content: center;
    padding: 0;
  }

  .brand-icon {
    width: 27px;
    height: 27px;
    border-radius: 7px;
    background: var(--accent);
    color: var(--accent-fg);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 12px;
    flex-shrink: 0;
  }

  .sidebar-logo-img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    border-radius: 5px;
  }

  .brand-name { overflow: hidden; white-space: nowrap; }
  .brand-title { font-size: 13px; font-weight: 700; color: var(--tx-high); }
  .brand-sub   { font-size: 10px; color: var(--tx-low); margin-top: 1px; }

  /* Nav */
  .sidebar-nav {
    flex: 1;
    overflow-y: auto;
    padding: 6px 6px 4px;
    scrollbar-width: none;
  }
  .sidebar-nav::-webkit-scrollbar { display: none; }

  .nav-group { display: flex; flex-direction: column; }

  .nav-divider {
    height: 1px;
    background: var(--border-subtle);
    margin: 5px 10px;
    flex-shrink: 0;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 7px;
    color: var(--tx-mid);
    font-size: 13px;
    font-weight: 400;
    text-decoration: none;
    white-space: nowrap;
    overflow: hidden;
    transition: background 0.12s, color 0.12s, box-shadow 0.12s;
  }

  .nav-item:hover {
    background: var(--accent-subtle);
    color: var(--tx-high);
  }

  .nav-item.active {
    background: var(--accent-subtle);
    color: var(--accent);
    font-weight: 500;
    box-shadow: inset 3px 0 0 var(--accent);
  }

  .sidebar.collapsed .nav-item {
    padding: 7px 0;
    justify-content: center;
  }

  .sidebar.collapsed .nav-item.active {
    box-shadow: none;
  }

  .sidebar.collapsed .nav-divider {
    margin: 5px 8px;
  }

  /* Sidebar user footer */
  .sidebar-footer {
    border-top: 1px solid var(--border-subtle);
    padding: 8px 8px 8px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .user-card {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 5px 6px;
    border-radius: 8px;
    overflow: hidden;
    text-decoration: none;
    transition: background 0.12s;
  }

  .user-card:hover {
    background: var(--accent-subtle);
  }

  .user-card.active {
    background: var(--accent-subtle);
    outline: 1.5px solid color-mix(in srgb, var(--accent) 30%, transparent);
  }

  .sidebar.collapsed .user-card {
    justify-content: center;
    padding: 5px 0;
    flex: unset;
    width: 100%;
  }

  .user-info {
    flex: 1;
    min-width: 0;
    overflow: hidden;
  }

  .user-name {
    font-size: 12px;
    font-weight: 500;
    color: var(--tx-mid);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .user-role {
    font-size: 10px;
    color: var(--tx-low);
    margin-top: 1px;
    white-space: nowrap;
    text-transform: lowercase;
  }

  .footer-actions {
    display: flex;
    align-items: center;
    gap: 2px;
    flex-shrink: 0;
  }

  .footer-btn {
    width: 28px;
    height: 28px;
    border-radius: 7px;
    border: 1px solid transparent;
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--tx-low);
    cursor: pointer;
    flex-shrink: 0;
    transition: background 0.12s, color 0.12s, border-color 0.12s;
  }

  .footer-btn:hover {
    background: color-mix(in srgb, #ef4444 12%, transparent);
    border-color: color-mix(in srgb, #ef4444 25%, transparent);
    color: #ef4444;
  }

  /* ── Topbar — full-bleed background, constrained content ────── */
  .topbar {
    width: 100%;
    height: var(--topbar-h);
    flex-shrink: 0;
    background: var(--surface-0);
    border-bottom: 1px solid var(--border-subtle);
    z-index: 40;
  }

  .topbar-inner {
    max-width: 1280px;
    margin: 0 auto;
    height: 100%;
    padding: 0 18px 0 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .topbar-btn {
    width: 30px;
    height: 30px;
    border-radius: 7px;
    border: 1px solid var(--border-subtle);
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--tx-mid);
    cursor: pointer;
    position: relative;
    transition: background 0.12s, color 0.12s, border-color 0.12s;
  }

  .topbar-btn:hover {
    background: var(--accent-subtle);
    border-color: color-mix(in srgb, var(--accent) 30%, var(--border-subtle));
    color: var(--tx-high);
  }

  .topbar-divider {
    width: 1px;
    height: 16px;
    background: var(--border-strong);
    flex-shrink: 0;
  }

  .topbar-spacer { flex: 1; }

  .page-title {
    font-size: 13px;
    font-weight: 500;
    color: var(--tx-high);
    text-transform: capitalize;
  }

  .notif-dot {
    position: absolute;
    top: 6px;
    right: 6px;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--accent);
    border: 1.5px solid var(--surface-0);
  }

  /* Page content — fills remaining width next to sidebar */
  .page-content {
    flex: 1;
    min-width: 0;
    overflow-y: auto;
    padding: 24px 28px;
  }

  /* ── Navigation progress bar ────────────────── */
  .nav-bar {
    position: fixed;
    top: 0; left: 0;
    height: 2px;
    width: 100%;
    z-index: 9999;
    background: var(--accent);
    transform-origin: left;
    animation: nav-progress 8s cubic-bezier(0.1, 0.05, 0, 1) forwards;
  }
  @keyframes nav-progress {
    0%   { transform: scaleX(0); }
    40%  { transform: scaleX(0.6); }
    80%  { transform: scaleX(0.85); }
    100% { transform: scaleX(0.95); }
  }
</style>
