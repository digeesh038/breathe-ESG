"""Anomaly detection that populates AnomalyFlags at ingest time.

Deliberately rule-based and explainable for a prototype — analysts must trust
*why* a row is flagged, so every flag carries a human-readable detail. Returns
unsaved AnomalyFlag instances; the pipeline attaches them to the ReviewItem.

Adapters can also pre-compute hints (e.g. an implausible flight distance) and
stash them on NormalizedRow.extra; we surface those here so the source-specific
knowledge lives in the adapter while the flagging stays uniform.
"""
from decimal import Decimal
from statistics import mean

from apps.emissions.models import ActivityRecord
from apps.reference.models import PlantCode

from ..models import AnomalyFlag

# Soft per-unit caps used when there isn't enough history for a statistical test.
_ABSOLUTE_CAPS = {"L": Decimal("10000"), "kWh": Decimal("30000")}
_OUTLIER_MULTIPLE = Decimal("3")


def evaluate(activity, raw_record, normalized_row) -> list[AnomalyFlag]:
    flags: list[AnomalyFlag] = []

    def flag(kind, detail):
        flags.append(AnomalyFlag(kind=kind, detail=detail))

    extra = normalized_row.extra or {}

    # 1. No emission factor matched -> can't compute CO2e.
    if activity.emission_factor_id is None:
        flag(AnomalyFlag.Kind.MISSING_FACTOR,
             f"No emission factor for '{activity.activity_category}'.")

    # 2. Invalid quantity (negative / zero).
    if activity.quantity <= 0:
        flag(AnomalyFlag.Kind.INVALID_VALUE,
             f"Quantity is {activity.quantity} {activity.unit} (must be positive).")

    # 3. Adapter-detected implausibility (e.g. given flight distance vs estimate).
    if extra.get("implausible"):
        flag(AnomalyFlag.Kind.IMPLAUSIBLE, extra["implausible"])

    # 4. Billing period that ends before it starts / spans an absurd range.
    if activity.period_start and activity.period_end:
        days = (activity.period_end - activity.period_start).days
        if days < 0:
            flag(AnomalyFlag.Kind.IMPLAUSIBLE, "Billing period ends before it starts.")
        elif days > 120:
            flag(AnomalyFlag.Kind.IMPLAUSIBLE, f"Billing period spans {days} days.")

    # 5. SAP plant code not in the lookup table.
    if activity.batch.source.source_type == "sap" and activity.site_code:
        known = PlantCode.objects.filter(
            organization=activity.organization, code=activity.site_code
        ).exists()
        if not known:
            flag(AnomalyFlag.Kind.UNMAPPED_CODE,
                 f"Plant code '{activity.site_code}' has no site mapping.")

    # 6. Possible duplicate of an existing record.
    dup = (
        ActivityRecord.objects.filter(
            organization=activity.organization,
            activity_category=activity.activity_category,
            site_code=activity.site_code,
            activity_date=activity.activity_date,
            quantity=activity.quantity,
        )
        .exclude(pk=activity.pk)
        .exists()
    )
    if dup:
        flag(AnomalyFlag.Kind.DUPLICATE, "Matches an existing record (site/date/qty).")

    # 7. Outlier: vs same-category history if available, else a soft cap.
    history = list(
        ActivityRecord.objects.filter(
            organization=activity.organization,
            activity_category=activity.activity_category,
        )
        .exclude(pk=activity.pk)
        .values_list("quantity", flat=True)
    )
    if len(history) >= 3:
        avg = Decimal(str(mean(float(q) for q in history)))
        if avg > 0 and activity.quantity > avg * _OUTLIER_MULTIPLE:
            flag(AnomalyFlag.Kind.OUTLIER,
                 f"{activity.quantity} {activity.unit} is >3x the category average ({avg:.0f}).")
    else:
        cap = _ABSOLUTE_CAPS.get(activity.unit)
        if cap and activity.quantity > cap:
            flag(AnomalyFlag.Kind.OUTLIER,
                 f"{activity.quantity} {activity.unit} exceeds the {cap} {activity.unit} review threshold.")

    return flags
