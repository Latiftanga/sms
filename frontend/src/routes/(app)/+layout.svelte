<script lang="ts">
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { auth, isAuthenticated, currentUser } from "$stores/auth";
  import {
    LayoutDashboard, Users, ClipboardCheck, BarChart2,
    CalendarDays, CreditCard, Users2, Settings2,
    PanelLeft, Bell, Sun, Moon, LogOut, ChevronRight,
  } from "@lucide/svelte";
  import { onMount } from "svelte";

  // ── Sidebar state ──────────────────────────────────────────────
  let collapsed = false;
  let dark = false;
  let mobile = false;
  let mobileOpen = false;

  const MOBILE_BP = 768;

  function onResize() {
    const wasMobile = mobile;
    mobile = window.innerWidth < MOBILE_BP;
    if (mobile && !wasMobile) mobileOpen = false;   // just went small: close drawer
    if (!mobile && wasMobile) mobileOpen = false;   // went back to desktop: reset
  }

  function toggleSidebar() {
    if (mobile) mobileOpen = !mobileOpen;
    else collapsed = !collapsed;
  }

  onMount(() => {
    const saved = localStorage.getItem("sis-theme");
    dark = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(dark);

    const savedAccent = localStorage.getItem("sis-accent");
    if (savedAccent) applyAccent(savedAccent);

    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  });

  function toggleTheme() {
    dark = !dark;
    applyTheme(dark);
    localStorage.setItem("sis-theme", dark ? "dark" : "light");
  }

  function applyTheme(isDark: boolean) {
    document.documentElement.classList.toggle("dark", isDark);
  }

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

  // ── Role-based nav ─────────────────────────────────────────────
  $: isSuperAdmin = $currentUser?.system_role === "SUPERADMIN";
  $: canViewStudents  = isSuperAdmin || auth.can("view_students");
  $: canViewFees      = isSuperAdmin || auth.can("view_fees");
  $: canManageStaff   = isSuperAdmin || auth.can("manage_users");
  $: canViewAnalytics = isSuperAdmin || auth.can("view_analytics");

  // Auth guard
  $: if (!$auth.loading && !$isAuthenticated) {
    goto("/login");
  }

  const SIDEBAR_BASE = "background:var(--surface-0);border-right:1px solid var(--border-subtle);display:flex;flex-direction:column;overflow:hidden;";
  $: sidebarStyle = mobile
    ? `position:fixed;top:0;left:0;height:100%;width:var(--sidebar-w);transform:translateX(${mobileOpen ? "0" : "-100%"});transition:transform 0.22s ease;z-index:50;${SIDEBAR_BASE}`
    : `position:relative;width:${collapsed ? "54px" : "var(--sidebar-w)"};flex-shrink:0;transition:width 0.2s ease;z-index:20;${SIDEBAR_BASE}`;
</script>

<div style="display:flex; height:100vh; overflow:hidden; background:var(--bg);">

  <!-- Mobile backdrop -->
  {#if mobile && mobileOpen}
    <div
      style="position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:49;"
      role="button"
      tabindex="-1"
      aria-label="Close sidebar"
      on:click={() => mobileOpen = false}
      on:keydown={(e) => e.key === 'Escape' && (mobileOpen = false)}
    />
  {/if}

  <!-- ── Sidebar ──────────────────────────────────────────────── -->
  <aside style={sidebarStyle}>

    <!-- Logo -->
    <div style="
      height: var(--topbar-h);
      padding: 0 12px;
      display: flex;
      align-items: center;
      gap: 10px;
      border-bottom: 1px solid var(--border-subtle);
      flex-shrink: 0;
      overflow: hidden;
    ">
      <div style="
        width: 27px; height: 27px;
        border-radius: 7px;
        background: var(--accent);
        color: var(--accent-fg);
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 12px;
        flex-shrink: 0;
      ">T</div>
      {#if !collapsed || mobile}
        <div style="overflow:hidden; white-space:nowrap;">
          <div style="font-size:13px; font-weight:700; color:var(--tx-high);">TTEK-SIS</div>
          <div style="font-size:10px; color:var(--tx-low); margin-top:1px;">School Management</div>
        </div>
      {/if}
    </div>

    <!-- Nav -->
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
    <nav style="flex:1; overflow-y:auto; padding:8px 6px 4px;"
         on:click={() => { if (mobile) mobileOpen = false; }}>

      <!-- Overview -->
      <div style="margin-bottom:4px;">
        {#if !collapsed || mobile}
          <div style="font-size:9.5px; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:var(--tx-low); padding:6px 8px 3px;">Overview</div>
        {/if}
        <a href="/dashboard" style="
          display:flex; align-items:center; gap:8px;
          padding:6px 8px; border-radius:7px;
          color:{active('/dashboard') ? 'var(--accent)' : 'var(--tx-mid)'};
          background:{active('/dashboard') ? 'var(--accent-subtle)' : 'transparent'};
          font-size:13px; font-weight:{active('/dashboard') ? '500' : '400'};
          text-decoration:none; white-space:nowrap; overflow:hidden;
          transition: background 0.12s, color 0.12s;
        ">
          <LayoutDashboard size={15} style="flex-shrink:0; opacity:{active('/dashboard') ? '1' : '.6'}" />
          {#if !collapsed || mobile}<span>Dashboard</span>{/if}
        </a>
      </div>

      <!-- Academic -->
      <div style="margin-bottom:4px;">
        {#if !collapsed || mobile}
          <div style="font-size:9.5px; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:var(--tx-low); padding:6px 8px 3px;">Academic</div>
        {/if}
        {#if canViewStudents}
          <a href="/students" style="
            display:flex; align-items:center; gap:8px;
            padding:6px 8px; border-radius:7px;
            color:{active('/students') ? 'var(--accent)' : 'var(--tx-mid)'};
            background:{active('/students') ? 'var(--accent-subtle)' : 'transparent'};
            font-size:13px; font-weight:{active('/students') ? '500' : '400'};
            text-decoration:none; white-space:nowrap; overflow:hidden;
            transition: background 0.12s, color 0.12s;
          ">
            <Users size={15} style="flex-shrink:0; opacity:{active('/students') ? '1' : '.6'}" />
            {#if !collapsed || mobile}<span>Students</span>{/if}
          </a>
        {/if}
        <a href="/attendance" style="
          display:flex; align-items:center; gap:8px;
          padding:6px 8px; border-radius:7px;
          color:{active('/attendance') ? 'var(--accent)' : 'var(--tx-mid)'};
          background:{active('/attendance') ? 'var(--accent-subtle)' : 'transparent'};
          font-size:13px; font-weight:{active('/attendance') ? '500' : '400'};
          text-decoration:none; white-space:nowrap; overflow:hidden;
          transition: background 0.12s, color 0.12s;
        ">
          <ClipboardCheck size={15} style="flex-shrink:0; opacity:{active('/attendance') ? '1' : '.6'}" />
          {#if !collapsed || mobile}<span>Attendance</span>{/if}
        </a>
        {#if !collapsed || mobile}
          <div style="
            display:flex; align-items:center; gap:8px;
            padding:6px 8px; border-radius:7px;
            color:var(--tx-low); font-size:13px;
            white-space:nowrap; overflow:hidden;
          ">
            <BarChart2 size={15} style="flex-shrink:0; opacity:.4" />
            <span style="flex:1;">Assessments</span>
            <span style="font-size:9px; font-weight:600; padding:1px 5px; border-radius:4px; background:var(--border-subtle); color:var(--tx-low);">soon</span>
          </div>
        {/if}
      </div>

      <!-- Finance -->
      {#if canViewFees}
        <div style="margin-bottom:4px;">
          {#if !collapsed || mobile}
            <div style="font-size:9.5px; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:var(--tx-low); padding:6px 8px 3px;">Finance</div>
          {/if}
          <a href="/fees" style="
            display:flex; align-items:center; gap:8px;
            padding:6px 8px; border-radius:7px;
            color:{active('/fees') ? 'var(--accent)' : 'var(--tx-mid)'};
            background:{active('/fees') ? 'var(--accent-subtle)' : 'transparent'};
            font-size:13px; font-weight:{active('/fees') ? '500' : '400'};
            text-decoration:none; white-space:nowrap; overflow:hidden;
            transition: background 0.12s, color 0.12s;
          ">
            <CreditCard size={15} style="flex-shrink:0; opacity:{active('/fees') ? '1' : '.6'}" />
            {#if !collapsed || mobile}<span>Fees Ledger</span>{/if}
          </a>
        </div>
      {/if}

      <!-- Admin -->
      {#if canManageStaff}
        <div style="margin-bottom:4px;">
          {#if !collapsed || mobile}
            <div style="font-size:9.5px; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:var(--tx-low); padding:6px 8px 3px;">Admin</div>
          {/if}
          <a href="/staff" style="
            display:flex; align-items:center; gap:8px;
            padding:6px 8px; border-radius:7px;
            color:{active('/staff') ? 'var(--accent)' : 'var(--tx-mid)'};
            background:{active('/staff') ? 'var(--accent-subtle)' : 'transparent'};
            font-size:13px; font-weight:{active('/staff') ? '500' : '400'};
            text-decoration:none; white-space:nowrap; overflow:hidden;
            transition: background 0.12s, color 0.12s;
          ">
            <Users2 size={15} style="flex-shrink:0; opacity:{active('/staff') ? '1' : '.6'}" />
            {#if !collapsed || mobile}<span>Staff</span>{/if}
          </a>
          <a href="/settings" style="
            display:flex; align-items:center; gap:8px;
            padding:6px 8px; border-radius:7px;
            color:{active('/settings') ? 'var(--accent)' : 'var(--tx-mid)'};
            background:{active('/settings') ? 'var(--accent-subtle)' : 'transparent'};
            font-size:13px; font-weight:{active('/settings') ? '500' : '400'};
            text-decoration:none; white-space:nowrap; overflow:hidden;
            transition: background 0.12s, color 0.12s;
          ">
            <Settings2 size={15} style="flex-shrink:0; opacity:{active('/settings') ? '1' : '.6'}" />
            {#if !collapsed || mobile}<span>Settings</span>{/if}
          </a>
        </div>
      {/if}

    </nav>

    <!-- School footer -->
    <div style="border-top:1px solid var(--border-subtle); padding:11px 12px; flex-shrink:0; overflow:hidden;">
      <div style="display:flex; align-items:center; gap:9px; overflow:hidden;">
        <div style="
          width:7px; height:7px; border-radius:50%;
          background:var(--ok-dot);
          box-shadow:0 0 0 2.5px var(--ok-bg);
          flex-shrink:0;
        "></div>
        {#if !collapsed || mobile}
          <div style="overflow:hidden;">
            <div style="font-size:11.5px; font-weight:500; color:var(--tx-mid); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
              {$currentUser?.email?.split('@')[0] ?? '—'}
            </div>
            <div style="font-size:10px; color:var(--tx-low); margin-top:1px; white-space:nowrap;">
              {$currentUser?.system_role ?? '—'}
            </div>
          </div>
        {/if}
      </div>
    </div>

  </aside>

  <!-- ── Main column ──────────────────────────────────────────── -->
  <div style="flex:1; display:flex; flex-direction:column; overflow:hidden; min-width:0;">

    <!-- Topbar -->
    <header style="
      height:var(--topbar-h);
      flex-shrink:0;
      background:var(--surface-0);
      border-bottom:1px solid var(--border-subtle);
      padding:0 18px 0 14px;
      display:flex;
      align-items:center;
      gap:10px;
    ">
      <!-- Sidebar toggle -->
      <button
        on:click={toggleSidebar}
        style="
          width:30px; height:30px; border-radius:7px;
          border:1px solid var(--border-subtle);
          background:transparent;
          display:flex; align-items:center; justify-content:center;
          color:var(--tx-mid);
          transition:background 0.12s, color 0.12s;
        "
        title="Toggle sidebar"
      >
        <PanelLeft size={14} />
      </button>

      <div style="width:1px; height:16px; background:var(--border-strong); flex-shrink:0;"></div>

      <!-- Breadcrumb -->
      <nav style="display:flex; align-items:center; gap:5px; font-size:13px; color:var(--tx-low);">
        <span>TTEK-SIS</span>
        <ChevronRight size={12} />
        <span style="color:var(--tx-high); font-weight:500; text-transform:capitalize;">
          {currentPath.split('/').filter(Boolean)[0] ?? 'Dashboard'}
        </span>
      </nav>

      <div style="flex:1;"></div>

      <!-- Notifications -->
      <button style="
        width:30px; height:30px; border-radius:7px;
        border:1px solid var(--border-subtle);
        background:transparent;
        display:flex; align-items:center; justify-content:center;
        color:var(--tx-mid); position:relative;
        transition:background 0.12s, color 0.12s;
      " title="Notifications">
        <Bell size={14} />
        <span style="
          position:absolute; top:6px; right:6px;
          width:5px; height:5px; border-radius:50%;
          background:var(--accent);
          border:1.5px solid var(--surface-0);
        "></span>
      </button>

      <!-- Theme toggle -->
      <button
        on:click={toggleTheme}
        style="
          width:30px; height:30px; border-radius:7px;
          border:1px solid var(--border-subtle);
          background:transparent;
          display:flex; align-items:center; justify-content:center;
          color:var(--tx-mid);
          transition:background 0.12s, color 0.12s;
        "
        title="Toggle theme"
      >
        {#if dark}<Sun size={14} />{:else}<Moon size={14} />{/if}
      </button>

      <!-- Avatar + logout -->
      <button
        on:click={handleLogout}
        style="
          display:flex; align-items:center; gap:7px;
          padding:4px 8px; border-radius:7px;
          border:1px solid var(--border-subtle);
          background:transparent;
          color:var(--tx-mid); font-size:12px;
          transition:background 0.12s, color 0.12s;
        "
        title="Sign out"
      >
        <div style="
          width:22px; height:22px; border-radius:50%;
          background:var(--accent-subtle);
          display:flex; align-items:center; justify-content:center;
          font-size:10px; font-weight:700; color:var(--accent);
        ">
          {($currentUser?.email?.[0] ?? 'U').toUpperCase()}
        </div>
        <LogOut size={13} />
      </button>

    </header>

    <!-- Page content -->
    <main style="flex:1; overflow-y:auto; padding:24px;">
      <slot />
    </main>

  </div>
</div>
