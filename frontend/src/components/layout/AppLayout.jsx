import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthContext";
import { Icon } from "@/components/ui/Icon";
import "./AppLayout.css";

// Persistent shell: branded sidebar + routed content. Nav order follows the
// analyst's workflow — overview, connect sources, ingest, then review.
const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: "dashboard" },
  { to: "/sources", label: "Sources", icon: "database" },
  { to: "/ingestion", label: "Ingestion", icon: "upload" },
  { to: "/review", label: "Review", icon: "review" },
  { to: "/audit", label: "Audit trail", icon: "history" },
];

export function AppLayout() {
  const { user, organizations, activeOrg, setActiveOrg, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const org = organizations.find((o) => String(o.id) === String(activeOrg));
  const initials = (user?.username ?? "?").slice(0, 2).toUpperCase();

  return (
    <div className="app-shell">
      {/* Mobile Top Header */}
      <header className="mobile-header">
        <div className="brand">
          <span className="brand-mark"><Icon name="leaf" size={18} /></span>
          <span className="brand-name">Breathe ESG</span>
        </div>
        <button
          className="menu-toggle"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
          aria-expanded={menuOpen}
        >
          <Icon name={menuOpen ? "close" : "menu"} size={22} />
        </button>
      </header>

      {/* Sidebar Overlay */}
      {menuOpen && <div className="sidebar-overlay" onClick={() => setMenuOpen(false)} />}

      <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
        <div className="brand">
          <span className="brand-mark"><Icon name="leaf" size={18} /></span>
          <span className="brand-name">Breathe ESG</span>
        </div>

        {organizations.length > 1 ? (
          <div className="org-pill" style={{ padding: 0, position: "relative" }}>
            <span className="org-dot" style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }} />
            <select
              value={activeOrg ?? ""}
              onChange={(e) => {
                setActiveOrg(e.target.value);
                setMenuOpen(false);
              }}
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                color: "#eaf4ef",
                fontWeight: 600,
                fontSize: "0.82rem",
                padding: "0.5rem 1.8rem 0.5rem 1.8rem",
                borderRadius: "10px",
                cursor: "pointer",
                outline: "none",
                appearance: "none",
              }}
            >
              {organizations.map((o) => (
                <option key={o.id} value={o.id} style={{ background: "#0a2a20", color: "#eaf4ef" }}>
                  {o.name}
                </option>
              ))}
            </select>
            <span style={{ position: "absolute", right: "0.75rem", top: "50%", transform: "translateY(-50%)", pointerEvents: "none", fontSize: "0.6rem", color: "#aecabd" }}>▼</span>
          </div>
        ) : org ? (
          <div className="org-pill" title="Active organization">
            <span className="org-dot" />
            <span className="org-name">{org.name}</span>
          </div>
        ) : null}

        <nav className="nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className="nav-item"
              onClick={() => setMenuOpen(false)}
            >
              <Icon name={item.icon} size={18} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-chip">
            <span className="user-avatar">{initials}</span>
            <div className="user-meta">
              <div className="user-name">{user?.username}</div>
              <div className="user-role">{org?.role ?? "analyst"}</div>
            </div>
          </div>
          <button className="signout" onClick={logout} title="Sign out">
            <Icon name="logout" size={16} />
          </button>
        </div>
      </aside>

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
