from rest_framework.viewsets import ModelViewSet

from core.enums import Roles
from core.permissions import IsAdminReadOnlyOrOwner
from games.filters import GameQueryFilter
from games.models import Game
from games.serializers import GameSerializer


class GameViewSet(ModelViewSet):
    """
    Games API

    Admin:
    - GET only
    - Can see all non-deleted games

    Gamer:
    - GET, POST, PATCH, DELETE
    - Only their own games
    """

    permission_classes = [IsAdminReadOnlyOrOwner]
    serializer_class = GameSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user

        if user.role == Roles.ADMIN:
            qs = Game.objects.all()
        else:
            qs = Game.objects.filter(user=user)

        return GameQueryFilter(qs, self.request.query_params).apply()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
