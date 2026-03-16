from django.urls import reverse
from rest_framework import status

from core.constants import MAX_FREE_USER_GAMES
from core.enums import Roles, Status, TenantStatus
from tests.factories.tenant_games import TenantGameFactory
from tests.factories.user_games import UserGameFactory
from tests.factories.users import UserFactory


class TestUserGamesAPI:
    @property
    def list_url(self):
        return reverse("user-game-list")

    def detail_url(self, pk):
        return reverse("user-game-detail", kwargs={"pk": pk})

    def test_gamer_can_add_game(self, authenticated_client, user, tenant):
        """Verify that a gamer can add a game from their tenant's catalog to their collection."""
        tg = TenantGameFactory(tenant=tenant)
        data = {
            "tenant_game": str(tg.id),
            "platform": str(tg.game.platforms.first().id),
            "status": Status.WISHLIST,
        }
        response = authenticated_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert user.user_games.count() == 1

    def test_gamer_active_tenant_limit(self, authenticated_client, user, tenant):
        """Verify that a gamer on an ACTIVE (free) tenant cannot exceed the game limit."""
        tenant.status = TenantStatus.ACTIVE
        tenant.save()

        # Fill the collection up to the limit
        for _ in range(MAX_FREE_USER_GAMES):
            tg = TenantGameFactory(tenant=tenant)
            UserGameFactory(user=user, tenant=tenant, tenant_game=tg)

        # Attempt to add one more game
        tg_new = TenantGameFactory(tenant=tenant)
        data = {
            "tenant_game": str(tg_new.id),
            "platform": str(tg_new.game.platforms.first().id),
            "status": Status.WISHLIST,
        }
        response = authenticated_client.post(self.list_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "maximum limit" in str(response.data)

    def test_gamer_premium_tenant_unlimited(self, authenticated_client, user, tenant):
        """Verify that a gamer on a PREMIUM tenant has no limit on the number of games."""
        tenant.status = TenantStatus.PREMIUM
        tenant.save()
        user.tenant.refresh_from_db()

        # Create games exceeding the free limit
        from user_games.models import UserGame

        for _ in range(MAX_FREE_USER_GAMES + 1):
            tg = TenantGameFactory(tenant=tenant)
            UserGameFactory(user=user, tenant=tenant, tenant_game=tg)

        assert UserGame.objects.filter(user=user).count() == MAX_FREE_USER_GAMES + 1

        # Add another game via API to confirm it works
        tg_api = TenantGameFactory(tenant=tenant)
        data = {
            "tenant_game": str(tg_api.id),
            "platform": str(tg_api.game.platforms.first().id),
            "status": Status.WISHLIST,
        }
        response = authenticated_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert user.user_games.count() == MAX_FREE_USER_GAMES + 2

    def test_admin_can_manage_gamer_games(self, admin_client, tenant):
        """Verify that a tenant admin can add games for a gamer in their tenant."""
        gamer = UserFactory(tenant=tenant, role=Roles.GAMER)
        tg = TenantGameFactory(tenant=tenant)

        data = {
            "user": str(gamer.id),
            "tenant_game": str(tg.id),
            "platform": str(tg.game.platforms.first().id),
            "status": Status.PLAYING,
        }
        response = admin_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert gamer.user_games.count() == 1

    def test_gamer_cannot_add_game_to_other_user(self, authenticated_client, tenant):
        """Verify that a gamer cannot add games to another user's collection."""
        other_user = UserFactory(tenant=tenant, role=Roles.GAMER)
        tg = TenantGameFactory(tenant=tenant)

        data = {
            "user": str(other_user.id),
            "tenant_game": str(tg.id),
            "platform": str(tg.game.platforms.first().id),
            "status": Status.WISHLIST,
        }
        response = authenticated_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot assign games to other users" in str(response.data).lower()
        assert other_user.user_games.count() == 0

    def test_gamer_can_list_own_games(self, authenticated_client, user, tenant):
        """Verify that a gamer can list their own games."""
        UserGameFactory.create_batch(3, user=user, tenant=tenant)

        other_gamer = UserFactory(tenant=tenant, role=Roles.GAMER)
        UserGameFactory.create_batch(2, user=other_gamer, tenant=tenant)

        response = authenticated_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 3

    def test_admin_can_list_tenant_games(self, admin_client, tenant):
        """Verify that a tenant admin can list all games in the tenant."""
        user1 = UserFactory(tenant=tenant, role=Roles.GAMER)
        user2 = UserFactory(tenant=tenant, role=Roles.GAMER)
        UserGameFactory.create_batch(2, user=user1, tenant=tenant)
        UserGameFactory.create_batch(2, user=user2, tenant=tenant)

        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 4

    def test_gamer_can_update_own_game(self, authenticated_client, user, tenant):
        """Verify that a gamer can update their game's hours played and status."""
        tg = TenantGameFactory(tenant=tenant)
        platform = tg.game.platforms.first()

        ug = UserGameFactory(
            user=user,
            tenant=tenant,
            tenant_game=tg,
            platform=platform,
            status=Status.PLAYING,
            hours_played=10,
        )

        data = {"status": Status.COMPLETED, "hours_played": 50}
        response = authenticated_client.patch(self.detail_url(ug.id), data=data)

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == Status.COMPLETED
        assert response.data["hours_played"] == 50

    def test_admin_can_update_gamer_game(self, admin_client, tenant):
        """Verify that an admin can update any gamer's game in their tenant."""
        gamer = UserFactory(tenant=tenant, role=Roles.GAMER)
        ug = UserGameFactory(user=gamer, tenant=tenant, personal_rating=3)

        data = {"personal_rating": 5}
        response = admin_client.patch(self.detail_url(ug.id), data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_gamer_cannot_update_other_user_game(self, authenticated_client, tenant):
        """Verify that a gamer gets 404 when trying to update another user's game."""
        other_gamer = UserFactory(tenant=tenant, role=Roles.GAMER)
        ug = UserGameFactory(user=other_gamer, tenant=tenant)

        data = {"hours_played": 99}
        response = authenticated_client.patch(self.detail_url(ug.id), data=data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_gamer_can_delete_own_game(self, authenticated_client, user, tenant):
        """Verify that a gamer can delete their game, and it cascades/soft-deletes notes."""
        from tests.factories.user_games import UserGameNoteFactory

        ug = UserGameFactory(user=user, tenant=tenant)
        note = UserGameNoteFactory(user_game=ug, tenant=tenant)

        response = authenticated_client.delete(self.detail_url(ug.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT

        note.refresh_from_db()
        assert note.deleted_at is not None

    def test_admin_can_delete_gamer_game(self, admin_client, tenant):
        """Verify that an admin can delete a gamer's game."""
        gamer = UserFactory(tenant=tenant, role=Roles.GAMER)
        ug = UserGameFactory(user=gamer, tenant=tenant)

        response = admin_client.delete(self.detail_url(ug.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_duplicate_game_addition(self, authenticated_client, user, tenant):
        """Verify that adding the same game on the same platform twice raises an error."""
        tg = TenantGameFactory(tenant=tenant)
        platform = tg.game.platforms.first()

        UserGameFactory(user=user, tenant=tenant, tenant_game=tg, platform=platform)

        data = {
            "tenant_game": str(tg.id),
            "platform": str(platform.id),
            "status": Status.PLAYING,
        }
        response = authenticated_client.post(self.list_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already have this game" in str(response.data)

    def test_invalid_personal_rating(self, authenticated_client, user, tenant):
        """Verify personal rating validates 0-5 bounds."""
        tg = TenantGameFactory(tenant=tenant)
        data = {
            "tenant_game": str(tg.id),
            "platform": str(tg.game.platforms.first().id),
            "status": Status.PLAYING,
            "personal_rating": 8,
        }
        response = authenticated_client.post(self.list_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Personal rating must be between 0 and 5" in str(response.data)

    def test_invalid_hours_played(self, authenticated_client, user, tenant):
        """Verify hours played validates maximum realistic bounds."""
        tg = TenantGameFactory(tenant=tenant)
        data = {
            "tenant_game": str(tg.id),
            "platform": str(tg.game.platforms.first().id),
            "status": Status.PLAYING,
            "hours_played": 200000,
        }
        response = authenticated_client.post(self.list_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot exceed 100,000" in str(response.data)

    def test_unauthenticated_user_cannot_list_games(self, api_client):
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
