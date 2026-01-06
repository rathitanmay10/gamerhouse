from rest_framework.routers import DefaultRouter

from games.views import GameViewSet

router = DefaultRouter()
router.register("games", GameViewSet, basename="games")

urlpatterns = router.urls
