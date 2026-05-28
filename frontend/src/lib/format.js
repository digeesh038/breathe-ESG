// Small pure formatters shared across features. Keep display logic out of
// components so it can be unit-tested.

export function formatCo2e(kg) {
  if (kg == null) return "—";
  const tonnes = Number(kg) / 1000;
  return `${tonnes.toLocaleString(undefined, { maximumFractionDigits: 2 })} t CO₂e`;
}

// Split form for stat cards: the number and unit are returned separately so
// the unit can be rendered smaller/muted next to a large value.
export function formatCo2eParts(kg) {
  if (kg == null) return { value: "—", unit: "" };
  const tonnes = Number(kg) / 1000;
  return {
    value: tonnes.toLocaleString(undefined, { maximumFractionDigits: 2 }),
    unit: "t CO₂e",
  };
}

export function formatDate(iso) {
  return new Date(iso).toLocaleDateString();
}
