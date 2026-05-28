import { statusDescription, statusLabel } from "@/lib/labels";

// Status pill. Color + dot (styled in index.css) encode state; the label is
// plain-language and the tooltip explains what the state means.
export function StatusBadge({ status }) {
  return (
    <span className={`badge badge--${status}`} title={statusDescription(status)}>
      {statusLabel(status)}
    </span>
  );
}
