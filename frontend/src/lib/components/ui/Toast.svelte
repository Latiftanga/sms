<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from "@lucide/svelte";
  import type { ToastVariant } from "$stores/toast";

  export let id: string;
  export let message: string;
  export let variant: ToastVariant;

  const dispatch = createEventDispatcher<{ dismiss: string }>();

  const icons = {
    success: CheckCircle2,
    error:   AlertCircle,
    warning: AlertTriangle,
    info:    Info,
  };

  $: Icon = icons[variant];
</script>

<div class="toast toast-{variant}" role="alert" aria-live="assertive">
  <span class="toast-icon"><svelte:component this={Icon} size={15} /></span>
  <span class="toast-msg">{message}</span>
  <button class="toast-close" on:click={() => dispatch("dismiss", id)} aria-label="Dismiss">
    <X size={13} />
  </button>
</div>

<style>
  .toast {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 11px 14px;
    border-radius: 9px;
    border: 1px solid transparent;
    box-shadow: var(--shadow-md);
    font-size: 13px;
    line-height: 1.5;
    min-width: 260px;
    max-width: 380px;
    animation: toast-in 0.2s cubic-bezier(0.34, 1.36, 0.64, 1);
    pointer-events: all;
  }

  @keyframes toast-in {
    from { transform: translateX(20px); opacity: 0; }
    to   { transform: translateX(0);    opacity: 1; }
  }

  .toast-success {
    background: var(--ok-bg);
    color: var(--ok-text);
    border-color: color-mix(in srgb, var(--ok-text) 18%, transparent);
  }
  .toast-error {
    background: var(--err-bg);
    color: var(--err-text);
    border-color: color-mix(in srgb, var(--err-text) 18%, transparent);
  }
  .toast-warning {
    background: var(--warn-bg);
    color: var(--warn-text);
    border-color: color-mix(in srgb, var(--warn-text) 18%, transparent);
  }
  .toast-info {
    background: var(--accent-subtle);
    color: var(--accent);
    border-color: var(--accent-border);
  }

  .toast-icon { flex-shrink: 0; margin-top: 1px; }
  .toast-msg  { flex: 1; }

  .toast-close {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
    border-radius: 4px;
    cursor: pointer;
    opacity: 0.65;
    color: inherit;
    transition: opacity 0.1s, background 0.1s;
  }
  .toast-close:hover { opacity: 1; background: color-mix(in srgb, currentColor 10%, transparent); }
</style>
