# SOURCES.md — Per-source research, sample data & failure modes

For each source: the real-world format researched, what was learned, what the
sample data looks like and why, and what would break in a real deployment.

---

## 1. SAP — fuel & procurement

**Formats considered:** IDoc (XML EDI), OData services (live REST), BAPI/RFC
(function-call API), and flat-file table/ALV exports.

**Chosen:** Flat-file **CSV export** (a downloaded ALV grid / table extract).
It's what a client can produce on day one without granting SAP system access;
the others require integration credentials and a longer onboarding.

**What I learned / quirks handled** (`sample_data/sap_fuel_procurement.csv`):
- **German column headers** in many configs: `Werk` (plant), `Kostenstelle`
  (cost center), `Menge` (quantity), `Einheit` (unit), `Buchungsdatum` (posting
  date), `Belegnummer` (document no.).
- **Semicolon delimiter** and **European decimals** (`12.450,75` = 12,450.75).
- **`DD.MM.YYYY`** dates.
- **Plant codes** (`Werk`) are meaningless without the `PlantCode` lookup.
- **Mixed units:** L (diesel/petrol), M3 (gas), KG/TO (procurement mass).
- **Scope split:** F-* materials = combusted fuel → Scope 1; P-* = purchased
  goods → Scope 3 (derived from the material code).

**Intentional dirty data:** plant code `2001` is left **unmapped** (→
`unmapped_code` flag) and `P-PAPIER` has **no emission factor** (→
`missing_factor` flag), to exercise validation.

**Handled subset:** fuel line items + simple procurement quantities.
**Ignored:** pricing, vendor master, reversals, multi-currency.

**What would break in production:** exports vary by client SAP config (column
order/language/extra columns); unmapped plant codes; units outside the
conversion table. All surface as flagged or failed rows, not crashes.

---

## 2. Electricity — utility

**Formats considered:** supplier **portal CSV export**, **PDF bill**, **utility
API** (rare for small suppliers; Green Button in the US).

**Chosen:** Portal **CSV export** of billed consumption. Facilities teams
routinely download these; PDF parsing is brittle and most suppliers expose no
API.

**What I learned / quirks handled** (`sample_data/utility_electricity.csv`):
- **Billing periods don't align to calendar months** (e.g. 14 Mar–12 Apr) —
  stored as `period_start`/`period_end`, not forced into a month.
- **Units vary:** kWh vs MWh (normalized to kWh).
- **Tariff bands** (day/night) split one period into multiple rows kept as
  separate records sharing the period; summed at reporting time.
- Electricity = **Scope 2** with a region-specific grid factor.

**Intentional dirty data:** a **negative consumption** row (→ `invalid_value`)
and a row whose `period_end` precedes `period_start` (→ `implausible`).

**Handled subset:** electricity consumption with periods + tariff bands.
**Ignored:** standing charges, demand (kVA) charges, gas/water, on-site solar.

**What would break in production:** estimated vs actual reads, period overlaps
across exports (double counting), and missing region → wrong/blank grid factor.

---

## 3. Corporate travel — flights, hotels, ground

**Formats considered:** **Concur** (trips with segments; reporting API),
**Navan** (similar trip/segment model), flattened CSV exports.

**Chosen:** **JSON** modeled on the Concur/Navan trip→segment structure — it
preserves the nested shape better than a flattened CSV and demonstrates
API-style ingestion.

**What I learned / quirks handled** (`sample_data/travel_concur.json`):
- **Category drives the factor:** flight (short/long haul) vs hotel-night vs
  rail vs ground/taxi.
- **Flights often give only IATA origin/dest**, `distance_km: null` → estimate
  great-circle distance via `AirportCode`, then bucket by haul length.
- **Cabin class** is captured (economy/business).
- All business travel = **Scope 3**.

**Intentional dirty data:** a LHR→JFK flight with a supplied `distance_km` of
**50** (vs ~5,540 expected) → `implausible` flag, demonstrating the
given-vs-estimate sanity check.

**Handled subset:** flights (with distance estimation), hotel nights, rail,
ground.
**Ignored:** rental-car fuel detail, multi-leg fare allocation, currency.

**What would break in production:** unknown IATA codes (→ row fails with a clear
reason), ground segments lacking both distance and duration, and trips spanning
reporting periods.

---

## Emission factors

Values in `seed_demo` are **illustrative**, DEFRA/IEA-style (e.g. diesel
2.68 kg/L, UK grid 0.207 kg/kWh). They are versioned by year/source/region and
pinned per record. **Before any real use, replace them with an authoritative,
dated factor set** — the model already supports versioning for exactly this.
