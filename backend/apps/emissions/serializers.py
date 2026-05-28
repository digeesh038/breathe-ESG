from rest_framework import serializers

from .models import ActivityRecord

# Data-quality scoring: each unresolved anomaly flag deducts from a perfect 1.0.
# Heavier weights for flags that mean the row's *value* is wrong; lighter for
# context-only flags (e.g. unit was inferred but the value is plausible).
FLAG_WEIGHTS = {
    "invalid_value": 0.5,
    "missing_factor": 0.3,
    "implausible": 0.3,
    "outlier": 0.2,
    "duplicate": 0.2,
    "unit_guess": 0.1,
    "unmapped_code": 0.1,
}


def _quality_score(record):
    """1.0 = clean, 0.0 = worst. Resolved flags don't count against the row.

    Computed from the review item's flags so the score stays in sync with
    whatever anomaly rules the review service emits.
    """
    review = getattr(record, "review", None)
    if review is None:
        return 1.0
    deductions = sum(
        FLAG_WEIGHTS.get(f.kind, 0.1)
        for f in review.flags.all()
        if not f.resolved
    )
    return round(max(0.0, 1.0 - deductions), 2)


class ActivityRecordSerializer(serializers.ModelSerializer):
    """Lean serializer for lists and the review queue."""

    factor = serializers.SerializerMethodField()
    data_quality_score = serializers.SerializerMethodField()

    class Meta:
        model = ActivityRecord
        fields = [
            "id", "batch", "raw_record", "activity_category", "scope",
            "site_code", "activity_date", "period_start", "period_end",
            "unit", "original_quantity", "quantity", "is_edited",
            "emission_factor", "factor", "co2e_kg", "data_quality_score",
            "created_at", "updated_at",
        ]
        read_only_fields = ["co2e_kg", "original_quantity", "raw_record", "batch", "is_edited"]

    def get_factor(self, obj):
        f = obj.emission_factor
        if f is None:
            return None
        return {"source": f.source, "co2e_per_unit": str(f.co2e_per_unit),
                "unit": f.unit, "valid_year": f.valid_year, "region": f.region}

    def get_data_quality_score(self, obj):
        return _quality_score(obj)


class ActivityDetailSerializer(ActivityRecordSerializer):
    """Adds source history — the verbatim raw record + its batch — for drilldown."""

    raw = serializers.SerializerMethodField()

    class Meta(ActivityRecordSerializer.Meta):
        fields = ActivityRecordSerializer.Meta.fields + ["raw"]

    def get_raw(self, obj):
        raw = obj.raw_record
        return {
            "row_number": raw.row_number,
            "status": raw.status,
            "error": raw.error,
            "payload": raw.payload,
            "batch": {
                "id": raw.batch_id,
                "filename": raw.batch.original_filename,
                "source_type": raw.batch.source.source_type,
                "received_at": raw.batch.received_at,
            },
        }
