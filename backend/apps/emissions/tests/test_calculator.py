"""Emission-factor resolution + CO2e math."""
from datetime import date

import pytest

from apps.emissions.services.calculator import resolve_factor
from apps.reference.models import EmissionFactor

pytestmark = pytest.mark.django_db


def test_resolve_prefers_reporting_year():
    EmissionFactor.objects.create(activity_category="diesel", scope="1", unit="L",
                                  co2e_per_unit="2.60", region="", valid_year=2023, source="DEFRA 2023")
    EmissionFactor.objects.create(activity_category="diesel", scope="1", unit="L",
                                  co2e_per_unit="2.68", region="", valid_year=2025, source="DEFRA 2025")

    factor = resolve_factor("diesel", date(2025, 6, 1))
    assert factor.valid_year == 2025


def test_resolve_falls_back_to_latest_when_year_missing():
    EmissionFactor.objects.create(activity_category="diesel", scope="1", unit="L",
                                  co2e_per_unit="2.60", region="", valid_year=2023, source="DEFRA 2023")
    factor = resolve_factor("diesel", date(2030, 1, 1))
    assert factor.valid_year == 2023  # most recent available


def test_resolve_returns_none_when_no_factor():
    assert resolve_factor("unobtanium", date(2025, 1, 1)) is None
