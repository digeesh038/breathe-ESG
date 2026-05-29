import { useMemo, useState } from "react";
import { saveAs } from "file-saver";
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useReviewItems } from "./useReviewItems";
import { ActivityDrawer } from "./ActivityDrawer";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PageHeader } from "@/components/ui/PageHeader";
import { emissionsApi } from "@/api/emissions";
import { formatCo2e } from "@/lib/format";
import { flagLabel, humanize, scopeDescription, scopeLabel } from "@/lib/labels";

// The core analyst surface. TanStack Table gives us sorting/filtering/pagination
// without a heavy grid component. Click a row to drill into source history.
const FILTERS = ["all", "pending", "locked", "rejected"];

export function ReviewPage() {
  const [filter, setFilter] = useState("pending");
  const [globalFilter, setGlobalFilter] = useState("");
  const [sorting, setSorting] = useState([]);
  const [selected, setSelected] = useState(null);

  const [exporting, setExporting] = useState(false);
  const status = filter === "all" ? undefined : filter;
  const { data, isLoading, isError, approve, reject } = useReviewItems(status);

  async function downloadExport(format) {
    setExporting(true);
    try {
      console.log(`Downloading export in format: ${format}`);
      const blob = await emissionsApi.exportActivities(format);
      const ext = format === "xlsx" ? "xlsx" : "csv";
      saveAs(blob, `emissions_${new Date().toISOString().slice(0, 10)}.${ext}`);
    } catch (err) {
      console.error("Export download failed:", err);
      alert(`Export failed: ${err.response?.data?.message || err.message}`);
    } finally {
      setExporting(false);
    }
  }

  const columns = useMemo(
    () => [
      {
        id: "activity",
        header: "Activity",
        accessorFn: (row) => row.activity_detail.activity_category,
        cell: ({ row }) => {
          const a = row.original.activity_detail;
          return (
            <div>
              <div className="cell-primary">{humanize(a.activity_category)}</div>
              <div className="cell-secondary">{a.site_code || "—"} · {a.activity_date}</div>
            </div>
          );
        },
        sortingFn: (a, b) =>
          a.original.activity_detail.activity_category.localeCompare(
            b.original.activity_detail.activity_category,
          ),
      },
      {
        id: "scope",
        header: "Scope",
        accessorFn: (row) => row.activity_detail.scope,
        cell: ({ row }) => {
          const s = row.original.activity_detail.scope;
          return (
            <span className={`chip-scope s${s}`} title={scopeDescription(s)}>
              {scopeLabel(s)}
            </span>
          );
        },
      },
      {
        id: "quantity",
        header: () => <span className="num">Quantity</span>,
        accessorFn: (row) => Number(row.activity_detail.quantity),
        cell: ({ row }) => {
          const a = row.original.activity_detail;
          return (
            <span className="num">
              {Number(a.quantity).toLocaleString()} {a.unit}
            </span>
          );
        },
        meta: { numeric: true },
      },
      {
        id: "co2e",
        header: () => (
          <span className="num" title="Tonnes of CO₂-equivalent — all greenhouse gases expressed as one comparable number.">
            CO₂e
          </span>
        ),
        accessorFn: (row) => Number(row.activity_detail.co2e_kg),
        cell: ({ row }) => (
          <span className="num">{formatCo2e(row.original.activity_detail.co2e_kg)}</span>
        ),
        meta: { numeric: true },
      },
      {
        id: "anomalies",
        header: "Anomalies",
        accessorFn: (row) => row.flags.map((f) => f.kind).join(" "),
        enableSorting: false,
        cell: ({ row }) =>
          row.original.flags.length === 0 ? (
            <span className="muted">—</span>
          ) : (
            row.original.flags.map((flag) => (
              <span key={flag.id} className="flag" title={flag.detail}>
                {flagLabel(flag.kind)}
              </span>
            ))
          ),
      },
      {
        id: "status",
        header: "Status",
        accessorKey: "status",
        cell: ({ row }) => <StatusBadge status={row.original.status} />,
      },
      {
        id: "actions",
        header: "Actions",
        enableSorting: false,
        cell: ({ row }) => {
          const item = row.original;
          const pending = item.status === "pending";
          return (
            <div onClick={(e) => e.stopPropagation()}>
              {pending ? (
                <div className="btn-row">
                  <button
                    className="btn btn--sm btn--approve"
                    onClick={() => approve.mutate({ id: item.id })}
                  >
                    Approve
                  </button>
                  <button
                    className="btn btn--sm btn--reject"
                    onClick={() => reject.mutate({ id: item.id })}
                  >
                    Reject
                  </button>
                </div>
              ) : (
                <span className="muted">{item.reviewed_at ? "signed off" : "—"}</span>
              )}
            </div>
          );
        },
      },
    ],
    [approve, reject],
  );

  const table = useReactTable({
    data: data ?? [],
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 25 } },
  });

  const total = table.getFilteredRowModel().rows.length;

  return (
    <section>
      <PageHeader
        title="Review & sign-off"
        subtitle="Click a row to inspect its source and edit. Approve to lock for audit."
        actions={
          <div className="btn-row">
            <button
              className="btn btn--sm"
              onClick={() => downloadExport("csv")}
              disabled={exporting}
            >
              Export CSV
            </button>
            <button
              className="btn btn--sm"
              onClick={() => downloadExport("xlsx")}
              disabled={exporting}
            >
              Export XLSX
            </button>
          </div>
        }
      />

      <div className="segmented">
        {FILTERS.map((f) => (
          <button
            key={f}
            className="seg-btn"
            onClick={() => setFilter(f)}
            aria-pressed={filter === f}
          >
            {f}
          </button>
        ))}
        <input
          className="seg-search"
          type="search"
          placeholder="Filter rows…"
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
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
              {table.getHeaderGroups().map((hg) => (
                <tr key={hg.id}>
                  {hg.headers.map((h) => {
                    const canSort = h.column.getCanSort();
                    const sortDir = h.column.getIsSorted();
                    return (
                      <th
                        key={h.id}
                        onClick={canSort ? h.column.getToggleSortingHandler() : undefined}
                        className={canSort ? "th-sortable" : undefined}
                      >
                        {flexRender(h.column.columnDef.header, h.getContext())}
                        {sortDir === "asc" && <span className="sort-ind"> ▲</span>}
                        {sortDir === "desc" && <span className="sort-ind"> ▼</span>}
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => setSelected(row.original)}
                  className={selected?.id === row.original.id ? "row-selected" : undefined}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                  ))}
                </tr>
              ))}
              {total === 0 && !isLoading && !isError && (
                <tr>
                  <td colSpan={columns.length} className="empty">
                    No items in this view.
                  </td>
                </tr>
              )}
              {isLoading && (
                <tr>
                  <td colSpan={columns.length} className="empty">
                    Loading…
                  </td>
                </tr>
              )}
              {isError && (
                <tr>
                  <td colSpan={columns.length} className="empty error-text">
                    Couldn&apos;t load review items.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {total > table.getState().pagination.pageSize && (
          <div className="table-pager">
            <button
              className="btn btn--sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              Prev
            </button>
            <span className="pager-info">
              Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
            </span>
            <button
              className="btn btn--sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
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
