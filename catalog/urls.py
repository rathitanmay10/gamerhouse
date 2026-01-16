from rest_framework.routers import DefaultRouter

from catalog.views import GameViewSet, GenreViewSet, PlatformViewSet

router = DefaultRouter()
router.register("genres", GenreViewSet, basename="genres")
router.register("platforms", PlatformViewSet, basename="platforms")
router.register("games", GameViewSet, basename="games")

urlpatterns = router.urls
