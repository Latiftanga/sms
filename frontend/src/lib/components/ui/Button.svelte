<script lang="ts">
  import { Loader2 } from "@lucide/svelte";

  export let variant: "primary" | "ghost" | "danger" | "danger-ghost" | "link" | "icon" = "primary";
  export let size: "sm" | "md" = "md";
  export let type: "button" | "submit" | "reset" = "button";
  export let disabled = false;
  export let loading = false;
  export let ariaLabel: string | undefined = undefined;
</script>

<button
  {type}
  class="btn btn-{variant} btn-{size}"
  disabled={disabled || loading}
  aria-label={ariaLabel}
  on:click
  on:mousedown
>
  {#if loading}<Loader2 size={12} class="spin" />{/if}
  <slot />
</button>

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border: 1px solid transparent;
    border-radius: 7px;
    font-family: inherit;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.12s, color 0.12s, border-color 0.12s, box-shadow 0.12s, opacity 0.12s;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .btn:disabled { opacity: 0.5; cursor: not-allowed; pointer-events: none; }
  .btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

  /* Sizes */
  .btn-sm { height: 28px; padding: 0 10px; font-size: 12px; }
  .btn-md { height: 32px; padding: 0 13px; font-size: 13px; }

  /* Variants */
  .btn-primary {
    background: var(--accent);
    color: var(--accent-fg);
    border-color: var(--accent);
  }
  .btn-primary:not(:disabled):hover {
    background: var(--accent-hover);
    border-color: var(--accent-hover);
  }

  .btn-ghost {
    background: transparent;
    color: var(--tx-mid);
    border-color: var(--border-strong);
  }
  .btn-ghost:not(:disabled):hover {
    background: var(--surface-2);
    color: var(--tx-high);
    border-color: color-mix(in srgb, var(--border-strong) 60%, var(--accent));
  }

  .btn-danger {
    background: #dc2626;
    color: #fff;
    border-color: #dc2626;
  }
  .btn-danger:not(:disabled):hover {
    background: #b91c1c;
    border-color: #b91c1c;
  }

  .btn-danger-ghost {
    background: transparent;
    color: #dc2626;
    border-color: color-mix(in srgb, #dc2626 35%, transparent);
  }
  .btn-danger-ghost:not(:disabled):hover {
    background: color-mix(in srgb, #dc2626 8%, transparent);
    border-color: #dc2626;
  }

  .btn-link {
    background: transparent;
    color: var(--accent);
    border-color: transparent;
    padding: 0;
    height: auto;
    font-weight: 500;
    font-size: 12px;
  }
  .btn-link:not(:disabled):hover { text-decoration: underline; }

  .btn-icon {
    background: transparent;
    color: var(--tx-low);
    border-color: transparent;
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 6px;
  }
  .btn-icon:not(:disabled):hover {
    background: var(--surface-2);
    color: var(--tx-high);
    border-color: var(--border-strong);
  }
</style>
