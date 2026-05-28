from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.services import record_event
from apps.common.viewsets import TenantViewSetMixin

from .models import ReviewItem
from .serializers import ReviewItemSerializer


class ReviewItemViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """The review dashboard's main endpoint.

    Filter by status / scope / batch to triage. approve and reject are explicit
    actions that stamp the reviewer, write an audit event, and (on approve) lock
    the row for audit.
    """

    serializer_class = ReviewItemSerializer
    filterset_fields = ["status", "activity__scope", "activity__batch"]

    def get_queryset(self):
        return (
            ReviewItem.objects.filter(organization=self.organization)
            .select_related("activity")
            .prefetch_related("flags")
            .order_by("-id")
        )

    def _transition(self, request, new_status, action_label):
        item = self.get_object()
        item.status = new_status
        item.reviewed_by = request.user
        item.reviewed_at = timezone.now()
        item.comment = request.data.get("comment", item.comment)
        item.save(update_fields=["status", "reviewed_by", "reviewed_at", "comment"])
        record_event(
            organization=self.organization,
            actor=request.user,
            action=action_label,
            target=item.activity,
            changes={"review_status": new_status},
        )
        return Response(self.get_serializer(item).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        # Approval locks the underlying record for audit.
        return self._transition(request, ReviewItem.Status.LOCKED, "locked")

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._transition(request, ReviewItem.Status.REJECTED, "rejected")
