<script lang="ts">
  /** Optional: show a card-header section above the body */
  export let title: string = "";
  export let description: string = "";
  export let noPad = false;
</script>

<div class="card">
  {#if title || $$slots.header}
    <div class="card-header">
      {#if $$slots.icon}
        <div class="card-hicon">
          <slot name="icon" />
        </div>
      {/if}
      <div class="card-header-text">
        {#if title}<h2 class="card-title">{title}</h2>{/if}
        {#if description}<p class="card-desc">{description}</p>{/if}
        <slot name="header" />
      </div>
    </div>
  {/if}
  <div class="card-body" class:no-pad={noPad}>
    <slot />
  </div>
</div>

<style>
  .card {
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    box-shadow: var(--shadow-xs);
    overflow: hidden;
    transition: box-shadow 0.15s;
  }
  .card:focus-within {
    box-shadow: 0 0 0 1px var(--accent-border), var(--shadow-sm);
  }

  .card-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 14px 20px;
    background: var(--surface-0);
    border-bottom: 1px solid var(--border-subtle);
  }

  .card-hicon {
    width: 30px;
    height: 30px;
    border-radius: 7px;
    background: var(--accent-subtle);
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 1px;
  }

  .card-header-text { flex: 1; min-width: 0; }
  .card-title { font-size: 13px; font-weight: 600; color: var(--tx-high); margin: 0 0 2px; }
  .card-desc  { font-size: 12px; color: var(--tx-low); margin: 0; line-height: 1.5; }

  .card-body { padding: 16px 20px; }
  .card-body.no-pad { padding: 0; }
</style>
