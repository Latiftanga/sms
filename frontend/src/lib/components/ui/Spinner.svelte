<script lang="ts">
  import { Loader2 } from "@lucide/svelte";
  export let size = 18;
  export let label = "Loading…";
</script>

<span class="spinner" aria-label={label} role="status">
  <Loader2 {size} class="spin" />
</span>

<style>
  .spinner {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: var(--tx-low);
  }
  :global(.spin) { animation: _spin 0.7s linear infinite; }
  @keyframes _spin { to { transform: rotate(360deg); } }
</style>
