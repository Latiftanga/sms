<script lang="ts">
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { auth, isAuthenticated, currentUser } from "$stores/auth";
  import { schoolBranding } from "$stores/school";
  import { Avatar, Toaster, ConfirmDialog } from "$components";
  import {
    LayoutDashboard, Users, ClipboardCheck, BarChart2,
    CalendarDays, CreditCard, Users2, Settings2,
    PanelLeft, Bell, Sun, Moon, Monitor, LogOut,
  } from "@lucide/svelte";
  import { onMount } from "svelte";

  // ── Sidebar state ──────────────────────────────────────────────
  let collapsed = false;
  let mobile = false;
  let mobileOpen = false;

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
    // Updating systemDark triggers the reactive $: block below automatically
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

  // Reactive: re-runs whenever themeMode or systemDark changes
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

  // ── Nav ────────────────────────────────────────────────────────
  $: currentPath = $page.url.pathname;

  function active(path: string) {
    return currentPath === path || currentPath.startsWith(path + "/");
  }

  $: pageTitle = currentPath.split("/").filter(Boolean)[0]?.replace(/-/g, " ") ?? "Dashboard";

  // ── Role-based nav ─────────────────────────────────────────────
  $: isSuperAdmin = $currentUser?.system_role === "SUPERADMIN";
  $: isSchoolStaff = $currentUser?.system_role === "SCHOOL_STAFF";
  $: canViewStudents  = isSuperAdmin || auth.can("view_students");
  $: canViewFees      = isSuperAdmin || auth.can("view_fees");
  $: canManageStaff   = isSuperAdmin || isSchoolStaff;

  // Auth guard
  $: if (!$auth.loading && !$isAuthenticated) {
    goto("/login");
  }

  // Only dynamic/positional properties — static styles live in the CSS block
  $: sidebarStyle = mobile
    ? `position:fixed;top:var(--topbar-h);left:0;height:calc(100% - var(--topbar-h));width:var(--sidebar-w);transform:translateX(${mobileOpen ? "0" : "-100%"});transition:transform 0.22s ease;z-index:50;`
    : `position:relative;width:${collapsed ? "54px" : "var(--sidebar-w)"};transition:width 0.2s ease;z-index:20;`;

  $: userName = $currentUser?.email?.split("@")[0] ?? "—";
  $: userRole = $currentUser?.system_role ?? "—";
</script>

<div class="app-shell">

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
          {#if $schoolBranding?.logo_url}
            <img src={$schoolBranding.logo_url} alt="School logo" class="sidebar-logo-img" />
          {:else}
            {($schoolBranding?.name ?? "T").charAt(0).toUpperCase()}
          {/if}
        </div>
        {#if !collapsed || mobile}
          <div class="brand-name">
            <div class="brand-title">{$schoolBranding?.name ?? "TTEK-SIS"}</div>
            <div class="brand-sub">School Management</div>
          </div>
        {/if}
      </div>

      <!-- Nav -->
      <!-- svelte-ignore a11y-click-events-have-key-events -->
      <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
      <nav class="sidebar-nav" on:click={() => { if (mobile) mobileOpen = false; }}>

        <!-- Overview -->
        <div class="nav-section">
          {#if !collapsed || mobile}
            <span class="nav-section-label">Overview</span>
          {/if}
          <a href="/dashboard" class="nav-item" class:active={active("/dashboard")}>
            <LayoutDashboard size={15} style="flex-shrink:0; opacity:{active('/dashboard') ? '1' : '.6'}" />
            {#if !collapsed || mobile}<span>Dashboard</span>{/if}
          </a>
        </div>

        <!-- Academic -->
        <div class="nav-section">
          {#if !collapsed || mobile}
            <span class="nav-section-label">Academic</span>
          {/if}
          {#if canViewStudents}
            <a href="/students" class="nav-item" class:active={active("/students")}>
              <Users size={15} style="flex-shrink:0; opacity:{active('/students') ? '1' : '.6'}" />
              {#if !collapsed || mobile}<span>Students</span>{/if}
            </a>
          {/if}
          <a href="/attendance" class="nav-item" class:active={active("/attendance")}>
            <ClipboardCheck size={15} style="flex-shrink:0; opacity:{active('/attendance') ? '1' : '.6'}" />
            {#if !collapsed || mobile}<span>Attendance</span>{/if}
          </a>
          {#if !collapsed || mobile}
            <div class="nav-item-disabled">
              <BarChart2 size={15} style="flex-shrink:0; opacity:.35" />
              <span style="flex:1;">Assessments</span>
              <span class="coming-badge">soon</span>
            </div>
          {/if}
        </div>

        <!-- Finance -->
        {#if canViewFees}
          <div class="nav-section">
            {#if !collapsed || mobile}
              <span class="nav-section-label">Finance</span>
            {/if}
            <a href="/fees" class="nav-item" class:active={active("/fees")}>
              <CreditCard size={15} style="flex-shrink:0; opacity:{active('/fees') ? '1' : '.6'}" />
              {#if !collapsed || mobile}<span>Fees Ledger</span>{/if}
            </a>
          </div>
        {/if}

        <!-- Admin -->
        {#if canManageStaff}
          <div class="nav-section">
            {#if !collapsed || mobile}
              <span class="nav-section-label">Admin</span>
            {/if}
            <a href="/staff" class="nav-item" class:active={active("/staff")}>
              <Users2 size={15} style="flex-shrink:0; opacity:{active('/staff') ? '1' : '.6'}" />
              {#if !collapsed || mobile}<span>Staff</span>{/if}
            </a>
          </div>
        {/if}

        <!-- Settings — always visible -->
        <div class="nav-section">
          {#if !collapsed || mobile}
            <span class="nav-section-label">System</span>
          {/if}
          <a href="/settings" class="nav-item" class:active={active("/settings")}>
            <Settings2 size={15} style="flex-shrink:0; opacity:{active('/settings') ? '1' : '.6'}" />
            {#if !collapsed || mobile}<span>Settings</span>{/if}
          </a>
        </div>

      </nav>

      <!-- User footer -->
      <div class="sidebar-footer">
        <div class="user-card">
          <Avatar name={$currentUser?.email ?? "U"} size="sm" />
          {#if !collapsed || mobile}
            <div class="user-info">
              <div class="user-name">{userName}</div>
              <div class="user-role">{userRole}</div>
            </div>
            <button class="logout-btn" on:click={handleLogout} aria-label="Sign out">
              <LogOut size={14} />
            </button>
          {/if}
        </div>
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
    padding: 8px 6px 4px;
    scrollbar-width: none;
  }
  .sidebar-nav::-webkit-scrollbar { display: none; }

  .nav-section { margin-bottom: 4px; }

  .nav-section-label {
    display: block;
    font-size: 9.5px;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--tx-low);
    padding: 6px 10px 3px;
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
    position: relative;
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
    border-radius: 7px;
  }

  .sidebar.collapsed .nav-item.active {
    /* no left-border indicator when collapsed — icon color conveys active state */
    box-shadow: none;
  }

  .nav-item-disabled {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 7px;
    color: var(--tx-low);
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    cursor: default;
  }

  .coming-badge {
    font-size: 9px;
    font-weight: 600;
    padding: 1px 5px;
    border-radius: 4px;
    background: var(--border-subtle);
    color: var(--tx-low);
    margin-left: auto;
  }

  /* Sidebar user footer */
  .sidebar-footer {
    border-top: 1px solid var(--border-subtle);
    padding: 10px 8px;
    flex-shrink: 0;
  }

  .user-card {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 5px 4px;
    border-radius: 8px;
    overflow: hidden;
  }

  .sidebar.collapsed .user-card {
    justify-content: center;
    padding: 5px 0;
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

  .logout-btn {
    width: 26px;
    height: 26px;
    border-radius: 6px;
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

  .logout-btn:hover {
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
</style>
