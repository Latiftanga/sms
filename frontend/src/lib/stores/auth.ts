/**
 * Auth store — single source of truth for user identity + permissions.
 * Populated on login and /auth/me hydration.
 * The can() function is the primary permission gate used across all components.
 */
import { writable, derived, get } from "svelte/store";
import type { User } from "$api/types";
import { api, setAccessToken, clearAccessToken } from "$api/client";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

function createAuthStore() {
  const { subscribe, set, update } = writable<AuthState>({
    user: null,
    loading: true,
    error: null,
  });

  return {
    subscribe,

    async init(): Promise<void> {
      // If user is already loaded, skip — prevents double-init from layout remounts.
      const current = get({ subscribe });
      if (!current.loading && current.user) return;

      try {
        const { data } = await api.get<User>("/auth/me");
        // Re-check after await: login() may have won the race and already set the user.
        if (get({ subscribe }).user) return;
        set({ user: data, loading: false, error: null });
      } catch {
        // Don't wipe a user that login() just set while /auth/me was in-flight.
        if (get({ subscribe }).user) return;
        set({ user: null, loading: false, error: null });
      }
    },

    // Silent, non-destructive refresh — keeps permissions current without wiping
    // the user out on transient errors (network blip, 5xx, etc.).
    async refresh(): Promise<void> {
      try {
        const { data } = await api.get<User>("/auth/me");
        update((s) => s.user ? { ...s, user: data } : s);
      } catch {
        // Silently swallow — don't clear user on background refresh failure.
      }
    },

    async login(email: string, password: string): Promise<void> {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const { data } = await api.post<{ access_token: string }>("/auth/login", {
          email,
          password,
        });
        setAccessToken(data.access_token);
        const { data: user } = await api.get<User>("/auth/me");
        set({ user, loading: false, error: null });
      } catch (err: unknown) {
        const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
        const msg = typeof detail === "string" ? detail : "Invalid email or password.";
        update((s) => ({ ...s, loading: false, error: msg }));
        throw err;
      }
    },

    async logout(): Promise<void> {
      try {
        await api.post("/auth/logout");
      } finally {
        clearAccessToken();
        set({ user: null, loading: false, error: null });
      }
    },

    patchUser(patch: Partial<NonNullable<AuthState["user"]>>): void {
      update((s) => s.user ? { ...s, user: { ...s.user, ...patch } } : s);
    },

    can(permission: string): boolean {
      const state = get({ subscribe });
      if (!state.user) return false;
      if (state.user.system_role === "SUPERADMIN") return true;
      return state.user.permissions[permission] === true;
    },
  };
}

export const auth = createAuthStore();

export const isAuthenticated = derived(auth, ($auth) => $auth.user !== null);
export const currentUser = derived(auth, ($auth) => $auth.user);
export const isLoading = derived(auth, ($auth) => $auth.loading);
