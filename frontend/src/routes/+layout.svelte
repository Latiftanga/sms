<script lang="ts">
  import "../app.css";
  import { onMount } from "svelte";
  import { QueryClient, QueryClientProvider } from "@tanstack/svelte-query";
  import { auth } from "$stores/auth";
  import { schoolBranding } from "$stores/school";

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5,
        retry: 1,
      },
    },
  });

  onMount(async () => {
    // Load school branding first so login page and app both get accent + logo
    await schoolBranding.load();
    await auth.init();
  });
</script>

<QueryClientProvider client={queryClient}>
  <slot />
</QueryClientProvider>
