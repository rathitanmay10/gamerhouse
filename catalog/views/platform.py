from rest_framework.viewsets import ModelViewSet
from catalog.serializers.platform import PlatformSerializer
from catalog.models import Platform
from core.permissions import IsAdminOrReadOnly


class PlatformViewSet(ModelViewSet):
    """
    API endpoints for managing platforms.

    Read access is open to all users.
    Write access is restricted to admin users.
    """

    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = ["get", "post", "patch", "head", "options"]
