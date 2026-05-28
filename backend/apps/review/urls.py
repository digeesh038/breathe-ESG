from rest_framework.routers import DefaultRouter

from .views import ReviewItemViewSet

router = DefaultRouter()
router.register("items", ReviewItemViewSet, basename="review-item")

urlpatterns = router.urls
