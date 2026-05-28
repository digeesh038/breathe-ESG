import { useQuery } from "@tanstack/react-query";
import { ingestionApi } from "@/api/ingestion";
import { PageHeader } from "@/components/ui/PageHeader";
import { Icon } from "@/components/ui/Icon";

// Configured source connections (SAP / utility / travel) for the active tenant.
const META = {
  sap: { label: "SAP fuel & procurement", icon: "database", blurb: "Semicolon CSV export · German headers" },
  utility: { label: "Electricity utility", icon: "upload", blurb: "Portal CSV · billing periods & tariff bands" },
  travel: { label: "Corporate travel", icon: "review", blurb: "Concur/Navan JSON · trips & segments" },
};

export function SourcesPage() {
  const sources = useQuery({ queryKey: ["sources"], queryFn: ingestionApi.listSources });
  const data = sources.data ?? [];

  return (
    <section>
      <PageHeader title="Sources" subtitle="Connected data sources feeding the ingestion pipeline." />

      {data.length === 0 ? (
        <div className="panel"><div className="empty">No sources configured yet.</div></div>
      ) : (
        <div className="source-grid">
          {data.map((s) => {
            const meta = META[s.source_type] ?? { label: s.source_type, icon: "database", blurb: "" };
            return (
              <div className="source-card" key={s.id}>
                <span className="source-icon"><Icon name={meta.icon} size={20} /></span>
                <h3>{s.name}</h3>
                <div className="source-type">{meta.label}</div>
                <div className="source-config">
                  <div className="cell-secondary" style={{ marginBottom: 6 }}>{meta.blurb}</div>
                  <code>{JSON.stringify(s.config)}</code>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
