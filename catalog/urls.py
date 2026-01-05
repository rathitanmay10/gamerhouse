from rest_framework.routers import DefaultRouter

from catalog.views.genre import GenreViewSet
from catalog.views.platform import PlatformViewSet

router = DefaultRouter()
router.register("genres", GenreViewSet, basename="genres")
router.register("platforms", PlatformViewSet, basename="platforms")

urlpatterns = router.urls
