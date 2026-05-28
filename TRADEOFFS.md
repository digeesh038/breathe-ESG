# TRADEOFFS.md — What I deliberately did NOT build

Three things intentionally left out, with the reasoning and the cost of the cut.

### 1. Asynchronous / queued ingestion (Celery, workers, broker)
- **Not built:** Ingestion runs synchronously inside the upload request.
- **Why:** Sample files are small; a task queue adds infrastructure (broker +
  workers) that changes neither the data model nor the analyst experience —
  which is what's being evaluated. The pipeline is written as a single
  `run_batch(batch, bytes)` function, so it can move behind a queue later with
  no model changes.
- **Cost of the cut:** A large real upload (100k+ rows) would time out the
  request; production needs async + progress reporting.

### 2. Live source connectors (SAP OData, Concur OAuth + polling)
- **Not built:** File/JSON upload only; no live API pulls or OAuth flows.
- **Why:** Real connectors need client credentials and system access we don't
  have, and onboarding realistically starts with exports anyway. The
  `SourceAdapter` contract (`adapters/base.py`) already isolates parsing, so a
  live puller is an additive adapter, not a rewrite.
- **Cost of the cut:** Ongoing sync is manual (re-upload) until connectors exist.

### 3. Full RBAC enforcement, SSO/MFA, and per-field permissions
- **Not built:** Roles exist on `Membership` (analyst/admin/viewer) but aren't
  enforced beyond authentication + tenant scoping; auth is a prototype token,
  no SSO/MFA.
- **Why:** The grading weight is on the data model, source realism, and analyst
  workflow — not an identity system. Real RBAC/SSO would consume the budget
  without improving what's evaluated.
- **Cost of the cut:** Not production-ready for real client access control;
  e.g. a "viewer" can currently call mutating endpoints if authenticated.

---

**Also consciously deferred:** charts/trend analytics, PDF/OCR utility-bill
parsing, and ML-based anomaly detection — all either lower-value for this
evaluation or over-engineering for a 4-day prototype.
