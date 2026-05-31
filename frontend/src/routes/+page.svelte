<script lang="ts">
  import { goto } from "$app/navigation";
  import { auth, isAuthenticated } from "$stores/auth";
  import { onMount } from "svelte";

  onMount(() => {
    // Wait for auth hydration to finish before deciding where to send the user.
    // Checking $isAuthenticated immediately always reads false (initial loading state).
    const unsub = auth.subscribe(state => {
      if (state.loading) return;
      unsub();
      goto($isAuthenticated ? "/dashboard" : "/login");
    });
  });
</script>
