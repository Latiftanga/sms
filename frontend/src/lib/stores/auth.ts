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
      try {
        const { data } = await api.get<User>("/auth/me");
        set({ user: data, loading: false, error: null });
      } catch {
        set({ user: null, loading: false, error: null });
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
