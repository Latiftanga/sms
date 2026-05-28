<script lang="ts">
  export let title: string;
  export let description: string = "";
</script>

<div class="page-head">
  <div class="page-head-text">
    <h1 class="page-title">{title}</h1>
    {#if description}<p class="page-desc">{description}</p>{/if}
  </div>
  {#if $$slots.default}
    <div class="page-head-actions">
      <slot />
    </div>
  {/if}
</div>

<style>
  .page-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  .page-title { font-size: 15px; font-weight: 600; color: var(--tx-high); margin: 0 0 3px; }
  .page-desc  { font-size: 12.5px; color: var(--tx-low); margin: 0; }
  .page-head-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
</style>
