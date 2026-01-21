from rest_framework.routers import DefaultRouter

from tenants.views import TenantViewSet

router = DefaultRouter()
router.register("tenants", TenantViewSet, basename="tenant")

urlpatterns = router.urls
