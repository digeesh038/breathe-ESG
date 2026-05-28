import os

from django.conf import settings
from rest_framework import serializers

from .models import IngestionBatch, RawRecord, SourceConnection


class SourceConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceConnection
        fields = ["id", "name", "source_type", "config", "created_at"]


class IngestionBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionBatch
        fields = [
            "id", "source", "status", "original_filename",
            "received_at", "row_count", "error_count", "notes",
        ]
        read_only_fields = ["status", "row_count", "error_count", "received_at"]


def validate_upload_file(upload):
    """Reject oversized files and unexpected extensions before any processing."""
    max_bytes = settings.MAX_UPLOAD_BYTES
    if upload.size > max_bytes:
        raise serializers.ValidationError(
            f"File is {upload.size} bytes; the limit is {max_bytes} bytes "
            f"({max_bytes // (1024 * 1024)} MB)."
        )
    ext = os.path.splitext(upload.name)[1].lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
        raise serializers.ValidationError(
            f"Unsupported file type '{ext}'. Allowed: {allowed}."
        )
    return upload


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ["id", "batch", "row_number", "payload", "status", "error"]


class BatchUploadSerializer(serializers.Serializer):
    """Multipart upload: a file + the source connection it belongs to."""

    source = serializers.PrimaryKeyRelatedField(queryset=SourceConnection.objects.all())
    file = serializers.FileField(validators=[validate_upload_file])
