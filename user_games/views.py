from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet

from core.enums import Roles
from core.permissions import IsAdminReadOnlyOrOwner
from user_games.filters import UserGameQueryFilter
from user_games.models import UserGame, UserGameNote
from user_games.serializers import UserGameNoteSerializer, UserGameSerializer


class UserGameViewSet(ModelViewSet):
    """
    User Games API

    Admin:
    - GET only

    Gamer:
    - GET, POST, PATCH, DELETE
    - Only their own games
    """

    permission_classes = [IsAdminReadOnlyOrOwner]
    serializer_class = UserGameSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user

        if user.role == Roles.ADMIN:
            qs = UserGame.objects.all()
        else:
            qs = UserGame.objects.filter(user=user)

        return UserGameQueryFilter(qs, self.request.query_params).apply()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserGameNoteViewSet(ModelViewSet):
    permission_classes = [IsAdminReadOnlyOrOwner]
    serializer_class = UserGameNoteSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user_game_id = self.kwargs.get("user_game_id")
        return UserGameNote.objects.filter(user_game_id=user_game_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user_game_id = self.kwargs.get("user_game_id")
        try:
            user_game = UserGame.objects.get(id=user_game_id)
        except UserGame.DoesNotExist:
            raise PermissionDenied("UserGame not found.")
        context["user_game"] = user_game
        return context

    def perform_create(self, serializer):
        serializer.save()
