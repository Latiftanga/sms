/**
 * Axios instance — handles auth headers, token refresh, and base URL.
 * All API calls go through this client.
 */
import axios, { type AxiosInstance, type AxiosError } from "axios";

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
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
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

// ── Token storage (sessionStorage — cleared on tab close) ─────────

const TOKEN_KEY = "ttek_access_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}
