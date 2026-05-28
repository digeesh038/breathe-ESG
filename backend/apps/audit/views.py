from rest_framework import viewsets

from apps.common.viewsets import TenantViewSetMixin

from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventViewSet(TenantViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only by design — the audit log is append-only and never edited."""

    serializer_class = AuditEventSerializer
    filterset_fields = ["action", "target_model", "actor"]

    def get_queryset(self):
        return AuditEvent.objects.filter(organization=self.organization)
