from rest_framework.viewsets import ModelViewSet
from catalog.serializers.genre import GenreSerializer
from catalog.models import Genre
from core.permissions import IsAdminOrReadOnly


class GenreViewSet(ModelViewSet):
    """
    API endpoints for managing genres.

    Read access is open to all users.
    Write access is restricted to admin users.
    """

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = ["get", "post", "patch", "head", "options"]
