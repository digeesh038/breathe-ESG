from rest_framework import serializers

from apps.emissions.serializers import ActivityRecordSerializer

from .models import AnomalyFlag, ReviewItem


class AnomalyFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnomalyFlag
        fields = ["id", "kind", "detail", "resolved"]


class ReviewItemSerializer(serializers.ModelSerializer):
    flags = AnomalyFlagSerializer(many=True, read_only=True)
    # Nested so the dashboard table has the activity's category/scope/qty/CO2e
    # without a second request per row.
    activity_detail = ActivityRecordSerializer(source="activity", read_only=True)

    class Meta:
        model = ReviewItem
        fields = [
            "id", "activity", "activity_detail", "status",
            "reviewed_by", "reviewed_at", "comment", "flags",
        ]
        read_only_fields = ["reviewed_by", "reviewed_at"]
