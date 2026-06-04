import { sveltekit } from "@sveltejs/kit/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    tailwindcss(),
    sveltekit(),
    VitePWA({
      registerType: "autoUpdate",
      devOptions: { enabled: false },
      workbox: {
        // Never cache API endpoints — all require Authorization headers.
        // Caching them causes Workbox to strip auth headers or serve stale 401s.
        runtimeCaching: [],
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2}"],
        navigateFallback: null,
      },
      manifest: {
        name: "TTEK-SIS",
        short_name: "TTEK-SIS",
        description: "Tagnatek School Information System",
        theme_color: "#5B7FFF",
        background_color: "#09090F",
        display: "standalone",
        orientation: "portrait",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
        ],
      },
    }),
  ],
  server: {
    proxy: {
      "/api": {
        target: process.env.API_TARGET || "http://localhost:8000",
        changeOrigin: true,
        // Strip the Secure flag from Set-Cookie headers so they work over plain http://localhost
        configure(proxy) {
          proxy.on("proxyRes", (proxyRes) => {
            const cookies = proxyRes.headers["set-cookie"];
            if (!cookies) return;
            proxyRes.headers["set-cookie"] = cookies.map((c) =>
              c.replace(/;\s*Secure/gi, "")
            );
          });
        },
      },
      // Proxy uploaded files (logos etc.) served as static files by the backend
      "/uploads": {
        target: process.env.API_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    // Enforce bundle size budget for teacher screens
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["axios", "dexie"],
          query: ["@tanstack/svelte-query"],
        },
      },
    },
  },
});
