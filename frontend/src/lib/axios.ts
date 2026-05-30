import axios, { AxiosError, AxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Reasonable client-side timeout — protect against hung backends.
  timeout: 30_000,
});

// ── Token storage helpers ──────────────────────────────────────────
// Centralized so swap to httpOnly cookie auth later only touches one file.
function getAccessToken(): string | null {
  return localStorage.getItem('access_token');
}

function setTokens(access: string, refresh: string): void {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

function clearTokens(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  localStorage.removeItem('auth-storage'); // zustand persist key
}

// ── Request interceptor: attach bearer token ───────────────────────
apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor: single-flight refresh on 401 ─────────────
//
// Why single-flight: when 5 concurrent requests fail with 401, naive
// implementation hits /auth/refresh 5 times. Each call rotates the
// refresh token (server-side rotation), so 4 of the 5 refreshes will
// fail with "token revoked" and log the user out.
//
// Single-flight: first 401 starts a refresh; the other four await the
// same promise and reuse the new access token.

let refreshPromise: Promise<string> | null = null;

async function performRefresh(): Promise<string> {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  // Use bare axios — calling apiClient would loop the interceptor.
  const response = await axios.post<{ access_token: string; refresh_token: string }>(
    `${API_BASE_URL}/auth/refresh`,
    { refresh_token: refreshToken }
  );

  const { access_token, refresh_token } = response.data;
  setTokens(access_token, refresh_token);
  return access_token;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Guard: only handle 401, only retry once, never recurse on /auth/refresh itself.
    const isAuthRefresh = originalRequest?.url?.includes('/auth/refresh');
    if (
      error.response?.status !== 401 ||
      originalRequest?._retry ||
      isAuthRefresh
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      // Coalesce concurrent refreshes
      if (!refreshPromise) {
        refreshPromise = performRefresh().finally(() => {
          refreshPromise = null;
        });
      }
      const newAccessToken = await refreshPromise;

      // Retry original with the fresh token
      originalRequest.headers = originalRequest.headers ?? {};
      (originalRequest.headers as Record<string, string>).Authorization =
        `Bearer ${newAccessToken}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      // Refresh definitively failed — clear state and bounce to login.
      clearTokens();
      // Avoid loop if user already on /login
      if (!window.location.pathname.startsWith('/login')) {
        window.location.assign('/login');
      }
      return Promise.reject(refreshError);
    }
  }
);
