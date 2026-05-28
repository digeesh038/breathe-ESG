from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = [
            "id", "actor", "action", "target_model", "target_id",
            "changes", "occurred_at",
        ]
