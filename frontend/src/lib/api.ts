import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { clearAuthCookies } from "@/lib/auth-cookies";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

type TokenResponse = {
  access_token: string;
  refresh_token?: string;
};

type RetryableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

let refreshRequest: Promise<TokenResponse | null> | null = null;

function clearAuthAndRedirectToLogin(): void {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  clearAuthCookies();

  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

async function refreshAccessToken(): Promise<TokenResponse | null> {
  if (typeof window === "undefined") {
    return null;
  }

  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) {
    return null;
  }

  if (!refreshRequest) {
    refreshRequest = axios
      .post<TokenResponse>(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      })
      .then(({ data }) => {
        localStorage.setItem("access_token", data.access_token);
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token);
        }
        return data;
      })
      .catch(() => {
        clearAuthAndRedirectToLogin();
        return null;
      })
      .finally(() => {
        refreshRequest = null;
      });
  }

  return refreshRequest;
}

// Interceptor para adicionar token JWT
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Interceptor para refresh automático em 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const axiosError = error as AxiosError;
    const originalRequest = axiosError.config as RetryableRequestConfig | undefined;

    if (axiosError.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;

      const tokenData = await refreshAccessToken();
      if (tokenData) {
        originalRequest.headers.Authorization = `Bearer ${tokenData.access_token}`;
        return api(originalRequest);
      }

      clearAuthAndRedirectToLogin();
    }

    return Promise.reject(error);
  }
);

export default api;
