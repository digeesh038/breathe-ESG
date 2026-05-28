import csv
import io
from datetime import date

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.audit.services import record_event
from apps.common.viewsets import TenantViewSetMixin
from apps.review.models import AnomalyFlag, ReviewItem

from .models import ActivityRecord
from .serializers import ActivityDetailSerializer, ActivityRecordSerializer, _quality_score
from .services.calculator import recalculate


def _f(value):
    return float(value or 0)


class ActivityRecordViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """Normalized records. Editing `quantity` re-runs the calculator, marks the
    row edited, and writes an audit event. Locked/rejected rows are read-only."""

    filterset_fields = ["scope", "activity_category", "batch", "site_code"]

    def get_serializer_class(self):
        # Detail view carries the source history (raw record); lists stay lean.
        if self.action == "retrieve":
            return ActivityDetailSerializer
        return ActivityRecordSerializer

    def get_queryset(self):
        return ActivityRecord.objects.filter(organization=self.organization)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Dashboard figures, computed server-side.

        Rejected records are excluded from the inventory totals — they are not
        part of reported emissions. We also expose the audit-ready (locked)
        total so the analyst sees how much has been signed off, plus a monthly
        time series for the trend chart.
        """
        org = self.organization
        inventory = ActivityRecord.objects.filter(organization=org).exclude(
            review__status=ReviewItem.Status.REJECTED
        )

        by_scope = []
        for scope in ("1", "2", "3"):
            rows = inventory.filter(scope=scope)
            by_scope.append({
                "scope": scope,
                "co2e": _f(rows.aggregate(s=Sum("co2e_kg"))["s"]),
                "count": rows.count(),
            })

        # Monthly trend: bucket by activity_date so the chart aligns with the
        # period the emission happened in, not when it was uploaded.
        monthly = (
            inventory.annotate(month=TruncMonth("activity_date"))
            .values("month", "scope")
            .annotate(co2e=Sum("co2e_kg"))
            .order_by("month", "scope")
        )
        # Re-shape into one row per month, scope columns side-by-side, which is
        # what Recharts wants for a stacked / grouped bar chart.
        buckets = {}
        for row in monthly:
            if not row["month"]:
                continue
            key = row["month"].strftime("%Y-%m")
            buckets.setdefault(key, {"month": key, "s1": 0, "s2": 0, "s3": 0})
            buckets[key][f"s{row['scope']}"] = _f(row["co2e"])
        trend = sorted(buckets.values(), key=lambda r: r["month"])

        locked = inventory.filter(review__status=ReviewItem.Status.LOCKED)
        review_counts = {
            status: ReviewItem.objects.filter(organization=org, status=status).count()
            for status in ("pending", "locked", "rejected")
        }
        open_anomalies = AnomalyFlag.objects.filter(
            organization=org, review_item__status=ReviewItem.Status.PENDING, resolved=False
        ).count()

        # Top sites by emissions — useful in the dashboard side-panel.
        top_sites = list(
            inventory.exclude(site_code="")
            .values("site_code")
            .annotate(co2e=Sum("co2e_kg"), count=Count("id"))
            .order_by("-co2e")[:5]
        )
        for row in top_sites:
            row["co2e"] = _f(row["co2e"])

        return Response({
            "total_co2e": _f(inventory.aggregate(s=Sum("co2e_kg"))["s"]),
            "locked_co2e": _f(locked.aggregate(s=Sum("co2e_kg"))["s"]),
            "record_count": inventory.count(),
            "by_scope": by_scope,
            "trend": trend,
            "top_sites": top_sites,
            "review": review_counts,
            "open_anomalies": open_anomalies,
        })

    @action(detail=False, methods=["get"])
    def export(self, request):
        """Stream the (filtered) record set as CSV or XLSX for auditor handoff.

        Driven by `?format=csv|xlsx`. Applies the same filters as the list
        endpoint so an analyst can export exactly what they see.
        """
        fmt = request.query_params.get("format", "csv").lower()
        qs = self.filter_queryset(self.get_queryset()).select_related(
            "emission_factor", "review"
        ).prefetch_related("review__flags")

        columns = [
            "id", "activity_category", "scope", "site_code", "activity_date",
            "unit", "quantity", "co2e_kg", "data_quality_score", "review_status",
        ]

        def rows():
            for r in qs:
                yield [
                    r.id,
                    r.activity_category,
                    r.scope,
                    r.site_code,
                    r.activity_date.isoformat() if r.activity_date else "",
                    r.unit,
                    str(r.quantity),
                    str(r.co2e_kg or ""),
                    _quality_score(r),
                    getattr(getattr(r, "review", None), "status", ""),
                ]

        filename = f"emissions_{date.today().isoformat()}"

        if fmt == "xlsx":
            from openpyxl import Workbook  # lazy import — only loaded on export
            wb = Workbook()
            ws = wb.active
            ws.title = "emissions"
            ws.append(columns)
            for row in rows():
                ws.append(row)
            buf = io.BytesIO()
            wb.save(buf)
            response = HttpResponse(
                buf.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
            return response

        # default: CSV
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(columns)
        writer.writerows(rows())
        response = HttpResponse(buf.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
        return response

    def perform_update(self, serializer):
        instance = serializer.instance
        review_status = getattr(getattr(instance, "review", None), "status", None)
        if review_status in ("locked", "rejected"):
            raise PermissionDenied(f"Record is {review_status} and can no longer be edited.")

        before = instance.quantity
        record = serializer.save()
        if record.quantity != before:
            record.is_edited = True
            recalculate(record)
            record.save(update_fields=["quantity", "is_edited", "co2e_kg", "emission_factor"])
            record_event(
                organization=self.organization,
                actor=self.request.user,
                action="edited",
                target=record,
                changes={"quantity": [str(before), str(record.quantity)]},
            )

    def perform_destroy(self, instance):
        # Locked records are audit-final and must never be deleted. Everything
        # else can be removed by an analyst/admin (cascades its review + flags);
        # we log the deletion to the immutable audit trail first.
        review_status = getattr(getattr(instance, "review", None), "status", None)
        if review_status == "locked":
            raise PermissionDenied("Locked records are audit-final and cannot be deleted.")
        record_event(
            organization=self.organization,
            actor=self.request.user,
            action="deleted",
            target=instance,
            changes={
                "activity_category": instance.activity_category,
                "quantity": str(instance.quantity),
                "co2e_kg": str(instance.co2e_kg or ""),
            },
        )
        instance.delete()
