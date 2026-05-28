"""Unit normalization registry.

Every ingested quantity is converted to a single canonical unit per dimension
before any emission factor is applied, so conversions are auditable and live as
data in one place rather than scattered through adapters.

Canonical units: energy -> kWh, liquid volume -> L, gas volume -> m3,
mass -> kg, distance -> km, plus pass-through units like `night`.

`to_canonical()` maps a source unit token to (converted_value, canonical_unit).
The factor table is intentionally explicit so a reviewer can see exactly what
multiplier was applied.
"""
from decimal import Decimal

from .exceptions import UnknownUnitError

# source unit token (case-insensitive) -> (canonical unit, multiplier)
_UNIT_TABLE: dict[str, tuple[str, str]] = {
    # liquid volume -> L
    "l": ("L", "1"),
    "gal": ("L", "3.78541"),
    "gal_us": ("L", "3.78541"),
    # gas volume -> m3 (kept distinct from liquid; gas factors are per m3)
    "m3": ("m3", "1"),
    "cbm": ("m3", "1"),
    # mass -> kg
    "kg": ("kg", "1"),
    "to": ("kg", "1000"),   # metric tonne (SAP "TO")
    "t": ("kg", "1000"),
    # energy -> kWh
    "kwh": ("kWh", "1"),
    "wh": ("kWh", "0.001"),
    "mwh": ("kWh", "1000"),
    # distance -> km
    "km": ("km", "1"),
    "mi": ("km", "1.60934"),
    # pass-through
    "night": ("night", "1"),
}


def to_canonical(value, unit: str) -> tuple[Decimal, str]:
    key = (unit or "").strip().lower()
    if key not in _UNIT_TABLE:
        raise UnknownUnitError(f"Unknown unit: {unit!r}")
    canonical_unit, multiplier = _UNIT_TABLE[key]
    return (Decimal(str(value)) * Decimal(multiplier), canonical_unit)
