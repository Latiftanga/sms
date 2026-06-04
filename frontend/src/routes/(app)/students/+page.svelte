<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { api } from "$api/client";
  import { auth } from "$stores/auth";
  import { schoolBranding } from "$stores/school";
  import Badge from "$components/ui/Badge.svelte";
  import Button from "$components/ui/Button.svelte";
  import {
    UserPlus, Upload, Search, ChevronLeft, ChevronRight,
    Users, AlertCircle,
  } from "@lucide/svelte";

  interface StudentListItem {
    id: string;
    first_name: string; middle_name: string | null; last_name: string;
    gender: string; photo_url: string | null; is_active: boolean;
    admission_number: string | null;
    register_number: string | null; class_name: string | null;
    class_id: string | null; year_name: string | null;
  }
  interface PagedResponse { items: StudentListItem[]; total: number; skip: number; limit: number; }
  interface ClassItem { id: string; name: string; }

  $: canEnroll = $auth.user?.permissions?.enroll_students === true
    || $auth.user?.system_role === "SUPERADMIN";

  let students: StudentListItem[] = [];
  let total = 0;
  let skip = 0;
  const LIMIT = 25;
  let loading = true;
  let error = "";

  let search = "";
  let filterClass = "";
  let classes: ClassItem[] = [];

  let searchTimer: ReturnType<typeof setTimeout>;

  async function loadClasses() {
    try {
      const { data } = await api.get<{ items: ClassItem[] }>("/settings/classes", { params: { limit: 200 } });
      classes = data.items;
    } catch { /* non-fatal */ }
  }

  async function load() {
    loading = true; error = "";
    try {
      const params: Record<string, string | number> = { skip, limit: LIMIT };
      if (search) params.search = search;
      if (filterClass) params.class_id = filterClass;
      const { data } = await api.get<PagedResponse>("/students", { params });
      students = data.items;
      total = data.total;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      error = err?.response?.data?.detail ?? "Failed to load students.";
    } finally {
      loading = false;
    }
  }

  function onSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { skip = 0; load(); }, 320);
  }

  function onFilter() { skip = 0; load(); }
  function prev() { if (skip >= LIMIT) { skip -= LIMIT; load(); } }
  function next() { if (skip + LIMIT < total) { skip += LIMIT; load(); } }

  onMount(() => { loadClasses(); load(); });

  function initials(s: StudentListItem) {
    return (s.first_name[0] + s.last_name[0]).toUpperCase();
  }

  $: totalPages = Math.ceil(total / LIMIT);
  $: currentPage = Math.floor(skip / LIMIT) + 1;
</script>

<svelte:head><title>Students — {$schoolBranding?.name ?? "TTEK SMS"}</title></svelte:head>

<!-- ── Header ─────────────────────────────────────────────────────── -->
<div class="page-header">
  <div>
    <h1 class="page-title">Students</h1>
    {#if !loading}<p class="page-sub">{total} student{total !== 1 ? "s" : ""} enrolled</p>{/if}
  </div>
  {#if canEnroll}
    <div class="header-actions">
      <Button variant="ghost" size="sm" on:click={() => goto("/students/import")}>
        <Upload size={13} /> Bulk Import
      </Button>
      <Button size="sm" on:click={() => goto("/students/new")}>
        <UserPlus size={13} /> Add Student
      </Button>
    </div>
  {/if}
</div>

<!-- ── Filters ────────────────────────────────────────────────────── -->
<div class="filters">
  <div class="search-wrap">
    <Search size={13} class="search-icon" />
    <input
      class="search-input"
      type="text"
      placeholder="Search by name…"
      bind:value={search}
      on:input={onSearch}
    />
  </div>

  <select class="filter-select" bind:value={filterClass} on:change={onFilter}>
    <option value="">All classes</option>
    {#each classes as c}
      <option value={c.id}>{c.name}</option>
    {/each}
  </select>
</div>

<!-- ── Content ────────────────────────────────────────────────────── -->
{#if error}
  <div class="error-banner"><AlertCircle size={14} />{error}</div>
{:else if loading}
  <div class="table-wrap">
    <table class="table">
      <thead><tr>
        <th>Student</th><th>Register No.</th><th>Class</th><th>Gender</th><th></th>
      </tr></thead>
      <tbody>
        {#each [1,2,3,4,5] as _}
          <tr>
            <td><div class="sk-row"><div class="skeleton sk-avatar"></div><div class="skeleton sk-name"></div></div></td>
            <td><div class="skeleton sk-reg"></div></td>
            <td><div class="skeleton sk-class"></div></td>
            <td><div class="skeleton sk-chip"></div></td>
            <td></td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

{:else if students.length === 0}
  <div class="empty-state">
    <div class="empty-icon"><Users size={28} /></div>
    <p class="empty-title">
      {search || filterClass ? "No students match your filters" : "No students enrolled yet"}
    </p>
    <p class="empty-body">
      {#if !search && !filterClass && canEnroll}
        Start building your class register by adding students.
      {:else if !search && !filterClass}
        Students will appear here once enrolled.
      {:else}
        Try adjusting your search or filter.
      {/if}
    </p>
    {#if canEnroll && !search && !filterClass}
      <a href="/students/new" class="btn-primary" style="margin-top:8px">
        <UserPlus size={14} /> Add First Student
      </a>
    {/if}
  </div>

{:else}
  <div class="table-wrap">
    <table class="table">
      <thead>
        <tr>
          <th>Student</th>
          <th>Register No.</th>
          <th>Class</th>
          <th>Gender</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {#each students as s (s.id)}
          <tr on:click={() => goto(`/students/${s.id}`)} class="clickable">
            <td>
              <div class="student-cell">
                {#if s.photo_url}
                  <img src={s.photo_url} alt={s.first_name} class="avatar-img" />
                {:else}
                  <div class="avatar">{initials(s)}</div>
                {/if}
                <div>
                  <div class="student-name">
                    {s.last_name}, {s.first_name}{s.middle_name ? ` ${s.middle_name}` : ""}
                  </div>
                  {#if s.admission_number}
                    <div class="student-sub">Adm. {s.admission_number}</div>
                  {/if}
                </div>
              </div>
            </td>
            <td class="mono">{s.register_number ?? "—"}</td>
            <td>
              {#if s.class_name}
                <Badge variant="subtle">{s.class_name}</Badge>
              {:else}
                <span class="not-enrolled">Not enrolled</span>
              {/if}
            </td>
            <td>
              <Badge variant={s.gender === "MALE" ? "accent" : "neutral"}>
                {s.gender === "MALE" ? "M" : "F"}
              </Badge>
            </td>
            <td class="action-col">
              <a href="/students/{s.id}" class="row-link" on:click|stopPropagation>
                View
              </a>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <!-- Pagination -->
  {#if total > LIMIT}
    <div class="pagination">
      <span class="pag-info">
        {skip + 1}–{Math.min(skip + LIMIT, total)} of {total}
      </span>
      <div class="pag-btns">
        <button class="pag-btn" disabled={skip === 0} on:click={prev}>
          <ChevronLeft size={14} />
        </button>
        <span class="pag-page">{currentPage} / {totalPages}</span>
        <button class="pag-btn" disabled={skip + LIMIT >= total} on:click={next}>
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  {/if}
{/if}

<style>
.page-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 12px; margin-bottom: 18px; flex-wrap: wrap;
}
.page-title { font-size: 18px; font-weight: 700; color: var(--tx-high); margin: 0 0 2px; }
.page-sub   { font-size: 13px; color: var(--tx-low); margin: 0; }

.header-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px; border-radius: 8px; font-size: 13px; font-weight: 500;
  background: var(--accent); color: var(--accent-fg, #fff);
  text-decoration: none; border: none; cursor: pointer; white-space: nowrap;
  transition: opacity 0.15s;
}
.btn-primary:hover { opacity: 0.88; }

/* Filters */
.filters {
  display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap;
}
.search-wrap {
  position: relative; flex: 1; min-width: 200px;
}
.search-wrap :global(.search-icon) {
  position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
  color: var(--tx-low); pointer-events: none;
}
.search-input {
  width: 100%; padding: 7px 10px 7px 30px;
  border: 1px solid var(--border-subtle); border-radius: 8px;
  background: var(--surface-1); color: var(--tx-high); font-size: 13px;
  outline: none;
}
.search-input:focus { border-color: var(--accent); }
.filter-select {
  padding: 7px 10px; border: 1px solid var(--border-subtle);
  border-radius: 8px; background: var(--surface-1); color: var(--tx-high);
  font-size: 13px; outline: none; cursor: pointer; min-width: 140px;
}
.filter-select:focus { border-color: var(--accent); }

/* Table */
.table-wrap {
  background: var(--surface-1); border: 1px solid var(--border-subtle);
  border-radius: 12px; overflow: hidden; box-shadow: var(--shadow-xs);
}
.table { width: 100%; border-collapse: collapse; }
.table thead th {
  padding: 11px 16px; text-align: left;
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--tx-low);
  background: var(--surface-0); border-bottom: 1px solid var(--border-subtle);
  white-space: nowrap;
}
.table tbody tr { border-top: 1px solid var(--border-subtle); }
.table tbody tr:first-child { border-top: none; }
.table tbody td { padding: 11px 16px; font-size: 13px; color: var(--tx-mid); }
.clickable { cursor: pointer; transition: background 0.1s; }
.clickable:hover { background: var(--surface-2); }

.student-cell { display: flex; align-items: center; gap: 10px; }
.avatar {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  background: var(--accent-subtle); color: var(--accent);
  font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.avatar-img { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.student-name { font-size: 13px; font-weight: 500; color: var(--tx-high); }
.student-sub  { font-size: 11px; color: var(--tx-low); margin-top: 1px; }

.mono { font-family: monospace; font-size: 12px; color: var(--tx-mid); }
.not-enrolled { font-size: 12px; color: var(--tx-low); font-style: italic; }
.action-col { width: 60px; text-align: right; }
.row-link {
  font-size: 12px; font-weight: 500; color: var(--accent);
  text-decoration: none; padding: 4px 8px; border-radius: 6px;
  transition: background 0.1s;
}
.row-link:hover { background: var(--accent-subtle); }

/* Pagination */
.pagination {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-top: 1px solid var(--border-subtle);
  font-size: 12px; color: var(--tx-low);
}
.pag-btns { display: flex; align-items: center; gap: 6px; }
.pag-btn {
  width: 28px; height: 28px; border-radius: 7px;
  border: 1px solid var(--border-subtle); background: var(--surface-1);
  color: var(--tx-mid); cursor: pointer; display: flex; align-items: center;
  justify-content: center; transition: background 0.1s;
}
.pag-btn:hover:not(:disabled) { background: var(--surface-2); }
.pag-btn:disabled { opacity: 0.4; cursor: default; }
.pag-page { font-size: 12px; color: var(--tx-mid); padding: 0 4px; }

/* Error */
.error-banner {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; border-radius: 10px; font-size: 13px;
  background: color-mix(in srgb, #ef4444 10%, transparent);
  color: #dc2626; border: 1px solid color-mix(in srgb, #ef4444 25%, transparent);
  margin-bottom: 12px;
}

/* Empty state */
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  text-align: center; padding: 64px 32px; gap: 10px;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 14px;
  background: var(--surface-2); color: var(--tx-low);
  display: flex; align-items: center; justify-content: center; margin-bottom: 4px;
}
.empty-title { font-size: 15px; font-weight: 600; color: var(--tx-high); margin: 0; }
.empty-body  { font-size: 13px; color: var(--tx-low); margin: 0; max-width: 360px; line-height: 1.55; }

/* Skeletons */
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position:  400px 0; }
}
.skeleton {
  background: linear-gradient(90deg, var(--surface-2) 25%, var(--border-subtle) 50%, var(--surface-2) 75%);
  background-size: 800px 100%; animation: shimmer 1.4s infinite linear; border-radius: 6px;
}
.sk-row    { display: flex; align-items: center; gap: 10px; }
.sk-avatar { width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0; }
.sk-name   { height: 13px; width: 140px; }
.sk-reg    { height: 13px; width: 100px; }
.sk-class  { height: 20px; width: 80px; border-radius: 99px; }
.sk-chip   { height: 20px; width: 28px; border-radius: 99px; }
</style>
