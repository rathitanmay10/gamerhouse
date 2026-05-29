import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from tests.factories.tenant_games import TenantGameFactory
from tests.factories.user_games import UserGameFactory


class TestTenantGameModel:
    def test_tenant_game_creation(self):
        tg = TenantGameFactory()
        assert tg.tenant is not None
        assert tg.game is not None
        assert tg.id is not None

    def test_unique_active_tenant_game_constraint(self):
        """
        Verifies that creating a second active TenantGame with the same tenant and game violates the database uniqueness constraint.
        
        Asserts that attempting to create another TenantGame using the same `tenant` and `game` as an existing record raises `IntegrityError`.
        """
        tg = TenantGameFactory()
        with pytest.raises(IntegrityError):
            TenantGameFactory(tenant=tg.tenant, game=tg.game)

    def test_tenant_game_deletion_protected(self):
        """
        Asserts that deleting a TenantGame is blocked when related UserGame instances exist.
        
        Creates a TenantGame and an associated UserGame, then verifies that attempting to delete the TenantGame raises a ProtectedError.
        """
        tg = TenantGameFactory()
        UserGameFactory(tenant_game=tg)

        with pytest.raises(ProtectedError):
            tg.delete()

    def test_tenant_game_soft_delete(self):
        """
        Verifies that deleting a TenantGame performs a soft delete: the instance's `deleted_at` is set, the default manager excludes the record, and the `all_objects` manager still returns it.
        """
        tg = TenantGameFactory()
        tg_id = tg.id
        tg.delete()

        assert tg.deleted_at is not None
        from tenant_games.models import TenantGame

        assert TenantGame.objects.filter(id=tg_id).count() == 0
        assert TenantGame.all_objects.filter(id=tg_id).count() == 1
