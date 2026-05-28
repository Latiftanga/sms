<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { X } from "@lucide/svelte";
  import Button from "./Button.svelte";

  export let open = false;
  export let title = "";
  export let description = "";
  export let confirmLabel = "Confirm";
  export let cancelLabel = "Cancel";
  export let variant: "default" | "danger" = "default";
  export let loading = false;
  export let hideCancel = false;
  export let noFooter = false;

  const dispatch = createEventDispatcher<{ confirm: void; cancel: void }>();

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape" && !loading) dispatch("cancel");
  }
</script>

<svelte:window on:keydown={open ? handleKeydown : undefined} />

{#if open}
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <div class="overlay" on:click|self={() => !loading && dispatch("cancel")}>
    <div
      class="panel"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div class="modal-header">
        <h3 class="modal-title" id="modal-title">{title}</h3>
        {#if !loading}
          <button
            class="close-btn"
            on:click={() => dispatch("cancel")}
            aria-label="Close dialog"
          >
            <X size={14} />
          </button>
        {/if}
      </div>

      {#if description || $$slots.default}
        <div class="modal-body">
          {#if description}<p class="modal-desc">{description}</p>{/if}
          <slot />
        </div>
      {/if}

      {#if !noFooter}
        <div class="modal-footer">
          {#if !hideCancel}
            <Button variant="ghost" size="sm" disabled={loading} on:click={() => dispatch("cancel")}>
              {cancelLabel}
            </Button>
          {/if}
          <Button
            variant={variant === "danger" ? "danger" : "primary"}
            size="sm"
            {loading}
            on:click={() => dispatch("confirm")}
          >
            {confirmLabel}
          </Button>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 200;
    padding: 20px;
    backdrop-filter: blur(2px);
    animation: fade-in 0.12s ease;
  }

  @keyframes fade-in {
    from { opacity: 0; }
    to   { opacity: 1; }
  }

  .panel {
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    box-shadow: var(--shadow-md);
    width: 100%;
    max-width: 420px;
    animation: slide-up 0.15s ease;
    overflow: hidden;
  }

  @keyframes slide-up {
    from { transform: translateY(10px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 18px 14px;
    border-bottom: 1px solid var(--border-subtle);
  }

  .modal-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--tx-high);
    margin: 0;
  }

  .close-btn {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
    border-radius: 5px;
    color: var(--tx-low);
    cursor: pointer;
    transition: background 0.1s, color 0.1s;
  }
  .close-btn:hover { background: var(--surface-2); color: var(--tx-high); }

  .modal-body { padding: 16px 18px; }
  .modal-desc {
    font-size: 13.5px;
    color: var(--tx-mid);
    line-height: 1.6;
    margin: 0;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 12px 18px;
    border-top: 1px solid var(--border-subtle);
    background: var(--surface-0);
  }
</style>
