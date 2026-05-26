<script lang="ts">
  import "../app.css";
  import { onMount } from "svelte";
  import { QueryClient, QueryClientProvider } from "@tanstack/svelte-query";
  import { auth } from "$stores/auth";

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5,
        retry: 1,
      },
    },
  });

  onMount(async () => {
    await auth.init();
  });
</script>

<QueryClientProvider client={queryClient}>
  <slot />
</QueryClientProvider>
