from rest_framework import viewsets

from apps.common.viewsets import TenantViewSetMixin

from .models import AirportCode, EmissionFactor, PlantCode
from .serializers import (
    AirportCodeSerializer,
    EmissionFactorSerializer,
    PlantCodeSerializer,
)


class EmissionFactorViewSet(viewsets.ReadOnlyModelViewSet):
    """Global reference data — not tenant-scoped (public factor datasets)."""

    queryset = EmissionFactor.objects.all()
    serializer_class = EmissionFactorSerializer
    filterset_fields = ["activity_category", "scope", "valid_year", "region"]


class PlantCodeViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    serializer_class = PlantCodeSerializer

    def get_queryset(self):
        return PlantCode.objects.filter(organization=self.organization)


class AirportCodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AirportCode.objects.all()
    serializer_class = AirportCodeSerializer
