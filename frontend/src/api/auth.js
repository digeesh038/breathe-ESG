import { apiClient } from "./client";

export const authApi = {
  login: (username, password) =>
    apiClient.post("/tenants/auth/login/", { username, password }).then((r) => r.data),

  refresh: (refresh) =>
    apiClient.post("/tenants/auth/refresh/", { refresh }).then((r) => r.data),

  logout: (refresh) => apiClient.post("/tenants/auth/logout/", { refresh }),

  me: () => apiClient.get("/tenants/auth/me/").then((r) => r.data),
};
