import axios from "axios";

// Single configured axios instance.
// Requests go to the deployed backend API.
// JWT auth uses:
// - Authorization: Bearer <access>
// - X-Organization: <orgId>

const ACCESS_KEY = "esg_access";
const REFRESH_KEY = "esg_refresh";

export const apiClient = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ||
    "https://breathe-esg-bcx4.onrender.com/api/v1",
});

// Apply auth headers globally
export function applyAuth(accessToken, orgId) {
  if (accessToken) {
    apiClient.defaults.headers.common[
      "Authorization"
    ] = `Bearer ${accessToken}`;
  } else {
    delete apiClient.defaults.headers.common["Authorization"];
  }

  if (orgId) {
    apiClient.defaults.headers.common[
      "X-Organization"
    ] = String(orgId);
  } else {
    delete apiClient.defaults.headers.common["X-Organization"];
  }
}

// Store tokens
export function storeTokens({ access, refresh }) {
  if (access) {
    localStorage.setItem(ACCESS_KEY, access);
  }

  if (refresh) {
    localStorage.setItem(REFRESH_KEY, refresh);
  }
}

// Read tokens
export function readTokens() {
  return {
    access: localStorage.getItem(ACCESS_KEY),
    refresh: localStorage.getItem(REFRESH_KEY),
  };
}

// Clear tokens
export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// Refresh handling
let refreshInFlight = null;

async function refreshAccess() {
  const { refresh } = readTokens();

  if (!refresh) {
    throw new Error("No refresh token");
  }

  if (!refreshInFlight) {
    refreshInFlight = axios
      .post(
        `${apiClient.defaults.baseURL}/tenants/auth/refresh/`,
        { refresh }
      )
      .then((r) => r.data)
      .finally(() => {
        refreshInFlight = null;
      });
  }

  const data = await refreshInFlight;

  storeTokens({
    access: data.access,
    refresh: data.refresh,
  });

  const orgId = localStorage.getItem("esg_org");

  applyAuth(data.access, orgId);

  return data.access;
}

// Auto refresh expired access token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config || {};
    const status = error.response?.status;

    const isRefreshRequest =
      original.url?.includes("/auth/refresh/");

    if (
      status === 401 &&
      !original._retried &&
      !isRefreshRequest
    ) {
      original._retried = true;

      try {
        const newAccess = await refreshAccess();

        original.headers = {
          ...(original.headers || {}),
          Authorization: `Bearer ${newAccess}`,
        };

        return apiClient(original);
      } catch (err) {
        clearTokens();

        window.dispatchEvent(
          new Event("auth-logout")
        );

        return Promise.reject(err);
      }
    }

    return Promise.reject(error);
  }
);

// Restore auth automatically on app load
const { access } = readTokens();
const orgId = localStorage.getItem("esg_org");

if (access) {
  applyAuth(access, orgId);
}

// DRF pagination helper
export const unwrap = (res) =>
  res.data?.results ?? res.data;