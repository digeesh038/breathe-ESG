# Sample data

Small, intentionally messy fixtures that mirror each real source's shape.
They exist to exercise the adapters and the review dashboard, and every quirk
here is explained in `../../SOURCES.md`.

- `sap_fuel_procurement.csv` — semicolon-delimited, **German headers**
  (Werk=plant, Menge=quantity, Einheit=unit, Buchungsdatum=posting date),
  **European decimals** (`12.450,75`), `DD.MM.YYYY` dates, units mixing L/M3/KG.
- `utility_electricity.csv` — **non-calendar billing periods**, kWh vs MWh,
  consumption split across day/night tariff bands that must be summed.
- `travel_concur.json` — Concur/Navan-style nested trips→segments; some
  **flights have `distance_km: null`** (only IATA codes), so distance must be
  estimated.
