import pytest
from django.urls import reverse
from rest_framework import status

from tests.factories.catalog import GameFactory
from tests.factories.tenant_games import TenantGameFactory


@pytest.fixture
def catalog_games():
    """Create a pool of games in the central catalog."""
    return GameFactory.create_batch(5)


class TestTenantGamesAPI:
    url = reverse("tenant_game-list")

    def test_admin_can_list_tenant_games(self, admin_client, tenant):
        """Verify that a tenant admin can list games mapped to their tenant."""
        # Create some games for this tenant
        TenantGameFactory.create_batch(3, tenant=tenant)
        # Create a game for another tenant (to verify it doesn't break list, though queryset is global)
        TenantGameFactory()

        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_gamer_can_list_tenant_games(self, authenticated_client, tenant):
        """Verify that a gamer can list games available in their tenant."""
        TenantGameFactory.create_batch(2, tenant=tenant)
        response = authenticated_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 2

    def test_admin_can_bulk_add_games(self, admin_client, tenant, catalog_games):
        """Verify that a tenant admin can bulk add games from the catalog."""
        bulk_url = reverse("tenant_game-bulk-add")
        game_ids = [str(g.id) for g in catalog_games]

        data = {"games": game_ids}
        response = admin_client.post(bulk_url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["created"] == len(game_ids)
        assert tenant.tenant_games.count() == len(game_ids)

    def test_gamer_cannot_bulk_add_games(self, authenticated_client, catalog_games):
        """Verify that a gamer does not have permission to bulk add games."""
        bulk_url = reverse("tenant_game-bulk-add")
        data = {"games": [str(g.id) for g in catalog_games]}
        response = authenticated_client.post(bulk_url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_bulk_delete_games(self, admin_client, tenant):
        """Verify that a tenant admin can bulk remove games from their tenant."""
        tg_objects = TenantGameFactory.create_batch(3, tenant=tenant)
        bulk_url = reverse("tenant_game-bulk-delete")
        tg_ids = [str(tg.id) for tg in tg_objects]

        data = {"tenant_games": tg_ids}
        response = admin_client.post(bulk_url, data=data, format="json")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert tenant.tenant_games.count() == 0

    def test_unauthenticated_cannot_access(self, api_client):
        """Verify that unauthenticated requests are rejected."""
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
