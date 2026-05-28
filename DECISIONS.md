# DECISIONS.md — Ambiguities resolved & open questions

Each entry: the ambiguity, what was chosen, why, and what I'd ask the PM.

---

### 1. Multi-tenancy isolation model
- **Chose:** Row-level isolation (shared schema, `organization` FK + querysets
  filtered by the active org).
- **Why:** Breathe's analysts review multiple client orgs; shared-schema makes
  cross-client work and migrations simple for a prototype. Schema/db-per-tenant
  is stronger isolation but heavier to operate at this stage.
- **Would ask PM:** Do any clients contractually require physical data
  isolation? That would push us to schema-per-tenant.

### 2. Tenant resolution at request time
- **Chose:** `X-Organization` header, validated against the user's memberships
  in a viewset mixin (resolved *after* auth, not in middleware).
- **Why:** With token auth, `request.user` isn't populated during middleware,
  so the org must be resolved in the view layer. An explicit header keeps the
  SPA in control of "which client am I looking at".
- **Would ask PM:** Subdomain-per-tenant, or an in-app org switcher? (The data
  model supports either.)

### 3. Authentication
- **Chose:** DRF **TokenAuthentication only** for the API; the SPA stores the
  token and sends `Authorization: Token …`.
- **Why:** I initially enabled SessionAuthentication too, but cookies on
  `localhost` are shared across ports, so a Django-admin session cookie made
  DRF treat SPA requests as session-authenticated and enforce CSRF → 403 on
  POSTs. Token-only removes that coupling and is the standard SPA pattern.
- **Would ask PM:** Is SSO/OIDC required for the real deployment? (Token is a
  prototype choice, not production identity.)

### 4. Raw vs canonical separation
- **Chose:** Store every source row verbatim (`RawRecord`) separately from the
  normalized `ActivityRecord` (1:1).
- **Why:** Auditability and re-runnable normalization; one bad row shouldn't
  block a batch, and analysts can see the exact source bytes behind any number.
- **Would ask PM:** How long must raw payloads be retained for compliance?

### 5. SAP ingestion mechanism
- **Chose:** Semicolon-delimited **flat-file CSV export** (not OData/BAPI/IDoc).
- **Why:** It's what a client can hand over on day one without granting SAP
  system access. The adapter contract isolates parsing so a live connector is
  an additive change later.
- **Handled subset:** fuel line items (F-* materials → Scope 1) and simple
  procurement (P-* → Scope 3), German headers, European decimals, DD.MM.YYYY.
- **Ignored:** pricing, vendor master, reversals, multi-currency.
- **Would ask PM:** Will we eventually get OData access? Which SAP config /
  column language do the real exports use?

### 6. Utility ingestion mechanism
- **Chose:** Portal **CSV export** of billed consumption (not PDF or API).
- **Why:** Facilities teams routinely download CSVs; PDF parsing is brittle and
  most suppliers expose no API.
- **Decision — tariff bands:** day/night bands are kept as **separate**
  ActivityRecords sharing a billing period (preserves the 1:1 raw→canonical
  link); summing happens at reporting time, not ingest.
- **Would ask PM:** Which utilities/regions, so we know the grid factors and
  tariff structures to support? Should bands be pre-summed?

### 7. Travel ingestion mechanism
- **Chose:** **JSON** modeled on the Concur/Navan trip→segment structure.
- **Why:** Preserves the nested segment shape; matches how platforms expose data
  and demonstrates API-style ingestion.
- **Decision — distances:** when a flight gives only IATA codes, estimate
  great-circle distance from `AirportCode`; when a distance *is* supplied, we
  still estimate and flag it `implausible` if it's <0.5× or >2× the estimate.
- **Would ask PM:** Great-circle vs actual routed distance? Apply a
  radiative-forcing uplift to flights?

### 8. Emission-factor scope & values
- **Chose:** Global (not tenant-scoped) factor table, versioned by
  year/region/source; illustrative DEFRA/IEA-style values.
- **Why:** Factors are public datasets; sharing avoids duplication and keeps the
  version applied auditable. `purchased_paper` has **no** factor on purpose, to
  demonstrate the `missing_factor` flag.
- **Would ask PM:** Which factor set/version is authoritative for this client?

### 9. Anomaly detection approach
- **Chose:** Explicit **rule-based** checks (missing factor, unmapped code,
  duplicate, outlier, invalid value, implausible), each with a readable reason.
- **Why:** Analysts must trust *why* a row is flagged; a black-box model would
  undermine that for a prototype. The outlier rule uses a 3× category-average
  test when history exists, else a soft per-unit cap (a deliberate placeholder).
- **Would ask PM:** Is there enough historical data to justify statistical
  baselines per site/category?

### 10. Locking semantics
- **Chose:** Approval transitions the ReviewItem to `locked`; the underlying
  ActivityRecord becomes read-only (edits rejected server-side).
- **Why:** "Locked for audit" must be immutable.
- **Would ask PM:** Who (if anyone) can unlock, and is unlocking itself an
  audited event?
