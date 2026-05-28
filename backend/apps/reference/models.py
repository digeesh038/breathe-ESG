"""Reference / master data used to interpret and convert raw source rows.

These are the "lookup tables" the assignment warns about: a SAP plant code
or cost center means nothing without a mapping, an airport code must resolve
to coordinates to estimate flight distance, and an emission factor is what
turns normalized activity into CO2e. Emission factors are versioned by
year/source because auditors care *which* factor was applied and when.
"""
from django.db import models

from apps.common.models import TimeStampedModel


class Scope(models.TextChoices):
    SCOPE_1 = "1", "Scope 1 (direct)"
    SCOPE_2 = "2", "Scope 2 (purchased energy)"
    SCOPE_3 = "3", "Scope 3 (value chain)"


class EmissionFactor(TimeStampedModel):
    """kg CO2e per unit of a normalized activity, for a given category/region/year."""

    activity_category = models.CharField(max_length=64)   # e.g. "diesel", "grid_electricity", "flight_short_haul"
    scope = models.CharField(max_length=1, choices=Scope.choices)
    unit = models.CharField(max_length=16)                # canonical unit the factor expects (L, kWh, km...)
    co2e_per_unit = models.DecimalField(max_digits=18, decimal_places=6)
    region = models.CharField(max_length=64, blank=True)  # grid factors are region-specific
    valid_year = models.PositiveIntegerField()
    source = models.CharField(max_length=128)             # e.g. "DEFRA 2024", "IEA 2023"

    class Meta:
        ordering = ["activity_category", "region"]
        unique_together = ("activity_category", "region", "valid_year", "source")


class PlantCode(TimeStampedModel):
    """Maps an opaque SAP plant / cost center code to a human site + scope hint."""

    organization = models.ForeignKey("tenants.Organization", on_delete=models.CASCADE)
    code = models.CharField(max_length=32)
    site_name = models.CharField(max_length=255)
    region = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["code"]
        unique_together = ("organization", "code")


class AirportCode(TimeStampedModel):
    """IATA code -> coordinates, so flights given only as ORIGIN/DEST can be estimated."""

    iata = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        ordering = ["iata"]
