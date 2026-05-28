"""Background tasks for the ingestion pipeline.

The pipeline itself stays in `services.pipeline` so it can be called both sync
(small files, tests) and async (large enterprise uploads). The Celery task
looks up the batch and runs the pipeline against the file in storage — bytes
never travel through the broker.
"""
import logging

from celery import shared_task

from .models import IngestionBatch
from .services.pipeline import run_batch_from_storage

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def run_batch_task(self, batch_id: int) -> dict:
    """Run the pipeline for a single batch, reading its file from storage.

    Retries cover transient broker / DB blips; the pipeline is
    `@transaction.atomic` so a retry doesn't double-write.
    """
    try:
        batch = IngestionBatch.objects.get(pk=batch_id)
    except IngestionBatch.DoesNotExist as exc:
        logger.error("run_batch_task: batch %s not found", batch_id)
        raise self.retry(exc=exc)

    run_batch_from_storage(batch)
    batch.refresh_from_db()
    return {
        "batch_id": batch.id,
        "status": batch.status,
        "rows": batch.row_count,
        "errors": batch.error_count,
    }
