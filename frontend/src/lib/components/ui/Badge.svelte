<script lang="ts">
  export let variant: "ok" | "warn" | "error" | "neutral" | "accent" = "neutral";
  export let size: "sm" | "md" = "md";
</script>

<span class="badge badge-{variant} badge-{size}">
  <slot />
</span>

<style>
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 5px;
    font-weight: 500;
    white-space: nowrap;
  }

  .badge-sm { font-size: 10.5px; padding: 1px 6px; }
  .badge-md { font-size: 11.5px; padding: 2px 8px; }

  .badge-ok      { background: var(--ok-bg);   color: var(--ok-text); }
  .badge-warn    { background: var(--warn-bg);  color: var(--warn-text); }
  .badge-error   { background: var(--err-bg);   color: var(--err-text); }
  .badge-accent  { background: var(--accent-subtle); color: var(--accent); }
  .badge-neutral {
    background: var(--surface-2);
    color: var(--tx-low);
    border: 1px solid var(--border-subtle);
  }
</style>
