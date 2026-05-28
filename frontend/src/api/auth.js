import {
  apiClient,
  storeTokens,
  applyAuth,
  clearTokens,
} from "./client";

export const authApi = {
  login: async (username, password) => {
    const response = await apiClient.post(
      "/tenants/auth/login/",
      {
        username,
        password,
      }
    );

    const data = response.data;

    // Store JWT tokens
    storeTokens({
      access: data.access,
      refresh: data.refresh,
    });

    // Get first organization
    const org = data.organizations?.[0];

    // Save organization and apply auth headers
    if (org) {
      localStorage.setItem("esg_org", org.id);

      applyAuth(data.access, org.id);
    } else {
      applyAuth(data.access, null);
    }

    return data;
  },

  refresh: async (refresh) => {
    const response = await apiClient.post(
      "/tenants/auth/refresh/",
      {
        refresh,
      }
    );

    const data = response.data;

    storeTokens({
      access: data.access,
      refresh: data.refresh,
    });

    const orgId = localStorage.getItem("esg_org");

    applyAuth(data.access, orgId);

    return data;
  },

  logout: async (refresh) => {
    try {
      await apiClient.post(
        "/tenants/auth/logout/",
        { refresh }
      );
    } finally {
      clearTokens();

      localStorage.removeItem("esg_org");

      applyAuth(null, null);
    }
  },

  me: async () => {
    const response = await apiClient.get(
      "/tenants/auth/me/"
    );

    return response.data;
  },
};