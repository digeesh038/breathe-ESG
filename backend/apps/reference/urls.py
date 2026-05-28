from rest_framework.routers import DefaultRouter

from .views import AirportCodeViewSet, EmissionFactorViewSet, PlantCodeViewSet

router = DefaultRouter()
router.register("emission-factors", EmissionFactorViewSet, basename="emission-factor")
router.register("plant-codes", PlantCodeViewSet, basename="plant-code")
router.register("airport-codes", AirportCodeViewSet, basename="airport-code")

urlpatterns = router.urls
