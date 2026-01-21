from rest_framework.viewsets import ModelViewSet

from catalog.models import Game
from catalog.serializers import GameSerializer
from core.permissions import IsSuperAdminOrAdminReadOnly


class GameViewSet(ModelViewSet):
    """
    API endpoints for managing games.

    Read access is open to all admins.
    Write access is restricted to super admin.
    """

    serializer_class = GameSerializer
    permission_classes = [IsSuperAdminOrAdminReadOnly]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Game.objects.select_related("genre").prefetch_related("platforms")
