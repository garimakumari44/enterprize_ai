import axios from "axios";

// ============================================================
// API BASE URL
// ============================================================

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000/api/v1";

// ============================================================
// Axios Instance
// ============================================================

const authApi = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    Accept: "application/json",
  },
});

// ============================================================
// Request Interceptor
// Automatically attach JWT access token
// ============================================================

authApi.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("accessToken");

      if (token) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${token}`;
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ============================================================
// Response Interceptor
// Handle expired / invalid tokens
// ============================================================

authApi.interceptors.response.use(
  (response) => response,

  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("accessToken");

        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
      }
    }

    return Promise.reject(error);
  }
);

// ============================================================
// Exports
// ============================================================

// Named export used by lib/auth.ts
export { authApi };

// Default export used by other frontend modules
export default authApi;