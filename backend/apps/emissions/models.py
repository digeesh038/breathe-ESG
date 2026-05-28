"""Canonical, normalized emissions data — the source of truth for audit.

One ActivityRecord = one normalized activity (X litres of diesel at site Y on
date Z) with its computed CO2e. Every record points back to the RawRecord
and IngestionBatch it came from (provenance) and records the EmissionFactor
version actually applied (so the math is reproducible years later).

source-of-truth / edit tracking is explicit here: original_quantity vs
quantity, plus an `is_edited` flag and the audit app's event log capture
whether an analyst overrode an ingested value before approval.
"""
from django.db import models

from apps.common.models import AuthoredModel, TenantScopedModel
from apps.reference.models import Scope


class ActivityRecord(TenantScopedModel, AuthoredModel):
    # --- provenance (which source produced this row, when) ---
    raw_record = models.OneToOneField(
        "ingestion.RawRecord", on_delete=models.PROTECT, related_name="activity"
    )
    batch = models.ForeignKey(
        "ingestion.IngestionBatch", on_delete=models.PROTECT, related_name="activities"
    )

    # --- classification ---
    activity_category = models.CharField(max_length=64)
    scope = models.CharField(max_length=1, choices=Scope.choices)
    site_code = models.CharField(max_length=32, blank=True)
    activity_date = models.DateField()
    period_start = models.DateField(null=True, blank=True)  # for non-monthly utility bills
    period_end = models.DateField(null=True, blank=True)

    # --- normalized quantity (canonical units) ---
    unit = models.CharField(max_length=16)
    original_quantity = models.DecimalField(max_digits=18, decimal_places=4)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    is_edited = models.BooleanField(default=False)

    # --- computed emissions + the factor actually applied ---
    emission_factor = models.ForeignKey(
        "reference.EmissionFactor", on_delete=models.PROTECT, null=True, blank=True
    )
    co2e_kg = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "scope", "activity_date"]),
        ]
