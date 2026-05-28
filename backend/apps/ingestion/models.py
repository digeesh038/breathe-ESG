"""Ingestion staging layer.

The design separates *what arrived* (RawRecord, kept verbatim) from *what we
made of it* (emissions.ActivityRecord). This is deliberate: auditors and
analysts must be able to trace any normalized number back to the exact bytes
that produced it, and we must be able to re-run normalization without
re-uploading. Nothing here is ever silently overwritten.
"""
from django.db import models

from apps.common.models import AuthoredModel, TenantScopedModel


class SourceType(models.TextChoices):
    SAP = "sap", "SAP (fuel & procurement)"
    UTILITY = "utility", "Utility (electricity)"
    TRAVEL = "travel", "Corporate travel"


class SourceConnection(TenantScopedModel):
    """A configured source for a tenant (e.g. 'Acme SAP flat-file export').

    Holds the ingestion mechanism and per-source config (delimiter, header
    language, timezone, default units) so adapters stay generic.
    """

    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=16, choices=SourceType.choices)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]


class IngestionBatch(TenantScopedModel, AuthoredModel):
    """One upload / pull. The unit of provenance the analyst reasons about."""

    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PARSING = "parsing", "Parsing"
        NORMALIZED = "normalized", "Normalized"
        FAILED = "failed", "Failed"

    source = models.ForeignKey(SourceConnection, on_delete=models.PROTECT, related_name="batches")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RECEIVED)
    original_filename = models.CharField(max_length=512, blank=True)
    # The uploaded file persisted to MEDIA storage (local disk in dev, S3 in
    # prod). The async worker reads bytes from here instead of receiving them
    # through the broker, so large uploads don't bloat Redis or memory.
    media_file = models.FileField(upload_to="ingestion/%Y/%m/", null=True, blank=True)
    # SHA-256 of the uploaded bytes — an idempotency signal so re-uploading the
    # same file for the same source can be detected (flagged, not blocked).
    content_hash = models.CharField(max_length=64, blank=True, db_index=True)
    received_at = models.DateTimeField(auto_now_add=True)
    row_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)


class RawRecord(TenantScopedModel):
    """One source row, stored exactly as received plus its parse outcome.

    `payload` is the untouched source row (dict of original columns). If
    parsing/normalization fails, `error` explains why and the analyst sees it
    in the review dashboard instead of the row vanishing.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        NORMALIZED = "normalized", "Normalized"
        FAILED = "failed", "Failed"

    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name="raw_records")
    row_number = models.PositiveIntegerField()
    payload = models.JSONField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    error = models.TextField(blank=True)

    class Meta:
        unique_together = ("batch", "row_number")
