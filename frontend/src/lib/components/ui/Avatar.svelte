<script lang="ts">
  export let name: string = "?";
  export let src: string | null = null;
  export let size: "xs" | "sm" | "md" | "lg" = "sm";

  $: initial = name.trim().charAt(0).toUpperCase() || "?";
</script>

<div class="avatar avatar-{size}" aria-hidden="true">
  {#if src}
    <img {src} alt={name} />
  {:else}
    <span>{initial}</span>
  {/if}
</div>

<style>
  .avatar {
    border-radius: 50%;
    background: var(--accent-subtle);
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    flex-shrink: 0;
    overflow: hidden;
  }

  .avatar img { width: 100%; height: 100%; object-fit: cover; }

  .avatar-xs { width: 22px; height: 22px; font-size: 9px; }
  .avatar-sm { width: 28px; height: 28px; font-size: 11px; }
  .avatar-md { width: 36px; height: 36px; font-size: 14px; }
  .avatar-lg { width: 48px; height: 48px; font-size: 18px; }
</style>
