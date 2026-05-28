"""Adapter contract for every source type.

An adapter does two things and nothing else: `parse` a raw file into rows that
get stored verbatim as RawRecords, and `normalize` one stored row into a
source-agnostic NormalizedRow. It must not write to the database (reference
lookups for distance estimation are the one read-only exception) or apply
emission factors — that is the calculator's job. Each source's quirks stay
quarantined in one small, testable class.

To add a 4th source: add one module here and register it in the pipeline's
ADAPTERS map. Nothing else changes.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Iterator, Optional, Protocol


@dataclass
class NormalizedRow:
    """Source-agnostic intermediate the calculator understands."""

    activity_category: str            # maps to EmissionFactor.activity_category
    scope: str                        # "1" | "2" | "3"
    quantity: Decimal                 # already in canonical unit
    unit: str                         # canonical unit (kWh, L, m3, kg, km, night)
    activity_date: date
    site_code: str = ""               # plant code / facility / cost center
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    source_row_ref: int = 0           # links back to RawRecord.row_number
    extra: dict = field(default_factory=dict)  # e.g. {"unit_guessed": True}


class SourceAdapter(Protocol):
    source_type: str

    def parse(self, raw_bytes: bytes, config: dict) -> Iterator[tuple[int, dict]]:
        """Yield (row_number, original_column_dict) for storage as RawRecord."""

    def normalize(self, row: dict, config: dict) -> NormalizedRow:
        """Map one raw row to a NormalizedRow. Raise IngestionError on bad data."""
