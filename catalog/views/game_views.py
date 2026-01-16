from rest_framework.viewsets import ModelViewSet

from catalog.models import Game
from catalog.serializers import GameSerializer
from core.permissions import IsAdminOrReadOnly


class GameViewSet(ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
