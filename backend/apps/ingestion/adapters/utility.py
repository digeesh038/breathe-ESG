"""Electricity utility adapter — portal CSV export.

Each row (including separate day/night tariff bands) becomes one ActivityRecord,
preserving the 1:1 raw->canonical link; bands sharing a billing period are summed
at reporting time, not at ingest. Electricity is Scope 2 with a region-specific
grid factor. Billing periods are kept as period_start/period_end rather than
forced into a calendar month.
"""
import csv
import io

from apps.common.units import to_canonical
from apps.ingestion.services.normalizer import parse_date, parse_decimal

from .base import NormalizedRow


class UtilityAdapter:
    source_type = "utility"

    def parse(self, raw_bytes, config):
        text = raw_bytes.decode(config.get("encoding", "utf-8-sig"))
        reader = csv.DictReader(io.StringIO(text))
        for i, row in enumerate(reader, start=1):
            yield i, {k: (v or "").strip() for k, v in row.items()}

    def normalize(self, row, config) -> NormalizedRow:
        quantity, unit = to_canonical(parse_decimal(row["consumption"]), row["unit"])
        period_start = parse_date(row["period_start"])
        period_end = parse_date(row["period_end"])
        return NormalizedRow(
            activity_category="grid_electricity",
            scope="2",
            quantity=quantity,
            unit=unit,
            activity_date=period_end,          # attribute to period end
            period_start=period_start,
            period_end=period_end,
            site_code=row.get("meter_id", ""),
            extra={
                "site_name": row.get("site_name", ""),
                "tariff_band": row.get("tariff_band", ""),
                "supplier": row.get("supplier", ""),
            },
        )
