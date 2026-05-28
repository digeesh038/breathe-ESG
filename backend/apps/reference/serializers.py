from rest_framework import serializers

from .models import AirportCode, EmissionFactor, PlantCode


class EmissionFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionFactor
        fields = "__all__"


class PlantCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantCode
        fields = "__all__"


class AirportCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirportCode
        fields = "__all__"
