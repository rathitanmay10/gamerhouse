from rest_framework.viewsets import ModelViewSet

from catalog.models import Genre
from catalog.serializers import GenreSerializer
from core.permissions import IsSuperAdminOrReadOnly


class GenreViewSet(ModelViewSet):
    """
    API endpoints for managing genres.

    Read access is open to all admins.
    Write access is restricted to super admin.
    """

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
