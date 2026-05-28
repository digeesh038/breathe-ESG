"""Shared tolerant-parsing helpers used by the adapters.

Centralized so date/number quirks (German `1.234,56`, `DD.MM.YYYY`) are parsed
and tested in one place instead of being re-implemented per source.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from dateutil import parser as date_parser

from apps.common.exceptions import IngestionError


def parse_date(value, *, dayfirst: bool = False) -> date:
    """Parse a date from many formats. `dayfirst=True` for European `DD.MM.YYYY`."""
    if isinstance(value, date):
        return value
    try:
        return date_parser.parse(str(value).strip(), dayfirst=dayfirst).date()
    except (ValueError, OverflowError) as exc:
        raise IngestionError(f"Unparseable date: {value!r}") from exc


def parse_decimal(value, *, european: bool = False) -> Decimal:
    """Parse a number. `european=True` treats '.' as thousands and ',' as decimal."""
    if value is None or str(value).strip() == "":
        raise IngestionError("Missing numeric value")
    text = str(value).strip()
    if european:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", "")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise IngestionError(f"Unparseable number: {value!r}") from exc
