"""Turns a NormalizedRow into an ActivityRecord with computed CO2e.

Factor resolution is by category, preferring the row's region and reporting
year, falling back to the latest available factor. If no factor matches, the
record is created with co2e=None and emission_factor=None — it is NOT dropped;
the anomaly service flags it as `missing_factor` so an analyst sees it in the
review queue. The factor actually used is pinned on the record for audit.
"""
from apps.emissions.models import ActivityRecord
from apps.reference.models import EmissionFactor


def resolve_factor(activity_category, activity_date, region=""):
    qs = EmissionFactor.objects.filter(activity_category=activity_category)
    if not qs.exists():
        return None
    # Prefer exact region, then blank/global region.
    region_qs = qs.filter(region=region) if region else qs.filter(region="")
    qs = region_qs if region_qs.exists() else qs
    # Prefer the reporting year, else the most recent factor.
    year_match = qs.filter(valid_year=activity_date.year).first()
    return year_match or qs.order_by("-valid_year").first()


def _co2e(quantity, factor):
    return quantity * factor.co2e_per_unit if factor else None


def build_activity_record(nr, batch, raw_record, organization) -> ActivityRecord:
    factor = resolve_factor(nr.activity_category, nr.activity_date)
    return ActivityRecord.objects.create(
        organization=organization,
        raw_record=raw_record,
        batch=batch,
        activity_category=nr.activity_category,
        scope=nr.scope,
        site_code=nr.site_code,
        activity_date=nr.activity_date,
        period_start=nr.period_start,
        period_end=nr.period_end,
        unit=nr.unit,
        original_quantity=nr.quantity,
        quantity=nr.quantity,
        emission_factor=factor,
        co2e_kg=_co2e(nr.quantity, factor),
    )


def recalculate(record) -> None:
    """Recompute co2e after an analyst edits the quantity."""
    factor = record.emission_factor or resolve_factor(
        record.activity_category, record.activity_date
    )
    record.emission_factor = factor
    record.co2e_kg = _co2e(record.quantity, factor)
