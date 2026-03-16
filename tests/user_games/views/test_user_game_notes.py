import pytest
from django.urls import reverse
from rest_framework import status

from tests.factories.user_games import UserGameFactory
from tests.factories.users import UserFactory


class TestUserGameNotesAPI:
    def test_gamer_can_create_note(self, authenticated_client, user, tenant):
        """Verify that a gamer can create a note for their own game."""
        ug = UserGameFactory(user=user, tenant=tenant)
        url = reverse("user-game-notes-list", kwargs={"user_game_id": ug.id})

        data = {"note": "This is a test note"}
        response = authenticated_client.post(url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["note"] == "This is a test note"
        assert ug.notes.count() == 1

    def test_gamer_can_list_notes(self, authenticated_client, user, tenant):
        """Verify that a gamer can list notes for their own game."""
        ug = UserGameFactory(user=user, tenant=tenant)
        from tests.factories.user_games import UserGameNoteFactory

        UserGameNoteFactory(user_game=ug, tenant=tenant, note="Test note 1")
        UserGameNoteFactory(user_game=ug, tenant=tenant, note="Test note 2")

        url = reverse("user-game-notes-list", kwargs={"user_game_id": ug.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 2

    def test_gamer_can_update_note(self, authenticated_client, user, tenant):
        """Verify that a gamer can update an existing note for their own game."""
        ug = UserGameFactory(user=user, tenant=tenant)
        from tests.factories.user_games import UserGameNoteFactory

        note = UserGameNoteFactory(user_game=ug, tenant=tenant, note="Old note")

        url = reverse(
            "user-game-notes-detail",
            kwargs={"user_game_id": str(ug.id), "pk": str(note.id)},
        )
        response = authenticated_client.patch(url, data={"note": "Updated note"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["note"] == "Updated note"
        note.refresh_from_db()
        assert note.note == "Updated note"

    def test_gamer_can_delete_note(self, authenticated_client, user, tenant):
        """Verify that a gamer can delete a note for their own game."""
        ug = UserGameFactory(user=user, tenant=tenant)
        from tests.factories.user_games import UserGameNoteFactory

        note = UserGameNoteFactory(user_game=ug, tenant=tenant, note="Note to delete")

        url = reverse(
            "user-game-notes-detail",
            kwargs={"user_game_id": str(ug.id), "pk": str(note.id)},
        )
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert ug.notes.count() == 0

    def test_gamer_cannot_access_other_users_game_notes(
        self, authenticated_client, tenant
    ):
        """Verify that a gamer cannot access or modify notes for a game they don't own."""
        other_user = UserFactory(tenant=tenant)
        ug_other = UserGameFactory(user=other_user, tenant=tenant)
        url = reverse("user-game-notes-list", kwargs={"user_game_id": str(ug_other.id)})

        response = authenticated_client.get(url)
        # The viewset raises PermissionDenied or NotFound depending on ownership and queryset
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_admin_can_view_tenant_notes(self, admin_client, tenant):
        """Verify that a tenant admin can view notes for games within their tenant."""
        gamer = UserFactory(tenant=tenant)
        ug = UserGameFactory(user=gamer, tenant=tenant)
        from tests.factories.user_games import UserGameNoteFactory

        UserGameNoteFactory(user_game=ug, tenant=tenant, note="Gamer note")

        url = reverse("user-game-notes-list", kwargs={"user_game_id": str(ug.id)})
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 1
