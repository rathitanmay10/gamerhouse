from rest_framework.routers import DefaultRouter

from tenant_games.views import TenantGameViewSet

router = DefaultRouter()
router.register(r"tenant_games", TenantGameViewSet, basename="tenant_game")

urlpatterns = router.urls
