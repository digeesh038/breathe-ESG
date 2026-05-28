import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { emissionsApi } from "@/api/emissions";
import { Icon } from "@/components/ui/Icon";
import { formatCo2e } from "@/lib/format";

// Right-side drilldown for one review item: normalized values (with inline
// edit), the emission factor applied, anomaly flags, and the verbatim source
// record it came from. Editing is blocked once a row is locked/rejected.
export function ActivityDrawer({ item, onClose }) {
  const qc = useQueryClient();
  const activityId = item.activity;
  const editable = item.status === "pending";

  const detail = useQuery({
    queryKey: ["activity", activityId],
    queryFn: () => emissionsApi.getActivity(activityId),
  });

  const [qty, setQty] = useState("");
  const save = useMutation({
    mutationFn: (value) => emissionsApi.updateActivity(activityId, { quantity: value }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["activity", activityId] });
      qc.invalidateQueries({ queryKey: ["review-items"] });
      qc.invalidateQueries({ queryKey: ["activities"] });
      qc.invalidateQueries({ queryKey: ["summary"] });
      setQty("");
    },
  });

  const a = detail.data;

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <aside className="drawer">
        <div className="drawer-head">
          <div>
            <div className="drawer-title">{a ? a.activity_category.replace(/_/g, " ") : "…"}</div>
            <div className="cell-secondary">Activity #{activityId}</div>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close"><Icon name="close" size={18} /></button>
        </div>

        {detail.isLoading && <div className="drawer-body muted">Loading…</div>}

        {a && (
          <div className="drawer-body">
            <section className="drawer-section">
              <div className="kv"><span>Scope</span><b><span className={`chip-scope s${a.scope}`}>Scope {a.scope}</span></b></div>
              <div className="kv"><span>Site / code</span><b>{a.site_code || "—"}</b></div>
              <div className="kv"><span>Activity date</span><b>{a.activity_date}</b></div>
              {a.period_start && <div className="kv"><span>Billing period</span><b>{a.period_start} → {a.period_end}</b></div>}
            </section>

            <p className="section-label">Normalized value</p>
            <section className="drawer-section">
              <div className="kv"><span>Original (ingested)</span><b>{Number(a.original_quantity).toLocaleString()} {a.unit}</b></div>
              <div className="kv">
                <span>Current quantity {a.is_edited && <span className="flag" style={{ cursor: "default" }}>edited</span>}</span>
                <b>{Number(a.quantity).toLocaleString()} {a.unit}</b>
              </div>
              <div className="kv"><span>Emission factor</span><b>{a.factor ? `${a.factor.co2e_per_unit} / ${a.factor.unit} · ${a.factor.source}` : "— none —"}</b></div>
              <div className="kv"><span>Calculated CO₂e</span><b>{formatCo2e(a.co2e_kg)}</b></div>

              {editable && (
                <div className="edit-row">
                  <input
                    className="input"
                    type="number"
                    step="any"
                    placeholder={`New quantity (${a.unit})`}
                    value={qty}
                    onChange={(e) => setQty(e.target.value)}
                  />
                  <button
                    className="btn btn--primary btn--sm"
                    disabled={save.isPending || qty === ""}
                    onClick={() => save.mutate(qty)}
                  >
                    {save.isPending ? "Saving…" : "Save & recompute"}
                  </button>
                </div>
              )}
            </section>

            {item.flags.length > 0 && (
              <>
                <p className="section-label">Anomalies</p>
                <section className="drawer-section">
                  {item.flags.map((f) => (
                    <div className="anomaly-row" key={f.id}>
                      <span className="flag" style={{ cursor: "default" }}>{f.kind.replace(/_/g, " ")}</span>
                      <span className="cell-secondary">{f.detail}</span>
                    </div>
                  ))}
                </section>
              </>
            )}

            <p className="section-label">Source history</p>
            <section className="drawer-section">
              <div className="kv"><span>Source</span><b>{a.raw.batch.source_type.toUpperCase()}</b></div>
              <div className="kv"><span>File</span><b>{a.raw.batch.filename}</b></div>
              <div className="kv"><span>Received</span><b>{new Date(a.raw.batch.received_at).toLocaleString()}</b></div>
              <div className="kv"><span>Raw row</span><b>#{a.raw.row_number} · {a.raw.status}</b></div>
              <div className="raw-payload">
                <div className="raw-payload-label">Original record (verbatim)</div>
                <table className="raw-table">
                  <tbody>
                    {Object.entries(a.raw.payload).map(([k, v]) => (
                      <tr key={k}><td>{k}</td><td>{typeof v === "object" ? JSON.stringify(v) : String(v)}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}
      </aside>
    </>
  );
}
