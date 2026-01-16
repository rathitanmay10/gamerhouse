from django.urls import include, path
from rest_framework.routers import DefaultRouter

from user_games.views import UserGameNoteViewSet, UserGameViewSet

router = DefaultRouter()
router.register("user-games", UserGameViewSet, basename="user-game")

notes_urls = [
    path(
        "user-games/<uuid:user_game_id>/notes/",
        UserGameNoteViewSet.as_view({"get": "list", "post": "create"}),
        name="user-game-notes-list",
    ),
    path(
        "user-games/<uuid:user_game_id>/notes/<uuid:pk>/",
        UserGameNoteViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="user-game-notes-detail",
    ),
]

urlpatterns = [
    path("", include(router.urls)),
] + notes_urls
