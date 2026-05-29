import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ingestionApi } from "@/api/ingestion";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PageHeader } from "@/components/ui/PageHeader";

// Upload a file against a source and watch the batch process. row_count vs
// error_count shows the analyst "what came in / what failed" at a glance.
export function IngestionPage() {
  const qc = useQueryClient();
  const fileRef = useRef(null);
  const [sourceId, setSourceId] = useState("");
  const [message, setMessage] = useState("");

  const sources = useQuery({ queryKey: ["sources"], queryFn: ingestionApi.listSources });
  const batches = useQuery({ queryKey: ["batches"], queryFn: ingestionApi.listBatches });
  const sourceName = (id) => (sources.data ?? []).find((s) => s.id === id)?.name ?? `#${id}`;

  const upload = useMutation({
    mutationFn: ({ id, file }) => ingestionApi.upload(id, file),
    onSuccess: (batch) => {
      if (batch.status === "failed") {
        setMessage(
          batch.notes ||
            `Couldn't ingest ${batch.original_filename}: all ${batch.row_count} rows failed — check the file matches the selected source type.`,
        );
      } else {
        setMessage(`Ingested ${batch.original_filename}: ${batch.row_count} rows, ${batch.error_count} errors.`);
      }
      qc.invalidateQueries({ queryKey: ["batches"] });
      qc.invalidateQueries({ queryKey: ["review-items"] });
      qc.invalidateQueries({ queryKey: ["activities"] });
      qc.invalidateQueries({ queryKey: ["summary"] });
      if (fileRef.current) fileRef.current.value = "";
    },
    onError: (err) =>
      setMessage(`Upload failed: ${err.response?.data?.detail || err.message}`),
  });

  function onSubmit(e) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!sourceId || !file) { setMessage("Pick a source and a file."); return; }
    upload.mutate({ id: Number(sourceId), file });
  }

  return (
    <section>
      <PageHeader title="Ingestion" subtitle="Upload a source export and track what came in versus what failed." />

      <div className="panel" style={{ marginBottom: "1.5rem" }}>
        <div className="panel-head"><span className="panel-title">New upload</span></div>
        <form className="toolbar" style={{ padding: "1rem 1.1rem" }} onSubmit={onSubmit}>
          <select className="select" value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
            <option value="">Select source…</option>
            {(sources.data ?? []).map((s) => (
              <option key={s.id} value={s.id}>{s.name} ({s.source_type})</option>
            ))}
          </select>
          <input ref={fileRef} type="file" accept=".csv,.tsv,.txt,.xlsx,.xls" />
          <button type="submit" className="btn btn--primary" disabled={upload.isPending}>
            {upload.isPending ? "Uploading…" : "Upload & ingest"}
          </button>
          {message && <span className="muted">{message}</span>}
        </form>
        <p className="form-hint" style={{ padding: "0 1.1rem 1rem", margin: 0 }}>
          Accepted: CSV, TSV, or Excel (.xlsx/.xls), up to 25&nbsp;MB. The file is processed into
          reviewable records — check the <strong>Errors</strong> column for rows that couldn&apos;t be read.
        </p>
      </div>

      <div className="panel">
        <div className="panel-head">
          <span className="panel-title">Ingestion batches</span>
          <span className="panel-note">{batches.data?.length ?? 0} batches</span>
        </div>
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>File</th><th>Source</th><th>Status</th>
                <th className="num">Rows</th><th className="num">Errors</th><th>Received</th>
              </tr>
            </thead>
            <tbody>
              {(batches.data ?? []).map((b) => (
                <tr key={b.id}>
                  <td className="cell-primary">{b.original_filename}</td>
                  <td>{sourceName(b.source)}</td>
                  <td><StatusBadge status={b.status} /></td>
                  <td className="num">{b.row_count}</td>
                  <td className="num">{b.error_count > 0 ? <span className="error-text">{b.error_count}</span> : 0}</td>
                  <td className="muted">{new Date(b.received_at).toLocaleString()}</td>
                </tr>
              ))}
              {batches.data?.length === 0 && <tr><td colSpan={6} className="empty">No batches yet — upload a file above.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
