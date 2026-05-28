"""SAP fuel & procurement adapter — semicolon CSV flat-file export.

Handles the quirks documented in SOURCES.md: German headers, European decimals,
DD.MM.YYYY dates, opaque plant codes, and mixed units. Scope is derived from the
material code: F-* fuels are combusted on-site (Scope 1), P-* are purchased
goods (Scope 3).
"""
import csv
import io

from apps.common.units import to_canonical
from apps.ingestion.services.normalizer import parse_date, parse_decimal

from .base import NormalizedRow

# Maps a SAP material code to (activity_category, scope).
_MATERIAL_MAP = {
    "F-DIESEL": ("diesel", "1"),
    "F-BENZIN": ("petrol", "1"),
    "F-ERDGAS": ("natural_gas", "1"),
    "P-PAPIER": ("purchased_paper", "3"),
}


class SAPAdapter:
    source_type = "sap"

    def parse(self, raw_bytes, config):
        delimiter = config.get("delimiter", ";")
        text = raw_bytes.decode(config.get("encoding", "utf-8-sig"))
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        for i, row in enumerate(reader, start=1):
            yield i, {k: (v or "").strip() for k, v in row.items()}

    def normalize(self, row, config) -> NormalizedRow:
        material = row.get("Material", "")
        category, scope = _MATERIAL_MAP.get(material, (material.lower() or "unknown", "3"))

        raw_qty = parse_decimal(row["Menge"], european=True)
        quantity, unit = to_canonical(raw_qty, row["Einheit"])

        return NormalizedRow(
            activity_category=category,
            scope=scope,
            quantity=quantity,
            unit=unit,
            activity_date=parse_date(row["Buchungsdatum"], dayfirst=True),
            site_code=row.get("Werk", ""),
            extra={"cost_center": row.get("Kostenstelle", ""), "doc": row.get("Belegnummer", "")},
        )
