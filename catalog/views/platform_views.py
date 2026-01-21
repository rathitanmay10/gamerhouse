from rest_framework.viewsets import ModelViewSet

from catalog.models import Platform
from catalog.serializers import PlatformSerializer
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
