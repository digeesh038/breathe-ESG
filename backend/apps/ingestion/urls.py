from rest_framework.routers import DefaultRouter

from .views import IngestionBatchViewSet, RawRecordViewSet, SourceConnectionViewSet

router = DefaultRouter()
router.register("sources", SourceConnectionViewSet, basename="source")
router.register("batches", IngestionBatchViewSet, basename="batch")
router.register("raw-records", RawRecordViewSet, basename="raw-record")

urlpatterns = router.urls
