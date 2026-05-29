"""Orchestrates ingestion: file bytes -> RawRecords -> ActivityRecords + review.

One bad row never kills the batch — parse failures fail the whole batch (the
file is unreadable), but per-row normalization errors mark just that RawRecord
FAILED with the reason, which the analyst sees in the dashboard.
"""
import logging

from django.conf import settings
from django.db import transaction

from apps.audit.services import record_event
from apps.common.exceptions import IngestionError
from apps.emissions.services.calculator import build_activity_record
from apps.ingestion.adapters.sap import SAPAdapter
from apps.ingestion.adapters.travel import TravelAdapter
from apps.ingestion.adapters.utility import UtilityAdapter
from apps.ingestion.models import IngestionBatch, RawRecord
from apps.review.models import AnomalyFlag, ReviewItem
from apps.review.services.anomaly import evaluate

logger = logging.getLogger("apps.ingestion")

ADAPTERS = {
    "sap": SAPAdapter,
    "utility": UtilityAdapter,
    "travel": TravelAdapter,
}


def run_batch_from_storage(batch: IngestionBatch) -> IngestionBatch:
    """Read the persisted upload from storage and run the pipeline.

    This is the single entrypoint used by both the sync (eager) view path and
    the Celery worker, so bytes never travel through the broker.
    """
    if not batch.media_file:
        batch.status = IngestionBatch.Status.FAILED
        batch.notes = "No file attached to batch."
        batch.save(update_fields=["status", "notes"])
        return batch
    batch.media_file.open("rb")
    try:
        raw_bytes = batch.media_file.read()
    finally:
        batch.media_file.close()
    return run_batch(batch, raw_bytes)


@transaction.atomic
def run_batch(batch: IngestionBatch, raw_bytes: bytes) -> IngestionBatch:
    adapter = ADAPTERS[batch.source.source_type]()
    config = batch.source.config or {}

    # 1. Parse + store every row verbatim. A parse failure fails the batch.
    try:
        parsed = list(adapter.parse(raw_bytes, config))
    except Exception as exc:  # malformed file
        batch.status = IngestionBatch.Status.FAILED
        batch.notes = f"Parse error: {exc}"
        batch.save(update_fields=["status", "notes"])
        return batch

    # Cap rows so a pathological file can't exhaust memory / DB.
    max_rows = getattr(settings, "MAX_UPLOAD_ROWS", 100_000)
    if len(parsed) > max_rows:
        batch.status = IngestionBatch.Status.FAILED
        batch.notes = f"File has {len(parsed)} rows; the limit is {max_rows}."
        batch.save(update_fields=["status", "notes"])
        return batch

    RawRecord.objects.bulk_create(
        [
            RawRecord(organization=batch.organization, batch=batch, row_number=n, payload=payload)
            for n, payload in parsed
        ]
    )

    # 2. Normalize each stored row -> ActivityRecord + ReviewItem + flags.
    # A single bad row must never kill the batch. Each row runs in its own
    # savepoint so partial writes roll back cleanly, and any failure marks just
    # that RawRecord FAILED. We catch broadly (not only IngestionError) because
    # a wrong-format file makes adapters raise KeyError/ValueError/etc. — that's
    # bad data, not a server bug, so it should fail the row, not 500 the batch.
    error_count = 0
    for raw in batch.raw_records.order_by("row_number"):
        try:
            with transaction.atomic():
                normalized = adapter.normalize(raw.payload, config)
                activity = build_activity_record(normalized, batch, raw, batch.organization)
                raw.status = RawRecord.Status.NORMALIZED
                raw.save(update_fields=["status"])

                review_item = ReviewItem.objects.create(
                    organization=batch.organization, activity=activity
                )
                flags = evaluate(activity, raw, normalized)
                for f in flags:
                    f.organization = batch.organization
                    f.review_item = review_item
                AnomalyFlag.objects.bulk_create(flags)

                # Provenance: record where this normalized row came from.
                record_event(
                    organization=batch.organization,
                    actor=batch.created_by,
                    action="created",
                    target=activity,
                    changes={"source": batch.source.source_type, "batch": batch.id, "row": raw.row_number},
                )
        except Exception as exc:  # noqa: BLE001 — bad data fails the row, not the batch
            logger.warning("Batch %s row %s failed to normalize: %s", batch.id, raw.row_number, exc)
            raw.status = RawRecord.Status.FAILED
            raw.error = str(exc) if isinstance(exc, IngestionError) else f"{type(exc).__name__}: {exc}"
            raw.save(update_fields=["status", "error"])
            error_count += 1

    # 3. Summarize the batch.
    batch.row_count = batch.raw_records.count()
    batch.error_count = error_count
    batch.status = (
        IngestionBatch.Status.FAILED
        if error_count and error_count == batch.row_count
        else IngestionBatch.Status.NORMALIZED
    )
    batch.save(update_fields=["row_count", "error_count", "status"])
    return batch
