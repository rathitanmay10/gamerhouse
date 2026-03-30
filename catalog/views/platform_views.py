from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from catalog.models import Platform
from catalog.serializers import PlatformSerializer
from core.decorators import drf_cache_response, drf_invalidate_cache
from core.permissions import IsSuperAdminOrReadOnly


class PlatformViewSet(ModelViewSet):
    """
    API endpoints for managing platforms.

    Read access is open to all admins.
    Write access is restricted to super admin.
    """

    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    @drf_cache_response(prefix="platforms:list")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @drf_cache_response(prefix="platforms:detail")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @drf_invalidate_cache(pattern="cache:platforms*")
    def perform_create(self, serializer):
        return super().perform_create(serializer)

    @drf_invalidate_cache(pattern="cache:platforms*")
    def perform_update(self, serializer):
        return super().perform_update(serializer)

    @drf_invalidate_cache(pattern="cache:platforms*")
    def perform_destroy(self, instance):
        return super().perform_destroy(instance)
