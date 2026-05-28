import { writable } from "svelte/store";
import { api } from "$lib/api/client";

export interface SchoolBranding {
  name: string;
  motto: string | null;
  logo_url: string | null;
  accent_color: string;
}

const CACHE_KEY = "sis-school-branding";

function getInitial(): SchoolBranding | null {
  if (typeof localStorage === "undefined") return null;
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? (JSON.parse(raw) as SchoolBranding) : null;
  } catch {
    return null;
  }
}

function createSchoolStore() {
  const { subscribe, set } = writable<SchoolBranding | null>(getInitial());

  function applyAccent(color: string) {
    if (typeof document !== "undefined") {
      document.documentElement.style.setProperty("--accent", color);
      localStorage.setItem("sis-accent", color);
    }
  }

  return {
    subscribe,

    async load() {
      try {
        const { data } = await api.get<SchoolBranding>("/public/school");
        set(data);
        localStorage.setItem(CACHE_KEY, JSON.stringify(data));
        applyAccent(data.accent_color);
      } catch {
        // Use cached value if fetch fails — accent already applied from localStorage
      }
    },

    clear() {
      set(null);
      if (typeof localStorage !== "undefined") {
        localStorage.removeItem(CACHE_KEY);
      }
    },
  };
}

export const schoolBranding = createSchoolStore();
