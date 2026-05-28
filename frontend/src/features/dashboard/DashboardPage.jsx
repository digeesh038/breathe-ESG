import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { emissionsApi } from "@/api/emissions";
import { useAuth } from "@/features/auth/AuthContext";
import { PageHeader } from "@/components/ui/PageHeader";
import { formatCo2e, formatCo2eParts } from "@/lib/format";
import { scopeDescription } from "@/lib/labels";

// Renders a tonnes figure with the unit visually subordinate to the number.
function Co2eValue({ kg }) {
  const { value, unit } = formatCo2eParts(kg);
  return (
    <>
      {value}
      {unit && <span className="stat-unit">{unit}</span>}
    </>
  );
}

// Scope brand colors (must match the design tokens in styles/index.css).
const SCOPE_COLORS = { "1": "#b4600f", "2": "#2563c4", "3": "#6a47c9" };

function tonnes(kg) {
  return Number(kg || 0) / 1000;
}

export function DashboardPage() {
  const { organizations, activeOrg } = useAuth();
  const org = organizations.find((o) => String(o.id) === String(activeOrg));

  const summary = useQuery({ queryKey: ["summary"], queryFn: emissionsApi.summary });
  const s = summary.data;

  const total = s?.total_co2e ?? 0;
  const byScope = (s?.by_scope ?? []).map((row) => ({
    ...row,
    share: total ? (row.co2e / total) * 100 : 0,
    label: `Scope ${row.scope}`,
    co2e_t: tonnes(row.co2e),
  }));

  // Trend rows arrive as { month: "2025-04", s1, s2, s3 } in kg → convert to tonnes for charting.
  const trend = (s?.trend ?? []).map((row) => ({
    month: row.month,
    "Scope 1": tonnes(row.s1),
    "Scope 2": tonnes(row.s2),
    "Scope 3": tonnes(row.s3),
  }));

  const topSites = s?.top_sites ?? [];

  return (
    <section>
      <PageHeader title="Dashboard" subtitle={`Emissions overview${org ? ` · ${org.name}` : ""}`} />

      <div className="stat-grid">
        <div className="stat-card stat-card--hero">
          <div className="stat-label">Total emissions <span className="hero-sub">(excl. rejected)</span></div>
          <div className="stat-value"><Co2eValue kg={total} /></div>
          <div className="stat-meta">{s?.record_count ?? 0} records · {formatCo2e(s?.locked_co2e ?? 0)} audit-ready</div>
        </div>
        {byScope.map((row) => (
          <div className={`stat-card s${row.scope}`} key={row.scope} title={scopeDescription(row.scope)}>
            <div className="stat-label">Scope {row.scope}</div>
            <div className="stat-value"><Co2eValue kg={row.co2e} /></div>
            <div className="stat-meta">{row.count} records · {row.share.toFixed(0)}% of total</div>
          </div>
        ))}
      </div>

      <div className="legend">
        <span className="legend-item"><span className="legend-dot s1" /> <strong>Scope 1</strong> — direct (fuel burned on-site &amp; vehicles)</span>
        <span className="legend-item"><span className="legend-dot s2" /> <strong>Scope 2</strong> — purchased energy (electricity)</span>
        <span className="legend-item"><span className="legend-dot s3" /> <strong>Scope 3</strong> — value chain (travel, suppliers)</span>
      </div>

      <div className="chart-grid">
        <div className="panel chart-panel">
          <div className="panel-head">
            <span className="panel-title">Emissions trend</span>
            <span className="panel-note">monthly · t CO₂e</span>
          </div>
          {trend.length === 0 ? (
            <p className="empty">No data yet — upload a batch on the Ingestion page.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={trend} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
                <CartesianGrid stroke="#e7ecea" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#5c6f68" }} />
                <YAxis tick={{ fontSize: 12, fill: "#5c6f68" }} />
                <Tooltip
                  formatter={(value) => `${Number(value).toFixed(2)} t`}
                  cursor={{ fill: "rgba(18, 122, 85, 0.06)" }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="Scope 1" stackId="co2e" fill={SCOPE_COLORS["1"]} />
                <Bar dataKey="Scope 2" stackId="co2e" fill={SCOPE_COLORS["2"]} />
                <Bar dataKey="Scope 3" stackId="co2e" fill={SCOPE_COLORS["3"]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="panel chart-panel">
          <div className="panel-head">
            <span className="panel-title">Mix by scope</span>
            <span className="panel-note">share of total</span>
          </div>
          {total === 0 ? (
            <p className="empty">No emissions recorded yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={byScope}
                  dataKey="co2e_t"
                  nameKey="label"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={2}
                >
                  {byScope.map((row) => (
                    <Cell key={row.scope} fill={SCOPE_COLORS[row.scope]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `${Number(value).toFixed(2)} t`} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <p className="section-label">Review progress</p>
      <div className="stat-grid">
        <div className="stat-card"><div className="stat-label">Pending review</div><div className="stat-value">{s?.review?.pending ?? 0}</div></div>
        <div className="stat-card"><div className="stat-label">Locked for audit</div><div className="stat-value">{s?.review?.locked ?? 0}</div></div>
        <div className="stat-card"><div className="stat-label">Rejected</div><div className="stat-value">{s?.review?.rejected ?? 0}</div></div>
        <div className="stat-card stat-card--warn"><div className="stat-label">Open anomalies</div><div className="stat-value">{s?.open_anomalies ?? 0}</div></div>
      </div>

      {topSites.length > 0 && (
        <>
          <p className="section-label">Top sites by emissions</p>
          <div className="panel">
            <table className="table">
              <thead>
                <tr>
                  <th>Site</th>
                  <th className="num">Records</th>
                  <th className="num">CO₂e</th>
                </tr>
              </thead>
              <tbody>
                {topSites.map((row) => (
                  <tr key={row.site_code}>
                    <td>{row.site_code}</td>
                    <td className="num">{row.count}</td>
                    <td className="num">{formatCo2e(row.co2e)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {summary.isLoading && <p className="muted spacer">Loading…</p>}
    </section>
  );
}
