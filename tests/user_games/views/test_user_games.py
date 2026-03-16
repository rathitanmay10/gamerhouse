import pytest
from django.urls import reverse
from rest_framework import status

from core.constants import MAX_FREE_USER_GAMES
from core.enums import Roles, Status, TenantStatus
from tests.factories.tenant_games import TenantGameFactory
from tests.factories.tenants import TenantFactory
from tests.factories.user_games import UserGameFactory
from tests.factories.users import UserFactory


class TestUserGamesAPI:
    url = reverse("user-game-list")

    def test_gamer_can_add_game(self, authenticated_client, user, tenant):
        """Verify that a gamer can add a game from their tenant's catalog to their collection."""
        tg = TenantGameFactory(tenant=tenant)
        data = {
            "tenant_game": str(tg.id),
            "platform": str(tg.game.platforms.first().id),
            "status": Status.WISHLIST,
        }
        response = authenticated_client.post(self.url, data=data)
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
        response = authenticated_client.post(self.url, data=data)

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
        response = authenticated_client.post(self.url, data=data)
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
        response = admin_client.post(self.url, data=data)
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
        response = authenticated_client.post(self.url, data=data)
        # Serializer raises ValidationError if user != request_user for a gamer
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot assign games to other users" in str(response.data).lower()
        # Check that it was actually added to the requester, not other_user
        assert other_user.user_games.count() == 0

    def test_unauthenticated_cannot_access(self, api_client):
        """Verify that unauthenticated requests are rejected."""
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
