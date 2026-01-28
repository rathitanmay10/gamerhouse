from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet

from core.enums import Roles
from user_games.filters import UserGameFilter
from user_games.models import UserGame, UserGameNote
from user_games.permissions import IsTenantAdminOrGamer, UserGameNotePermission
from user_games.serializers import UserGameNoteSerializer, UserGameSerializer


class UserGameViewSet(ModelViewSet):
    """
    User Games API

    Gamers:
        - GET, POST, PATCH, DELETE
        - Only their own games

    Admins:
        - GET, POST, PATCH, DELETE
        - Can manage games for any user in their tenant
    """

    permission_classes = [IsTenantAdminOrGamer]
    serializer_class = UserGameSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserGameFilter

    def get_queryset(self):
        user = self.request.user
        qs = (
            UserGame.objects.filter(tenant=user.tenant)
            .select_related("tenant_game__game")
            .prefetch_related("tenant_game__game__platforms")
        )
        if user.role == Roles.GAMER:
            qs = qs.filter(user=user)
        return qs


class UserGameNoteViewSet(ModelViewSet):
    permission_classes = [UserGameNotePermission]
    serializer_class = UserGameNoteSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_user_game(self):
        """Get and cache the UserGame object with permission checks."""
        if not hasattr(self, "_user_game"):
            user = self.request.user
            user_game_id = self.kwargs.get("user_game_id")
            try:
                user_game = UserGame.objects.get(id=user_game_id, tenant=user.tenant)
            except UserGame.DoesNotExist:
                raise PermissionDenied("UserGame not found.")

            if user.role == Roles.GAMER and user_game.user != user:
                raise PermissionDenied(
                    "You do not have permission to access this resource."
                )
            self._user_game = user_game
        return self._user_game

    def get_queryset(self):
        user_game = self.get_user_game()
        return UserGameNote.objects.filter(user_game=user_game)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user_game"] = self.get_user_game()
        return context
