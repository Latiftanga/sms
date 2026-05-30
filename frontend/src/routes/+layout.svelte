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

  function dismissInitOverlay() {
    const el = document.getElementById("app-init");
    if (!el) return;
    el.style.opacity = "0";
    el.addEventListener("transitionend", () => el.remove(), { once: true });
  }

  onMount(async () => {
    // Load school branding first so login page and app both get accent + logo
    await schoolBranding.load();
    await auth.init();
    dismissInitOverlay();

    // Refresh permissions silently every 12 minutes so they stay current across
    // the 15-minute access-token window without ever wiping the nav on failure.
    const interval = setInterval(() => auth.refresh(), 12 * 60 * 1000);

    // Also refresh when the user returns to this tab after being away.
    function onVisibilityChange() {
      if (document.visibilityState === "visible") auth.refresh();
    }
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  });
</script>

<QueryClientProvider client={queryClient}>
  <slot />
</QueryClientProvider>
