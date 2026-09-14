import { authApi } from "./api";

// ============================
// LOGIN
// ============================

export const login = async (
  email: string,
  password: string
) => {
  const { data } = await authApi.post("/auth/login", {
    email,
    password,
  });

  return {
    access_token: data.access_token,
    token_type: data.token_type,
  };
};

// ============================
// REGISTER
// ============================

export const register = async (
  full_name: string,
  email: string,
  password: string
) => {
  const { data } = await authApi.post("/auth/register", {
    full_name,
    email,
    password,
  });

  return data;
};

// ============================
// CURRENT USER
// ============================

export const getCurrentUser = async () => {
  const { data } = await authApi.get("/auth/me");
  return data;
};

// ============================
// LOGOUT
// ============================

export const logout = async () => {
  try {
    // If your backend implements a logout endpoint,
    // this will notify the server.
    await authApi.post("/auth/logout");
  } catch {
    // Ignore 404 if logout is not implemented.
  }
};