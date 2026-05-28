"""Rule-based anomaly detection at ingest."""
from datetime import date

import pytest

from apps.ingestion.adapters.base import NormalizedRow
from apps.review.models import AnomalyFlag
from apps.review.services.anomaly import evaluate

pytestmark = pytest.mark.django_db


def _row(**kw):
    base = dict(activity_category="diesel", scope="1", quantity=100, unit="L",
                activity_date=date(2025, 3, 15))
    base.update(kw)
    return NormalizedRow(**base)


def test_missing_factor_flag(make_activity, sap_source):
    activity = make_activity(sap_source, factor=None)  # no factor attached
    kinds = {f.kind for f in evaluate(activity, activity.raw_record, _row())}
    assert AnomalyFlag.Kind.MISSING_FACTOR in kinds


def test_invalid_value_flag_for_nonpositive(make_activity, sap_source):
    activity = make_activity(sap_source, quantity="-5")
    kinds = {f.kind for f in evaluate(activity, activity.raw_record, _row())}
    assert AnomalyFlag.Kind.INVALID_VALUE in kinds


def test_unmapped_plant_code_flag(make_activity, sap_source):
    activity = make_activity(sap_source, site_code="9999")  # no PlantCode mapping
    kinds = {f.kind for f in evaluate(activity, activity.raw_record, _row())}
    assert AnomalyFlag.Kind.UNMAPPED_CODE in kinds


def test_duplicate_flag(make_activity, sap_source):
    make_activity(sap_source, quantity="100", site_code="1010", activity_date=date(2025, 3, 15))
    dup = make_activity(sap_source, quantity="100", site_code="1010", activity_date=date(2025, 3, 15))
    kinds = {f.kind for f in evaluate(dup, dup.raw_record, _row())}
    assert AnomalyFlag.Kind.DUPLICATE in kinds
