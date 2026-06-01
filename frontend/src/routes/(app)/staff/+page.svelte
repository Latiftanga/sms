<script lang="ts">
  import { onMount } from "svelte";
  import { goto, preloadData } from "$app/navigation";
  import { api } from "$api/client";
  import Button from "$components/ui/Button.svelte";
  import Badge from "$components/ui/Badge.svelte";
  import Spinner from "$components/ui/Spinner.svelte";
  import EmptyState from "$components/ui/EmptyState.svelte";
  import { UserPlus, Upload, Search, ChevronLeft, ChevronRight, Check, AlertCircle, Users } from "@lucide/svelte";
  import type { StaffMember, PagedResponse } from "$api/types";
  import { auth } from "$lib/stores/auth";
  import { schoolBranding } from "$stores/school";

  $: canManageStaff = $auth.user?.system_role === "SUPERADMIN" || $auth.user?.permissions?.manage_staff === true;

  // ── List state ────────────────────────────────────────────────────
  let staff: StaffMember[] = [];
  let total = 0;
  let skip = 0;
  const LIMIT = 25;
  let loading = true;
  let listError = "";

  let search = "";
  let filterCategory = "";
  let filterActive: "true" | "false" | "" = "";

  let searchDebounce: ReturnType<typeof setTimeout>;

  const CATEGORY_LABELS: Record<string, string> = {
    TEACHING: "Teaching",
    "NON-TEACHING": "Non-Teaching",
  };

  function apiError(e: unknown): string {
    const err = e as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail ?? "Something went wrong.";
  }

  async function loadStaff() {
    loading = true; listError = "";
    try {
      const params: Record<string, string | number> = { skip, limit: LIMIT };
      if (search) params.search = search;
      if (filterCategory) params.category = filterCategory;
      if (filterActive !== "") params.is_active = filterActive;
      const { data } = await api.get<PagedResponse<StaffMember>>("/staff", { params });
      staff = data.items;
      total = data.total;
    } catch (e) {
      listError = apiError(e);
    } finally {
      loading = false;
    }
  }

  function onSearchInput() {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => { skip = 0; loadStaff(); }, 320);
  }

  function onFilterChange() { skip = 0; loadStaff(); }

  function prevPage() { if (skip >= LIMIT) { skip -= LIMIT; loadStaff(); } }
  function nextPage() { if (skip + LIMIT < total) { skip += LIMIT; loadStaff(); } }

  onMount(loadStaff);

  // ── Helpers ───────────────────────────────────────────────────────
  function initials(m: StaffMember) {
    return (m.first_name.charAt(0) + m.last_name.charAt(0)).toUpperCase();
  }

  function categoryColor(cat: string): "accent" | "neutral" {
    return cat === "TEACHING" ? "accent" : "neutral";
  }

  function humanise(s: string | null | undefined): string {
    if (!s) return "—";
    return s.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  }

  $: pageStart = skip + 1;
  $: pageEnd   = Math.min(skip + LIMIT, total);
</script>

<svelte:head><title>Staff — {$schoolBranding?.name ?? 'TTEK-SMS'}</title></svelte:head>

<div class="page">

  <div class="staff-card">

    <!-- ── Card header ──────────────────────────────────────────── -->
    <div class="card-header">
      <div class="header-left">
        <div class="header-icon"><Users size={15} /></div>
        <h1 class="card-title">Staff</h1>
        {#if !loading}
          <span class="count-chip">{total.toLocaleString()}</span>
        {/if}
      </div>
      <div class="header-actions">
        {#if canManageStaff}
          <Button variant="ghost" size="sm" on:click={() => goto("/staff/import")}>
            <Upload size={13} /> Bulk Import
          </Button>
          <Button size="sm" on:click={() => goto("/staff/new")}>
            <UserPlus size={13} /> Add Staff
          </Button>
        {/if}
      </div>
    </div>

    <!-- ── Filter bar ─────────────────────────────────────────── -->
    <div class="filter-bar">
      <div class="search-wrap">
        <Search size={13} class="search-icon" />
        <input
          class="input search-input"
          placeholder="Search name or staff ID…"
          bind:value={search}
          on:input={onSearchInput}
        />
      </div>
      <select class="input filter-select" bind:value={filterCategory} on:change={onFilterChange}>
        <option value="">All categories</option>
        <option value="TEACHING">Teaching</option>
        <option value="NON-TEACHING">Non-Teaching</option>
      </select>
      <select class="input filter-select" bind:value={filterActive} on:change={onFilterChange}>
        <option value="">Active + inactive</option>
        <option value="true">Active only</option>
        <option value="false">Inactive only</option>
      </select>
    </div>

    <!-- ── Body ──────────────────────────────────────────────── -->
    <div class="card-body">
      {#if loading}
        <div class="centered-state"><Spinner /></div>

      {:else if listError}
        <div class="centered-state">
          <AlertCircle size={20} class="error-icon" />
          <p class="error-text">{listError}</p>
          <Button size="sm" on:click={loadStaff}>Retry</Button>
        </div>

      {:else if staff.length === 0}
        <EmptyState
          message={search || filterCategory
            ? "No staff match your filters. Try adjusting your search."
            : "No staff yet. Add individual staff or bulk import from CSV/Excel."}
        >
          {#if !search && !filterCategory && canManageStaff}
            <Button on:click={() => goto("/staff/new")}>
              <UserPlus size={13} /> Add First Staff Member
            </Button>
          {/if}
        </EmptyState>

      {:else}
        <div class="table-wrap">
          <table class="staff-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>ID</th>
                <th>Category</th>
                <th>Employment</th>
                <th>Rank / Designation</th>
                <th>Account</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {#each staff as member}
                <tr
                  class="staff-row"
                  on:click={() => goto(`/staff/${member.id}`)}
                  on:mouseenter={() => preloadData(`/staff/${member.id}`)}
                >
                  <td>
                    <div class="member-cell">
                      <div class="avatar" data-cat={member.category}>
                        {#if member.photo_url}
                          <img src={member.photo_url} alt={member.first_name} />
                        {:else}
                          {initials(member)}
                        {/if}
                      </div>
                      <div class="member-info">
                        <span class="member-name">{member.first_name} {member.last_name}</span>
                        {#if member.designation}
                          <span class="member-sub">{humanise(member.designation)}</span>
                        {/if}
                      </div>
                    </div>
                  </td>
                  <td class="mono">{member.staff_id ?? member.ges_staff_id ?? "—"}</td>
                  <td>
                    <Badge variant={categoryColor(member.category)}>
                      {CATEGORY_LABELS[member.category] ?? member.category}
                    </Badge>
                  </td>
                  <td class="text-muted">{humanise(member.employment_type)}</td>
                  <td class="text-muted">
                    {member.current_rank ?? (member.designation ? humanise(member.designation) : "—")}
                  </td>
                  <td>
                    {#if member.has_account}
                      <span class="account-yes"><Check size={12} /> Active</span>
                    {:else}
                      <span class="account-no">No account</span>
                    {/if}
                  </td>
                  <td>
                    <Badge variant={member.is_active ? "ok" : "neutral"}>
                      {member.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        {#if total > LIMIT}
          <div class="pagination">
            <span class="page-info">{pageStart}–{pageEnd} of {total.toLocaleString()}</span>
            <button class="page-btn" on:click={prevPage} disabled={skip === 0} aria-label="Previous page">
              <ChevronLeft size={14} />
            </button>
            <button class="page-btn" on:click={nextPage} disabled={skip + LIMIT >= total} aria-label="Next page">
              <ChevronRight size={14} />
            </button>
          </div>
        {/if}
      {/if}
    </div>

  </div>
</div>


<style>
  .page { display: flex; flex-direction: column; gap: 0; }

  /* ── Staff card ──────────────────────────────────────────────── */
  .staff-card {
    background: var(--surface-0);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  /* ── Card header ─────────────────────────────────────────────── */
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 14px 20px;
    border-bottom: 1px solid var(--border-subtle);
    background: var(--surface-1);
    flex-wrap: wrap;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .header-icon {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    background: var(--accent-subtle);
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .card-title {
    font-size: 0.9375rem;
    font-weight: 700;
    color: var(--tx-high);
    margin: 0;
  }

  .count-chip {
    display: inline-flex;
    align-items: center;
    padding: 2px 9px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    background: var(--surface-2);
    color: var(--tx-low);
    border: 1px solid var(--border-subtle);
  }

  .header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  /* ── Filter bar ──────────────────────────────────────────────── */
  .filter-bar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    align-items: center;
    padding: 12px 20px;
    border-bottom: 1px solid var(--border-subtle);
    background: var(--surface-0);
  }

  .search-wrap {
    position: relative;
    flex: 1;
    min-width: 200px;
  }

  .search-wrap :global(.search-icon) {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--tx-low);
    pointer-events: none;
  }

  .search-input { padding-left: 32px !important; }

  .filter-select { width: auto; flex-shrink: 0; }

  /* ── Card body ───────────────────────────────────────────────── */
  .card-body {
    flex: 1;
    min-height: 200px;
  }

  /* ── Table ───────────────────────────────────────────────────── */
  .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }

  .staff-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }

  .staff-table thead tr {
    background: var(--surface-2);
  }

  .staff-table th {
    text-align: left;
    padding: 9px 16px;
    font-size: 0.6875rem;
    font-weight: 600;
    color: var(--tx-low);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1px solid var(--border-subtle);
    white-space: nowrap;
  }

  .staff-table td {
    padding: 11px 16px;
    border-bottom: 1px solid color-mix(in srgb, var(--border-subtle) 60%, transparent);
    vertical-align: middle;
    color: var(--tx-high);
  }

  .staff-row { cursor: pointer; transition: background 0.1s; }
  .staff-row:hover { background: var(--surface-1); }
  .staff-row:last-child td { border-bottom: none; }

  /* ── Member cell ─────────────────────────────────────────────── */
  .member-cell {
    display: flex;
    align-items: center;
    gap: 11px;
  }

  .avatar {
    width: 34px;
    height: 34px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    color: #fff;
    flex-shrink: 0;
    overflow: hidden;
    background: var(--accent);
  }

  .avatar[data-cat="TEACHING"]     { background: #3b82f6; }
  .avatar[data-cat="NON-TEACHING"] { background: #8b5cf6; }
  .avatar img { width: 100%; height: 100%; object-fit: cover; }

  .member-info {
    display: flex;
    flex-direction: column;
    gap: 1px;
    min-width: 0;
  }

  .member-name {
    font-weight: 600;
    color: var(--tx-high);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .member-sub {
    font-size: 0.75rem;
    color: var(--tx-low);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .mono { font-family: ui-monospace, monospace; font-size: 0.8125rem; color: var(--tx-mid); }
  .text-muted { color: var(--tx-mid); font-size: 0.8125rem; }

  .account-yes {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    color: #059669;
    font-weight: 500;
  }

  .account-no {
    font-size: 0.75rem;
    color: var(--tx-low);
  }

  /* ── Centered state ──────────────────────────────────────────── */
  .centered-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 64px 24px;
    color: var(--tx-low);
  }

  .centered-state :global(.error-icon) { color: #ef4444; }
  .error-text { margin: 0; font-size: 0.9rem; color: var(--tx-mid); }

  /* ── Pagination ──────────────────────────────────────────────── */
  .pagination {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 6px;
    padding: 10px 16px;
    border-top: 1px solid var(--border-subtle);
    background: var(--surface-1);
  }

  .page-info {
    font-size: 0.8125rem;
    color: var(--tx-low);
    margin-right: 4px;
  }

  .page-btn {
    width: 30px;
    height: 30px;
    border-radius: 6px;
    border: 1px solid var(--border-subtle);
    background: var(--surface-0);
    color: var(--tx-mid);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.12s, border-color 0.12s;
  }
  .page-btn:hover:not(:disabled) {
    background: var(--surface-2);
    border-color: var(--border-strong);
  }
  .page-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  /* ── Inputs ──────────────────────────────────────────────────── */
  .input {
    height: 34px;
    padding: 0 10px;
    border: 1px solid var(--border-strong);
    border-radius: 7px;
    font-size: 0.875rem;
    background: var(--surface-0);
    color: var(--tx-high);
    font-family: inherit;
    outline: none;
    box-sizing: border-box;
    transition: border-color 0.12s, box-shadow 0.12s;
  }
  .input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent);
  }
  select.input { cursor: pointer; }
</style>
