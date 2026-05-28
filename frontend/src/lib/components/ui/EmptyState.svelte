<script lang="ts">
  export let message: string = "Nothing here yet.";
  export let bordered = true;
</script>

<div class="empty" class:bordered>
  <slot name="icon" />
  <p class="msg">{message}</p>
  <slot />
</div>

<style>
  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 48px 20px;
    text-align: center;
    color: var(--tx-low);
    border-radius: 10px;
    background: var(--surface-1);
  }
  .empty.bordered {
    border: 1.5px dashed var(--border-strong);
  }
  .msg { font-size: 13.5px; color: var(--tx-mid); margin: 0; }
</style>
