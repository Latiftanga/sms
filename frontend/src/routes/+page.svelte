<script lang="ts">
  import { goto } from "$app/navigation";
  import { isAuthenticated } from "$stores/auth";
  import { onMount } from "svelte";

  onMount(() => {
    if ($isAuthenticated) {
      goto("/dashboard");
    } else {
      goto("/login");
    }
  });
</script>
