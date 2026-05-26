<script lang="ts">
  import { currentUser } from "$stores/auth";
  import {
    Users, CreditCard, ClipboardCheck, UserCheck,
    TrendingUp, TrendingDown, AlertCircle, CheckCircle2,
    ArrowRight, UserPlus, FileText, BookOpen,
  } from "@lucide/svelte";

  // ── Mock data (replace with TanStack Query + real API) ─────────
  const kpis = [
    {
      label: "Total Students",
      value: "1,248",
      sub: "+12 this term",
      trend: "up",
      icon: Users,
    },
    {
      label: "Fees Collected",
      value: "GHS 84,320",
      sub: "of GHS 112,000 billed",
      trend: "neutral",
      icon: CreditCard,
    },
    {
      label: "Attendance Today",
      value: "91.4%",
      sub: "1,139 of 1,248 present",
      trend: "down",
      icon: ClipboardCheck,
    },
    {
      label: "Active Staff",
      value: "68",
      sub: "4 on leave",
      trend: "neutral",
      icon: UserCheck,
    },
  ];

  const transactions = [
    { student: "Ama Owusu",       class: "JHS 3A", amount: "GHS 850",  date: "26 May 2026", status: "paid" },
    { student: "Kweku Mensah",    class: "SHS 1B", amount: "GHS 1,200",date: "26 May 2026", status: "paid" },
    { student: "Abena Asante",    class: "JHS 2C", amount: "GHS 700",  date: "25 May 2026", status: "paid" },
    { student: "Kofi Boateng",    class: "SHS 2A", amount: "GHS 950",  date: "25 May 2026", status: "partial" },
    { student: "Akosua Darko",    class: "JHS 1B", amount: "GHS 850",  date: "24 May 2026", status: "paid" },
  ];

  const alerts = [
    { type: "warn",  text: "14 students have outstanding fees over 30 days." },
    { type: "info",  text: "Term 2 timetable not yet published." },
    { type: "ok",    text: "Migration 002 applied successfully." },
  ];

  const quickActions = [
    { label: "Add Student",     icon: UserPlus,  href: "/students/new" },
    { label: "Record Payment",  icon: CreditCard, href: "/fees/record" },
    { label: "Mark Attendance", icon: ClipboardCheck, href: "/attendance" },
    { label: "View Reports",    icon: FileText,  href: "/analytics" },
  ];

  function trendColor(t: string) {
    return t === "up" ? "var(--ok-text)" : t === "down" ? "var(--err-text)" : "var(--tx-low)";
  }

  function statusStyle(s: string) {
    return s === "paid"
      ? { color: "var(--ok-text)", bg: "var(--ok-bg)" }
      : { color: "var(--warn-text)", bg: "var(--warn-bg)" };
  }

  function alertStyle(t: string) {
    if (t === "warn") return { icon: AlertCircle, color: "var(--warn-text)", bg: "var(--warn-bg)" };
    if (t === "ok")   return { icon: CheckCircle2, color: "var(--ok-text)", bg: "var(--ok-bg)" };
    return { icon: AlertCircle, color: "var(--tx-low)", bg: "var(--surface-2)" };
  }

  $: greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  })();

  $: name = $currentUser?.email?.split("@")[0] ?? "there";
</script>

<svelte:head>
  <title>Dashboard — TTEK-SIS</title>
</svelte:head>

<!-- Page header -->
<div style="margin-bottom:24px;">
  <h1 style="font-size:17px; font-weight:600; color:var(--tx-high); line-height:1.3;">
    {greeting}, {name}
  </h1>
  <p style="font-size:13px; color:var(--tx-low); margin-top:3px;">
    Here's what's happening at your school today.
  </p>
</div>

<!-- KPI cards -->
<div style="
  display:grid;
  grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));
  gap:14px;
  margin-bottom:24px;
">
  {#each kpis as kpi}
    <div style="
      background:var(--surface-1);
      border:1px solid var(--border-subtle);
      border-radius:var(--radius);
      padding:18px 20px;
      box-shadow:var(--shadow-xs);
    ">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
        <span style="font-size:12px; font-weight:500; color:var(--tx-low); letter-spacing:.02em;">{kpi.label}</span>
        <div style="
          width:30px; height:30px; border-radius:7px;
          background:var(--accent-subtle);
          display:flex; align-items:center; justify-content:center;
          color:var(--accent);
        ">
          <svelte:component this={kpi.icon} size={14} />
        </div>
      </div>
      <div style="font-size:22px; font-weight:700; color:var(--tx-high); line-height:1; margin-bottom:6px;">
        {kpi.value}
      </div>
      <div style="display:flex; align-items:center; gap:4px; font-size:11.5px; color:{trendColor(kpi.trend)};">
        {#if kpi.trend === "up"}
          <TrendingUp size={11} />
        {:else if kpi.trend === "down"}
          <TrendingDown size={11} />
        {/if}
        <span>{kpi.sub}</span>
      </div>
    </div>
  {/each}
</div>

<!-- Content grid -->
<div style="
  display:grid;
  grid-template-columns:1fr 300px;
  gap:14px;
  align-items:start;
">

  <!-- Recent transactions -->
  <div style="
    background:var(--surface-1);
    border:1px solid var(--border-subtle);
    border-radius:var(--radius);
    box-shadow:var(--shadow-xs);
    overflow:hidden;
  ">
    <div style="
      display:flex; align-items:center; justify-content:space-between;
      padding:14px 18px;
      border-bottom:1px solid var(--border-subtle);
    ">
      <span style="font-size:13px; font-weight:600; color:var(--tx-high);">Recent Payments</span>
      <a href="/fees" style="
        font-size:12px; color:var(--accent);
        display:flex; align-items:center; gap:3px;
        text-decoration:none;
      ">
        View all <ArrowRight size={11} />
      </a>
    </div>

    <table style="width:100%; border-collapse:collapse;">
      <thead>
        <tr style="background:var(--surface-2);">
          <th style="text-align:left; padding:9px 18px; font-size:11px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:var(--tx-low);">Student</th>
          <th style="text-align:left; padding:9px 12px; font-size:11px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:var(--tx-low);">Class</th>
          <th style="text-align:right; padding:9px 12px; font-size:11px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:var(--tx-low);">Amount</th>
          <th style="text-align:left; padding:9px 12px; font-size:11px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:var(--tx-low);">Date</th>
          <th style="text-align:center; padding:9px 18px 9px 12px; font-size:11px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:var(--tx-low);">Status</th>
        </tr>
      </thead>
      <tbody>
        {#each transactions as tx, i}
          {@const st = statusStyle(tx.status)}
          <tr style="border-top:{i > 0 ? '1px solid var(--border-subtle)' : 'none'};">
            <td style="padding:11px 18px; font-size:13px; font-weight:500; color:var(--tx-high);">{tx.student}</td>
            <td style="padding:11px 12px; font-size:12px; color:var(--tx-low);">{tx.class}</td>
            <td style="padding:11px 12px; font-size:13px; font-weight:500; color:var(--tx-high); text-align:right;">{tx.amount}</td>
            <td style="padding:11px 12px; font-size:12px; color:var(--tx-low);">{tx.date}</td>
            <td style="padding:11px 18px 11px 12px; text-align:center;">
              <span style="
                font-size:11px; font-weight:600;
                padding:2px 8px; border-radius:4px;
                color:{st.color}; background:{st.bg};
                text-transform:capitalize;
              ">{tx.status}</span>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <!-- Right column -->
  <div style="display:flex; flex-direction:column; gap:14px;">

    <!-- Alerts -->
    <div style="
      background:var(--surface-1);
      border:1px solid var(--border-subtle);
      border-radius:var(--radius);
      box-shadow:var(--shadow-xs);
      overflow:hidden;
    ">
      <div style="padding:14px 16px; border-bottom:1px solid var(--border-subtle);">
        <span style="font-size:13px; font-weight:600; color:var(--tx-high);">Alerts</span>
      </div>
      <div style="padding:8px;">
        {#each alerts as alert}
          {@const s = alertStyle(alert.type)}
          <div style="
            display:flex; align-items:flex-start; gap:9px;
            padding:9px 10px; border-radius:6px;
            background:{s.bg}; margin-bottom:6px;
          ">
            <div style="color:{s.color}; flex-shrink:0; margin-top:1px;">
              <svelte:component this={s.icon} size={13} />
            </div>
            <span style="font-size:12px; color:{s.color}; line-height:1.45;">{alert.text}</span>
          </div>
        {/each}
      </div>
    </div>

    <!-- Quick actions -->
    <div style="
      background:var(--surface-1);
      border:1px solid var(--border-subtle);
      border-radius:var(--radius);
      box-shadow:var(--shadow-xs);
      overflow:hidden;
    ">
      <div style="padding:14px 16px; border-bottom:1px solid var(--border-subtle);">
        <span style="font-size:13px; font-weight:600; color:var(--tx-high);">Quick Actions</span>
      </div>
      <div style="padding:8px; display:flex; flex-direction:column; gap:4px;">
        {#each quickActions as action}
          <a href={action.href} style="
            display:flex; align-items:center; gap:10px;
            padding:9px 10px; border-radius:6px;
            color:var(--tx-mid); font-size:13px;
            text-decoration:none;
            transition:background 0.12s, color 0.12s;
          "
          on:mouseenter={e => (e.currentTarget as HTMLElement).style.background = 'var(--bg-hover)'}
          on:mouseleave={e => (e.currentTarget as HTMLElement).style.background = 'transparent'}
          >
            <div style="
              width:28px; height:28px; border-radius:6px;
              background:var(--accent-subtle);
              display:flex; align-items:center; justify-content:center;
              color:var(--accent); flex-shrink:0;
            ">
              <svelte:component this={action.icon} size={13} />
            </div>
            <span style="flex:1;">{action.label}</span>
            <ArrowRight size={12} style="color:var(--tx-low);" />
          </a>
        {/each}
      </div>
    </div>

  </div>
</div>
