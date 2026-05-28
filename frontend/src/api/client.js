import axios from "axios";

// Single configured axios instance. Requests go to /api (same-origin via the
// Vite dev proxy), so no CORS in dev. Auth is a JWT access token in the
// Authorization header plus the active org in X-Organization. Refresh is
// performed once on a 401, then the original request is retried.
const ACCESS_KEY = "esg_access";
const REFRESH_KEY = "esg_refresh";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api/v1",
});

export function applyAuth(accessToken, orgId) {
  if (accessToken) apiClient.defaults.headers.common["Authorization"] = `Bearer ${accessToken}`;
  else delete apiClient.defaults.headers.common["Authorization"];

  if (orgId) apiClient.defaults.headers.common["X-Organization"] = String(orgId);
  else delete apiClient.defaults.headers.common["X-Organization"];
}

export function storeTokens({ access, refresh }) {
  if (access) localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

export function readTokens() {
  return {
    access: localStorage.getItem(ACCESS_KEY),
    refresh: localStorage.getItem(REFRESH_KEY),
  };
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// One-shot refresh + retry. We avoid touching apiClient.interceptors during
// the refresh call itself by using a bare axios instance, otherwise a 401 on
// /auth/refresh would loop.
let refreshInFlight = null;
async function refreshAccess() {
  const { refresh } = readTokens();
  if (!refresh) throw new Error("no_refresh_token");
  if (!refreshInFlight) {
    refreshInFlight = axios
      .post(`${apiClient.defaults.baseURL}/tenants/auth/refresh/`, { refresh })
      .then((r) => r.data)
      .finally(() => {
        refreshInFlight = null;
      });
  }
  const data = await refreshInFlight;
  storeTokens({ access: data.access, refresh: data.refresh });
  const orgId = localStorage.getItem("esg_org");
  applyAuth(data.access, orgId);
  return data.access;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config || {};
    const status = error.response?.status;
    const isRefresh = original.url?.includes("/auth/refresh/");
    if (status === 401 && !original._retried && !isRefresh) {
      original._retried = true;
      try {
        const newAccess = await refreshAccess();
        original.headers = { ...(original.headers || {}), Authorization: `Bearer ${newAccess}` };
        return apiClient(original);
      } catch (err) {
        clearTokens();
        window.dispatchEvent(new Event("auth-logout"));
        return Promise.reject(err);
      }
    }
    return Promise.reject(error);
  },
);

// DRF list endpoints are paginated ({count,results}); detail/action ones aren't.
export const unwrap = (res) => res.data?.results ?? res.data;
