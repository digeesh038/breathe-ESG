import { createContext, useContext, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/api/auth";
import { applyAuth, clearTokens, readTokens, storeTokens } from "@/api/client";

// JWT access + refresh + active org are persisted in localStorage and mirrored
// onto the axios client. On load we re-apply them and verify via /auth/me.
// Refresh on 401 is handled inside the axios client, not here.
const ORG_KEY = "esg_org";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const queryClient = useQueryClient();
  const initialTokens = readTokens();
  const [accessToken, setAccessToken] = useState(initialTokens.access);
  const [activeOrg, setActiveOrg] = useState(() => localStorage.getItem(ORG_KEY));
  const [organizations, setOrganizations] = useState([]);
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const handleAuthLogout = () => {
      logout();
    };
    window.addEventListener("auth-logout", handleAuthLogout);

    if (!accessToken) {
      setReady(true);
      return () => {
        window.removeEventListener("auth-logout", handleAuthLogout);
      };
    }
    applyAuth(accessToken, activeOrg);
    authApi
      .me()
      .then((data) => {
        setUser(data.user);
        setOrganizations(data.organizations);
        if (!activeOrg && data.organizations[0]) chooseOrg(data.organizations[0].id);
      })
      .catch(() => logout())
      .finally(() => setReady(true));

    return () => {
      window.removeEventListener("auth-logout", handleAuthLogout);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Switch the active tenant: persist it, update the X-Organization header, and
  // drop cached server data so every page refetches for the new org. Without
  // this, React Query keeps serving the previous tenant's data and the dropdown
  // looks like it does nothing.
  function chooseOrg(id) {
    const value = String(id);
    const prev = localStorage.getItem(ORG_KEY);
    localStorage.setItem(ORG_KEY, value);
    setActiveOrg(value);
    applyAuth(accessToken, value);
    if (prev !== value) {
      // Remove stale tenant data first (so org A's numbers don't flash while
      // org B loads), then refetch everything currently on screen.
      queryClient.removeQueries();
      queryClient.invalidateQueries();
    }
  }

  async function login(username, password) {
    const data = await authApi.login(username, password);
    storeTokens({ access: data.access, refresh: data.refresh });
    setAccessToken(data.access);
    setUser(data.user);
    setOrganizations(data.organizations);
    const orgId = data.organizations[0]?.id;
    if (orgId) {
      localStorage.setItem(ORG_KEY, String(orgId));
      setActiveOrg(String(orgId));
    }
    applyAuth(data.access, orgId);
    queryClient.invalidateQueries();
    return data;
  }

  function logout() {
    // Best-effort: blacklist the refresh token server-side so it can't be
    // reused. We don't await it — local state is cleared regardless.
    const { refresh } = readTokens();
    if (refresh) authApi.logout(refresh).catch(() => {});
    clearTokens();
    localStorage.removeItem(ORG_KEY);
    setAccessToken(null);
    setUser(null);
    setOrganizations([]);
    setActiveOrg(null);
    applyAuth(null, null);
    queryClient.clear();
  }

  const value = {
    token: accessToken,
    user,
    organizations,
    activeOrg,
    ready,
    login,
    logout,
    setActiveOrg: chooseOrg,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
