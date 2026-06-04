import { writable } from "svelte/store";
import { api } from "$lib/api/client";

export interface SchoolBranding {
  name: string;
  motto: string | null;
  logo_url: string | null;
  accent_color: string;
}

export interface SchoolContext {
  education_levels: string[];
  facility_type: string;
  has_houses: boolean;
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

    // Called before login — resolves branding from subdomain/custom domain,
    // falls back to generic platform branding when no match.
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

    // Called after login — overwrites with the authenticated user's real school
    // branding so the sidebar always shows the correct name, logo, and accent.
    async loadFromAuth() {
      try {
        const { data } = await api.get<SchoolBranding & { education_levels?: string[] }>("/settings/school");
        const branding: SchoolBranding = {
          name: data.name,
          motto: data.motto ?? null,
          logo_url: data.logo_url ?? null,
          accent_color: data.accent_color,
        };
        set(branding);
        localStorage.setItem(CACHE_KEY, JSON.stringify(branding));
        applyAccent(branding.accent_color);
      } catch {
        // unauthenticated or network error — keep existing branding
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

// ── School context (authenticated) ────────────────────────────────────────────
// Holds school capabilities: education levels, facility type, houses.
// Loaded once in the app shell after auth resolves; cleared on logout.
function createSchoolContextStore() {
  const { subscribe, set } = writable<SchoolContext | null>(null);

  return {
    subscribe,

    async load() {
      try {
        const { data } = await api.get<SchoolContext>("/settings/school");
        set({
          education_levels: data.education_levels ?? [],
          facility_type: data.facility_type ?? "DAY",
          has_houses: data.has_houses ?? false,
        });
      } catch {
        // unauthenticated or network error — leave as null
      }
    },

    clear() {
      set(null);
    },
  };
}

export const schoolContext = createSchoolContextStore();
