import { useMemo, useState } from "react";
import { saveAs } from "file-saver";
import { useReviewItems } from "./useReviewItems";
import { ActivityDrawer } from "./ActivityDrawer";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PageHeader } from "@/components/ui/PageHeader";
import { emissionsApi } from "@/api/emissions";
import { formatCo2e } from "@/lib/format";
import { flagLabel, humanize, scopeDescription, scopeLabel, statusLabel } from "@/lib/labels";

// The core analyst surface. Plain table + plain React state — no grid library —
// so the behavior is easy to follow. Click a row to drill into source history.
const FILTERS = ["all", "pending", "locked", "rejected"];
const PAGE_SIZE = 25;

// Column metadata drives the header row and sorting. Cell bodies are rendered
// inline below so action handlers stay in component scope.
const COLUMNS = [
  { key: "activity", label: "Activity", sortable: true, sortValue: (i) => i.activity_detail.activity_category },
  { key: "scope", label: "Scope", sortable: true, sortValue: (i) => i.activity_detail.scope },
  { key: "quantity", label: "Quantity", numeric: true, sortable: true, sortValue: (i) => Number(i.activity_detail.quantity) },
  { key: "co2e", label: "CO₂e", numeric: true, sortable: true, sortValue: (i) => Number(i.activity_detail.co2e_kg) },
  { key: "anomalies", label: "Anomalies", sortable: false },
  { key: "status", label: "Status", sortable: true, sortValue: (i) => i.status },
  { key: "actions", label: "Actions", sortable: false },
];

function searchText(item) {
  const a = item.activity_detail;
  return [
    humanize(a.activity_category),
    a.site_code,
    scopeLabel(a.scope),
    statusLabel(item.status),
    item.flags.map((f) => flagLabel(f.kind)).join(" "),
  ]
    .join(" ")
    .toLowerCase();
}

export function ReviewPage() {
  const [filter, setFilter] = useState("pending");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState({ key: null, dir: "asc" });
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");

  const status = filter === "all" ? undefined : filter;
  const { data, isLoading, isError, approve, reject } = useReviewItems(status);

  const actionError = approve.error || reject.error;
  const acting = approve.isPending || reject.isPending;

  // Filter (by search) then sort. Memoized so typing doesn't re-sort the whole
  // list on unrelated renders.
  const rows = useMemo(() => {
    const items = data ?? [];
    const q = query.trim().toLowerCase();
    const filtered = q ? items.filter((i) => searchText(i).includes(q)) : items;
    if (!sort.key) return filtered;
    const col = COLUMNS.find((c) => c.key === sort.key);
    if (!col?.sortValue) return filtered;
    const dir = sort.dir === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const av = col.sortValue(a);
      const bv = col.sortValue(b);
      if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir;
      return String(av).localeCompare(String(bv)) * dir;
    });
  }, [data, query, sort]);

  const total = rows.length;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const pageRows = rows.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);

  function changeFilter(f) {
    setFilter(f);
    setPage(0);
  }

  function toggleSort(key) {
    setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" }));
  }

  async function downloadExport(format) {
    setExporting(true);
    setExportError("");
    try {
      const blob = await emissionsApi.exportActivities(format);
      const ext = format === "xlsx" ? "xlsx" : "csv";
      saveAs(blob, `emissions_${new Date().toISOString().slice(0, 10)}.${ext}`);
    } catch (err) {
      setExportError(`Export failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setExporting(false);
    }
  }

  return (
    <section>
      <PageHeader
        title="Review & sign-off"
        subtitle="Click a row to inspect its source and edit. Approve to lock for audit."
        actions={
          <div className="btn-row">
            <button className="btn btn--sm" onClick={() => downloadExport("csv")} disabled={exporting}>
              Export CSV
            </button>
            <button className="btn btn--sm" onClick={() => downloadExport("xlsx")} disabled={exporting}>
              Export XLSX
            </button>
          </div>
        }
      />

      {exportError && (
        <p className="error-text" role="alert" style={{ marginTop: "0.5rem" }}>
          {exportError}
        </p>
      )}
      {actionError && (
        <p className="error-text" role="alert" style={{ marginTop: "0.5rem" }}>
          Couldn&apos;t update the record: {actionError.response?.data?.detail || actionError.message}
        </p>
      )}

      <div className="segmented">
        {FILTERS.map((f) => (
          <button key={f} className="seg-btn" onClick={() => changeFilter(f)} aria-pressed={filter === f}>
            {f}
          </button>
        ))}
        <input
          className="seg-search"
          type="search"
          placeholder="Filter rows…"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setPage(0);
          }}
        />
      </div>

      <div className="panel">
        <div className="panel-head">
          <span className="panel-title">Review queue</span>
          <span className="panel-note">{total} items</span>
        </div>
        <div className="table-responsive">
          <table className="table table--clickable">
            <thead>
              <tr>
                {COLUMNS.map((col) => {
                  const active = sort.key === col.key;
                  return (
                    <th
                      key={col.key}
                      onClick={col.sortable ? () => toggleSort(col.key) : undefined}
                      className={col.sortable ? "th-sortable" : undefined}
                    >
                      <span className={col.numeric ? "num" : undefined}>{col.label}</span>
                      {active && <span className="sort-ind"> {sort.dir === "asc" ? "▲" : "▼"}</span>}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((item) => {
                const a = item.activity_detail;
                const pending = item.status === "pending";
                return (
                  <tr
                    key={item.id}
                    onClick={() => setSelected(item)}
                    className={selected?.id === item.id ? "row-selected" : undefined}
                  >
                    <td>
                      <div className="cell-primary">{humanize(a.activity_category)}</div>
                      <div className="cell-secondary">{a.site_code || "—"} · {a.activity_date}</div>
                    </td>
                    <td>
                      <span className={`chip-scope s${a.scope}`} title={scopeDescription(a.scope)}>
                        {scopeLabel(a.scope)}
                      </span>
                    </td>
                    <td className="num">
                      {Number(a.quantity).toLocaleString()} {a.unit}
                    </td>
                    <td className="num">{formatCo2e(a.co2e_kg)}</td>
                    <td>
                      {item.flags.length === 0 ? (
                        <span className="muted">—</span>
                      ) : (
                        item.flags.map((flag) => (
                          <span key={flag.id} className="flag" title={flag.detail}>
                            {flagLabel(flag.kind)}
                          </span>
                        ))
                      )}
                    </td>
                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                    <td>
                      <div onClick={(e) => e.stopPropagation()}>
                        {pending ? (
                          <div className="btn-row">
                            <button
                              className="btn btn--sm btn--approve"
                              disabled={acting}
                              onClick={() => approve.mutate({ id: item.id })}
                            >
                              Approve
                            </button>
                            <button
                              className="btn btn--sm btn--reject"
                              disabled={acting}
                              onClick={() => reject.mutate({ id: item.id })}
                            >
                              Reject
                            </button>
                          </div>
                        ) : (
                          <span className="muted">{item.reviewed_at ? "signed off" : "—"}</span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}

              {isLoading && (
                <tr>
                  <td colSpan={COLUMNS.length} className="empty">
                    Loading…
                  </td>
                </tr>
              )}
              {isError && !isLoading && (
                <tr>
                  <td colSpan={COLUMNS.length} className="empty error-text">
                    Couldn&apos;t load review items.
                  </td>
                </tr>
              )}
              {!isLoading && !isError && total === 0 && (
                <tr>
                  <td colSpan={COLUMNS.length} className="empty">
                    No items in this view.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {pageCount > 1 && (
          <div className="table-pager">
            <button className="btn btn--sm" onClick={() => setPage(safePage - 1)} disabled={safePage === 0}>
              Prev
            </button>
            <span className="pager-info">
              Page {safePage + 1} of {pageCount}
            </span>
            <button
              className="btn btn--sm"
              onClick={() => setPage(safePage + 1)}
              disabled={safePage >= pageCount - 1}
            >
              Next
            </button>
          </div>
        )}
      </div>

      {selected && <ActivityDrawer item={selected} onClose={() => setSelected(null)} />}
    </section>
  );
}
