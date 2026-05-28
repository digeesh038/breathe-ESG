# MODEL.md — Data model & rationale

## Guiding principle

**Separate what arrived from what we made of it.** Raw source rows are stored
verbatim and never mutated; a separate canonical table holds the normalized,
calculated emissions that are the source of truth for audit. This preserves
provenance and lets normalization be re-run without re-uploading.

```
Organization (tenant)
  └─ SourceConnection ─< IngestionBatch ─< RawRecord ──1:1── ActivityRecord
                                                              │
ReviewItem ──1:1── ActivityRecord                            ├─ EmissionFactor (FK, pinned)
   └─< AnomalyFlag                                            └─ site_code → PlantCode (lookup)
AuditEvent (append-only, generic target reference)
```

## Tables (see `backend/apps/*/models.py`)

### Multi-tenancy — `apps/tenants`
- **Organization** is the tenant boundary. Isolation is **row-level**: every
  tenant-owned table carries an `organization` FK (via the `TenantScopedModel`
  abstract base) and querysets are filtered by the active org. Chosen over
  schema-/database-per-tenant because a consultancy like Breathe has analysts
  working across many client orgs; row-level keeps cross-tenant queries and a
  single migration path simple for a prototype.
- **User** (custom) + **Membership** (user × org, with `role`:
  analyst/admin/viewer). Membership is many-to-many because one analyst reviews
  several client orgs. The active org is resolved per request from the
  `X-Organization` header, validated against membership in `TenantViewSetMixin`.

### Reference / master data — `apps/reference`
- **EmissionFactor** — kg CO₂e per canonical unit, **versioned** by
  `valid_year` + `source` + `region`. Versioning matters because auditors need
  to know *which* factor was applied; factors are never overwritten. The factor
  used is pinned as a FK on each `ActivityRecord`, so the calculation is
  reproducible years later.
- **PlantCode** — maps an opaque SAP plant / cost-center code to a site +
  region (tenant-scoped).
- **AirportCode** — IATA → lat/long, so flights given only as codes can have
  distance estimated (great-circle).

### Ingestion staging — `apps/ingestion`
- **SourceConnection** — a configured source for a tenant; `config` JSON holds
  per-source quirks (delimiter, header language, encoding).
- **IngestionBatch** — one upload/pull; the unit of provenance, with `status`,
  `row_count`, `error_count`.
- **RawRecord** — one source row stored **exactly as received** (`payload`
  JSON) plus its parse `status` and `error`. Bad rows are kept and surfaced in
  the dashboard, never silently dropped.

### Canonical emissions — `apps/emissions`
- **ActivityRecord** — the source of truth. Carries:
  - **Provenance:** `raw_record` (1:1) + `batch` FKs → trace any number back to
    the exact bytes (surfaced as "source history" in the UI drilldown).
  - **Classification:** `activity_category`, `scope` (1/2/3), `site_code`,
    `activity_date`, plus `period_start`/`period_end` for non-calendar utility
    bills.
  - **Unit normalization:** `unit` is canonical; `original_quantity` vs
    `quantity` + `is_edited` capture analyst overrides (an edit recomputes
    CO₂e and writes an audit event; edits are blocked once locked/rejected).
  - **Reproducible math:** pinned `emission_factor` FK + computed `co2e_kg`.

### Review workflow — `apps/review`
- **ReviewItem** (1:1 with ActivityRecord) — lifecycle `pending → locked`
  (approve) or `pending → rejected`. Modeled separately so workflow state never
  pollutes the canonical record. Approval = "locked for audit".
- **AnomalyFlag** — typed reasons a row "looks suspicious", each with a
  human-readable `detail`: `missing_factor`, `unmapped_code`, `duplicate`,
  `outlier`, `invalid_value` (negative/zero), `implausible` (impossible flight
  distance or reversed/absurd billing period).

### Audit trail — `apps/audit`
- **AuditEvent** — append-only log (`created` on ingest, `edited`, `locked`,
  `rejected`) with actor, generic target (`target_model` + `target_id`), and a
  `changes` before/after diff. Survives deletion of the target; never updated
  or deleted (enforced in admin too).

## How the model satisfies each required concern
| Requirement | Where |
|---|---|
| Multi-tenancy | `TenantScopedModel.organization` + `TenantViewSetMixin` (header-resolved, membership-validated) |
| Scope 1/2/3 | `Scope` choices on `EmissionFactor` and `ActivityRecord` |
| Source-of-truth tracking | `ActivityRecord.raw_record`/`batch`, `is_edited`, `original_quantity` vs `quantity` |
| Unit normalization | `apps/common/units.py` registry → canonical `unit` on records |
| Audit trail | `apps/audit.AuditEvent` (append-only; written on ingest/edit/approve/reject) |
| Data quality score | `data_quality_score` (0–1) on the activity serializer, computed from unresolved `AnomalyFlag`s with per-kind weights (see `apps/emissions/serializers.py::FLAG_WEIGHTS`). Not stored — derived on read so it stays in sync with flag resolution. |
| Background ingestion | `apps/ingestion/tasks.py::run_batch_task` (Celery). The view base64-encodes the upload payload, enqueues the task, and returns the queued batch; the worker runs the same `services.pipeline.run_batch` as the sync path. Dev defaults to `CELERY_TASK_ALWAYS_EAGER=True` so a worker isn't required. |
| JWT auth | `rest_framework_simplejwt` with `Authorization: Bearer <access>`; refresh rotation enabled and old refreshes blacklisted on rotation. |

## Known limitations (honest)
- `EmissionFactor` is global, not tenant-scoped (factors come from public
  datasets like DEFRA/IEA). Fine for a prototype; a client mandating a specific
  factor set would need tenant overrides.
- Region is not yet derived from `site_code`, so grid-electricity uses the
  blank-region factor even for German sites (a DE factor exists but is unused).

## Production hardening (added)
- **RBAC** — `OrgRolePermission` on every tenant viewset: any member can read,
  `analyst`/`admin` can write, source management is `admin`-only. Reads/writes
  are still org-scoped by the `TenantViewSetMixin` (see `apps/common/`).
- **Uploads** persist to MEDIA storage (`IngestionBatch.media_file`; local disk
  in dev, S3 in prod via `USE_S3`). The Celery worker reads bytes from storage,
  not through the broker. Size + row-count caps reject pathological files.
- **Re-ingestion idempotency** — `IngestionBatch.content_hash` (SHA-256) flags a
  re-upload of the same file for the same source (noted, not blocked).
- **Auth** — SimpleJWT with a logout/blacklist endpoint; login + upload are
  rate-limited (`apps/common/throttling.py`).
- **Tests** — `pytest` suite covers auth, tenant isolation, RBAC, the calculator,
  anomaly rules, and the end-to-end ingestion pipeline.
