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

    // Refresh when the user returns to this tab, debounced to avoid request
    // storms from rapid tab switching.
    let visibilityTimer: ReturnType<typeof setTimeout> | null = null;
    function onVisibilityChange() {
      if (document.visibilityState !== "visible") return;
      if (visibilityTimer) clearTimeout(visibilityTimer);
      visibilityTimer = setTimeout(() => auth.refresh(), 500);
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
