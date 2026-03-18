import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from tests.factories.tenant_games import TenantGameFactory
from tests.factories.user_games import UserGameFactory


@pytest.mark.django_db
class TestTenantGameModel:
    def test_tenant_game_creation(self):
        tg = TenantGameFactory()
        assert tg.tenant is not None
        assert tg.game is not None
        assert tg.id is not None

    def test_tenant_game_str(self):
        tg = TenantGameFactory()
        expected_str = f"{tg.tenant.name} - {tg.game.title}"
        assert str(tg) == expected_str

    def test_unique_active_tenant_game_constraint(self):
        tg = TenantGameFactory()
        with pytest.raises(IntegrityError):
            TenantGameFactory(tenant=tg.tenant, game=tg.game)

    def test_tenant_game_deletion_protected(self):
        tg = TenantGameFactory()
        UserGameFactory(tenant_game=tg)

        with pytest.raises(ProtectedError):
            tg.delete()

    def test_tenant_game_soft_delete(self):
        tg = TenantGameFactory()
        tg_id = tg.id
        tg.delete()

        assert tg.deleted_at is not None
        from tenant_games.models import TenantGame

        assert TenantGame.objects.filter(id=tg_id).count() == 0
        assert TenantGame.all_objects.filter(id=tg_id).count() == 1
