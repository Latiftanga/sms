<script lang="ts">
  import { confirmDialog } from "$stores/confirm";
  import { AlertTriangle, Info } from "@lucide/svelte";
  import Button from "./Button.svelte";

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape" && $confirmDialog.open && !$confirmDialog.loading) {
      confirmDialog.respond(false);
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if $confirmDialog.open}
  <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
  <div
    class="overlay"
    on:click|self={() => !$confirmDialog.loading && confirmDialog.respond(false)}
  >
    <div class="panel" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title">

      <div class="panel-body">
        <div class="icon-wrap" class:danger={$confirmDialog.options.variant === "danger"}>
          {#if $confirmDialog.options.variant === "danger"}
            <AlertTriangle size={20} />
          {:else}
            <Info size={20} />
          {/if}
        </div>

        <div class="text">
          <p class="title" id="confirm-title">{$confirmDialog.options.title}</p>
          {#if $confirmDialog.options.message}
            <p class="message">{$confirmDialog.options.message}</p>
          {/if}
        </div>
      </div>

      <div class="panel-footer">
        <Button
          variant="ghost"
          size="sm"
          disabled={$confirmDialog.loading}
          on:click={() => confirmDialog.respond(false)}
        >
          {$confirmDialog.options.cancelLabel ?? "Cancel"}
        </Button>
        <Button
          variant={$confirmDialog.options.variant === "danger" ? "danger" : "primary"}
          size="sm"
          loading={$confirmDialog.loading}
          on:click={() => confirmDialog.respond(true)}
        >
          {$confirmDialog.options.confirmLabel ?? "Confirm"}
        </Button>
      </div>
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
    z-index: 300;
    padding: 20px;
    backdrop-filter: blur(2px);
    animation: fade-in 0.1s ease;
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
    max-width: 380px;
    animation: slide-up 0.14s ease;
    overflow: hidden;
  }

  @keyframes slide-up {
    from { transform: translateY(8px); opacity: 0; }
    to   { transform: translateY(0);   opacity: 1; }
  }

  .panel-body {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 20px 20px 16px;
  }

  .icon-wrap {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    background: color-mix(in srgb, var(--accent) 12%, transparent);
    color: var(--accent);
  }

  .icon-wrap.danger {
    background: color-mix(in srgb, #ef4444 12%, transparent);
    color: #ef4444;
  }

  .text { display: flex; flex-direction: column; gap: 4px; padding-top: 2px; }

  .title {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--tx-high);
    line-height: 1.4;
  }

  .message {
    margin: 0;
    font-size: 0.8125rem;
    color: var(--tx-low);
    line-height: 1.55;
  }

  .panel-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 12px 20px;
    border-top: 1px solid var(--border-subtle);
    background: var(--surface-0);
  }
</style>
