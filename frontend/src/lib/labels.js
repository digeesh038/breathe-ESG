// Human-readable labels + plain-language explanations for the domain jargon.
// Kept in one place so the same wording (and tooltip text) is used everywhere.

export const SCOPE_LABELS = {
  1: "Scope 1",
  2: "Scope 2",
  3: "Scope 3",
};

// Shown as tooltips so a non-specialist understands what each scope covers.
export const SCOPE_DESCRIPTIONS = {
  1: "Direct emissions from sources you own or control — e.g. fuel burned on-site or in company vehicles.",
  2: "Indirect emissions from the energy you buy — mainly purchased electricity, heat, or steam.",
  3: "Value-chain emissions you don't directly control — e.g. business travel, purchased goods, suppliers.",
};

export const STATUS_LABELS = {
  pending: "Pending review",
  approved: "Approved",
  locked: "Locked",
  rejected: "Rejected",
  // ingestion batch statuses
  received: "Received",
  parsing: "Processing",
  normalized: "Processed",
  failed: "Failed",
};

export const STATUS_DESCRIPTIONS = {
  pending: "Waiting for an analyst to review and sign off.",
  approved: "Reviewed and accepted.",
  locked: "Signed off and locked — counted in the audit-ready inventory and no longer editable.",
  rejected: "Excluded from reported emissions.",
  received: "Upload received, not yet processed.",
  parsing: "Reading and normalizing the file.",
  normalized: "File processed into reviewable records.",
  failed: "The file couldn't be processed — see notes.",
};

// Anomaly flag kinds -> short label + why it matters.
export const FLAG_LABELS = {
  outlier: "Unusually high",
  missing_factor: "No emission factor",
  unmapped_code: "Unknown site code",
  duplicate: "Possible duplicate",
  unit_guess: "Unit inferred",
  invalid_value: "Invalid value",
  implausible: "Implausible",
};

export function humanize(value) {
  return String(value ?? "").replace(/_/g, " ");
}

export function scopeLabel(scope) {
  return SCOPE_LABELS[scope] ?? `Scope ${scope}`;
}

export function scopeDescription(scope) {
  return SCOPE_DESCRIPTIONS[scope] ?? "";
}

export function statusLabel(status) {
  return STATUS_LABELS[status] ?? humanize(status);
}

export function statusDescription(status) {
  return STATUS_DESCRIPTIONS[status] ?? "";
}

export function flagLabel(kind) {
  return FLAG_LABELS[kind] ?? humanize(kind);
}
