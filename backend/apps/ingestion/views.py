from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.common.throttling import UploadThrottle
from apps.common.viewsets import TenantViewSetMixin

from .models import IngestionBatch, RawRecord, SourceConnection
from .serializers import (
    BatchUploadSerializer,
    IngestionBatchSerializer,
    RawRecordSerializer,
    SourceConnectionSerializer,
)
from .services.pipeline import run_batch_from_storage
from .tasks import run_batch_task


class SourceConnectionViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SourceConnectionSerializer
    # Configuring data sources is an admin responsibility, not an analyst one.
    write_roles = {"admin"}

    def get_queryset(self):
        return SourceConnection.objects.filter(organization=self.organization)


class IngestionBatchViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    serializer_class = IngestionBatchSerializer
    filterset_fields = ["status", "source"]

    def get_queryset(self):
        return (
            IngestionBatch.objects.filter(organization=self.organization)
            .select_related("source")
            .order_by("-received_at")
        )

    @action(
        detail=False,
        methods=["post"],
        serializer_class=BatchUploadSerializer,
        parser_classes=[MultiPartParser, FormParser],
        throttle_classes=[UploadThrottle],
    )
    def upload(self, request):
        """Persist the upload to storage and dispatch the pipeline.

        The file is saved to the batch's `media_file` (local disk in dev, S3 in
        prod) so the worker reads it from storage rather than receiving bytes
        through the broker. Behavior depends on `CELERY_TASK_ALWAYS_EAGER`:
        eager (dev/tests) runs inline; async (prod) enqueues a Celery task.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source = serializer.validated_data["source"]
        upload = serializer.validated_data["file"]

        if source.organization_id != self.organization.id:
            return Response(
                {"detail": "Source does not belong to this organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Idempotency signal: hash the bytes, then rewind so media_file saves
        # the full content. A prior batch with the same source+hash means this
        # is a re-upload — we note it rather than block (the analyst decides).
        import hashlib

        raw_bytes = upload.read()
        content_hash = hashlib.sha256(raw_bytes).hexdigest()
        upload.seek(0)
        duplicate_of = (
            IngestionBatch.objects.filter(
                organization=self.organization, source=source, content_hash=content_hash
            )
            .order_by("id")
            .first()
        )

        batch = IngestionBatch.objects.create(
            organization=self.organization,
            source=source,
            created_by=request.user,
            original_filename=upload.name,
            media_file=upload,  # saved to MEDIA storage here
            content_hash=content_hash,
            notes=(
                f"Possible re-upload of batch #{duplicate_of.id} (identical file)."
                if duplicate_of else ""
            ),
        )

        from django.conf import settings

        if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
            run_batch_from_storage(batch)
            batch.refresh_from_db()
        else:
            run_batch_task.delay(batch.id)

        return Response(
            IngestionBatchSerializer(batch).data, status=status.HTTP_201_CREATED
        )


class RawRecordViewSet(TenantViewSetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = RawRecordSerializer
    filterset_fields = ["batch", "status"]

    def get_queryset(self):
        return RawRecord.objects.filter(organization=self.organization).order_by("row_number")
