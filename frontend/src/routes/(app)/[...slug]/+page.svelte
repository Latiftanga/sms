<script lang="ts">
  import { page } from "$app/stores";
  import { Construction } from "@lucide/svelte";
</script>

<svelte:head>
  <title>Coming Soon — TTEK-SIS</title>
</svelte:head>

<div style="
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  min-height:60vh; text-align:center; gap:16px;
">
  <div style="
    width:48px; height:48px; border-radius:12px;
    background:var(--accent-subtle);
    display:flex; align-items:center; justify-content:center;
    color:var(--accent);
  ">
    <Construction size={22} />
  </div>

  <div>
    <h2 style="font-size:15px; font-weight:600; color:var(--tx-high); margin-bottom:6px;">
      Not yet available
    </h2>
    <p style="font-size:13px; color:var(--tx-low); max-width:320px; line-height:1.6;">
      <code style="
        font-size:12px; padding:1px 6px; border-radius:4px;
        background:var(--surface-2); color:var(--tx-mid);
      ">/{$page.params.slug}</code>
      is coming in a future release.
    </p>
  </div>
</div>
