import { useQuery } from "@tanstack/react-query";
import { auditApi } from "@/api/audit";
import { PageHeader } from "@/components/ui/PageHeader";
import { humanize } from "@/lib/labels";

// Append-only audit log. Read-only by design — every create/edit/lock/reject
// is recorded with actor, target, and a before/after diff for auditors.
function shortTarget(t) {
  return humanize(t.replace(/^.*\./, ""));
}

// Render the changes JSON as plain language instead of raw JSON.
// e.g. {"quantity": ["100","200"]} -> "quantity: 100 → 200"
function describeChanges(changes) {
  const keys = Object.keys(changes || {});
  if (keys.length === 0) return "—";
  return keys
    .map((k) => {
      const v = changes[k];
      if (Array.isArray(v) && v.length === 2) return `${humanize(k)}: ${v[0]} → ${v[1]}`;
      if (v && typeof v === "object") return `${humanize(k)}: ${Object.values(v).join(", ")}`;
      return `${humanize(k)}: ${v}`;
    })
    .join(" · ");
}

// created/edited/locked/rejected -> friendly verb.
const ACTION_LABELS = {
  created: "Created",
  edited: "Edited",
  locked: "Approved & locked",
  rejected: "Rejected",
};

export function AuditPage() {
  const events = useQuery({ queryKey: ["audit"], queryFn: () => auditApi.list() });
  const rows = events.data ?? [];

  return (
    <section>
      <PageHeader title="Audit trail" subtitle="Immutable record of every change, for audit compliance." />

      <div className="panel">
        <div className="panel-head">
          <span className="panel-title">Events</span>
          <span className="panel-note">{rows.length} entries</span>
        </div>
        <div className="table-responsive">
          <table className="table table-cards">
            <thead>
              <tr>
                <th>When</th><th>Action</th><th>Target</th><th>Actor</th><th>Changes</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((e) => (
                <tr key={e.id}>
                  <td data-label="When" className="muted">{new Date(e.occurred_at).toLocaleString()}</td>
                  <td data-label="Action"><span className={`audit-action ${e.action}`}>{ACTION_LABELS[e.action] ?? humanize(e.action)}</span></td>
                  <td data-label="Target">{shortTarget(e.target_model)} <span className="muted">#{e.target_id}</span></td>
                  <td data-label="Actor">{e.actor ?? "system"}</td>
                  <td data-label="Changes">{describeChanges(e.changes)}</td>
                </tr>
              ))}
              {rows.length === 0 && !events.isLoading && (
                <tr><td colSpan={5} className="empty">No audit events yet.</td></tr>
              )}
              {events.isLoading && <tr><td colSpan={5} className="empty">Loading…</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
