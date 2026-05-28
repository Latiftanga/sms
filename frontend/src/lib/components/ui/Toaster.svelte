<script lang="ts">
  import { toast } from "$stores/toast";
  import ToastItem from "./Toast.svelte";
</script>

<div class="toaster" aria-label="Notifications" aria-live="polite">
  {#each $toast as item (item.id)}
    <ToastItem
      id={item.id}
      message={item.message}
      variant={item.variant}
      on:dismiss={(e) => toast.remove(e.detail)}
    />
  {/each}
</div>

<style>
  .toaster {
    position: fixed;
    bottom: 24px;
    /* Stay 24px inside the 1280px UI column — on wide viewports offset by half the excess */
    right: max(24px, calc((100vw - 1280px) / 2 + 24px));
    display: flex;
    flex-direction: column;
    gap: 10px;
    z-index: 9999;
    pointer-events: none;
    align-items: flex-end;
  }

  @media (max-width: 480px) {
    .toaster {
      bottom: 16px;
      right: 12px;
      left: 12px;
      align-items: stretch;
    }
  }
</style>
