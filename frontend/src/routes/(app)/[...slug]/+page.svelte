<script lang="ts">
  import { page } from "$app/stores";
  import { Construction, ClipboardCheck, PenLine, Users, CreditCard, BarChart3, Home } from "@lucide/svelte";
  import { schoolBranding } from "$stores/school";

  // Route-specific messages so teachers understand what each module will do,
  // rather than a generic "coming in a future release."
  const ROUTE_META: Record<string, {
    icon: typeof Construction;
    label: string;
    description: string;
  }> = {
    attendance: {
      icon: ClipboardCheck,
      label: "Attendance",
      description: "Mark daily attendance for your class, view attendance history and flag absences. You'll be able to do this from any device.",
    },
    scores: {
      icon: PenLine,
      label: "Scores",
      description: "Enter and review student scores, track class performance and generate term reports.",
    },
    students: {
      icon: Users,
      label: "Students",
      description: "View student profiles, class enrolment records and academic history.",
    },
    fees: {
      icon: CreditCard,
      label: "Fees",
      description: "Record payments, view fee statements and manage outstanding balances.",
    },
    analytics: {
      icon: BarChart3,
      label: "Reports & Analytics",
      description: "Generate school-wide reports, attendance summaries and academic performance analytics.",
    },
    "students/new": {
      icon: Users,
      label: "Add Student",
      description: "Enrol new students and manage class assignments.",
    },
    "fees/record": {
      icon: CreditCard,
      label: "Record Payment",
      description: "Record fee payments and issue receipts.",
    },
  };

  $: slug = $page.params.slug ?? "";
  $: meta = ROUTE_META[slug] ?? null;
  $: icon = meta?.icon ?? Construction;
</script>

<svelte:head>
  <title>{meta?.label ?? 'Coming Soon'} — {$schoolBranding?.name ?? 'TTEK-SMS'}</title>
</svelte:head>

<div class="wrap">
  <div class="icon-wrap">
    <svelte:component this={icon} size={22} />
  </div>

  <div class="body">
    <h2 class="title">
      {meta?.label ?? 'Not yet available'}
    </h2>
    <p class="desc">
      {#if meta}
        {meta.description} This module is coming in a future release.
      {:else}
        <code class="slug">/{slug}</code> is coming in a future release.
      {/if}
    </p>
  </div>
</div>

<style>
  .wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    text-align: center;
    gap: 16px;
    padding: 24px;
  }

  .icon-wrap {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    background: var(--accent-subtle);
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .body {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-width: 380px;
  }

  .title {
    font-size: 15px;
    font-weight: 600;
    color: var(--tx-high);
    margin: 0;
  }

  .desc {
    font-size: 13px;
    color: var(--tx-low);
    line-height: 1.6;
    margin: 0;
  }

  .slug {
    font-size: 12px;
    padding: 1px 6px;
    border-radius: 4px;
    background: var(--surface-2);
    color: var(--tx-mid);
  }
</style>
