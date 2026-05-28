from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ActivityRecordViewSet

router = DefaultRouter()
router.register("activities", ActivityRecordViewSet, basename="activity")

urlpatterns = [
    path("act_xport/", ActivityRecordViewSet.as_view({"get": "export"}), name="activity-export-custom"),
] + router.urls
