/**
 * Axios instance — handles auth headers, token refresh, and base URL.
 * All API calls go through this client.
 */
import axios, { type AxiosInstance, type AxiosError } from "axios";
import { offlineDb } from "$lib/db/offline";

const BASE_URL = "/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true, // sends refresh_token httpOnly cookie
});

// ── Request interceptor: attach access token ─────────────────────

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: auto-refresh on 401 ────────────────────

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as typeof error.config & { _retry?: boolean };

    if (error.response?.status === 401 && !original?._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (original) original.headers!["Authorization"] = `Bearer ${token}`;
            return api(original!);
          })
          .catch((err) => Promise.reject(err));
      }

      original!._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post<{ access_token: string }>(
          `${BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );
        setAccessToken(data.access_token);
        failedQueue.forEach((q) => q.resolve(data.access_token));
        failedQueue = [];
        original!.headers!["Authorization"] = `Bearer ${data.access_token}`;
        return api(original!);
      } catch (refreshError) {
        failedQueue.forEach((q) => q.reject(refreshError));
        failedQueue = [];
        clearAccessToken();
        await offlineDb.attendanceQueue.clear();
        await offlineDb.scoreQueue.clear();
        // Don't hard-redirect when the original request was /auth/me — that just
        // means "no session yet" and the auth store handles it gracefully. Only
        // redirect when a previously-authenticated request loses its session mid-use.
        const isAuthInit = original?.url === "/auth/me";
        if (
          typeof window !== "undefined" &&
          !isAuthInit &&
          !window.location.pathname.startsWith("/login")
        ) {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ── Token storage ──────────────────────────────────────────────────
// Primary: sessionStorage — survives page refresh within the same tab,
//          cleared when the tab closes (no long-lived XSS exposure).
// Fallback: in-memory only when sessionStorage is unavailable (SSR, etc.)
// The httpOnly refresh cookie is still used to rehydrate a new tab or
// after the access token expires, via the 401 → /auth/refresh flow above.

const _SESSION_KEY = "sis_at";
let _accessToken: string | null = null;

export function getAccessToken(): string | null {
  if (_accessToken) return _accessToken;
  try {
    return sessionStorage.getItem(_SESSION_KEY);
  } catch {
    return null;
  }
}

export function setAccessToken(token: string): void {
  _accessToken = token;
  try {
    sessionStorage.setItem(_SESSION_KEY, token);
  } catch {
    // sessionStorage unavailable (private mode restrictions, etc.)
  }
}

export function clearAccessToken(): void {
  _accessToken = null;
  try {
    sessionStorage.removeItem(_SESSION_KEY);
  } catch {
    // ignore
  }
}
