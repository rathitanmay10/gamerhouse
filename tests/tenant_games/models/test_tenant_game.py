import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from catalog.models import Game, Genre, Platform
from tenant_games.models import TenantGame
from tenants.models import Tenant
from user_games.models import UserGame
from users.models import User


@pytest.fixture
def test_data(db):
    genre = Genre.objects.create(name="RPG")
    platform = Platform.objects.create(name="PC")
    game = Game.objects.create(title="Test RPG", genre=genre)
    game.platforms.add(platform)

    tenant = Tenant.objects.create(name="Test Tenant")
    user = User.objects.create(
        email="gamer@example.com", username="gamer", tenant=tenant
    )

    tenant_game = TenantGame.objects.create(tenant=tenant, game=game)

    return {
        "genre": genre,
        "platform": platform,
        "game": game,
        "tenant": tenant,
        "user": user,
        "tenant_game": tenant_game,
    }


class TestTenantGameModel:
    def test_tenant_game_creation(self, test_data):
        tg = test_data["tenant_game"]
        assert tg.tenant == test_data["tenant"]
        assert tg.game == test_data["game"]
        assert tg.id is not None

    def test_tenant_game_str(self, test_data):
        tg = test_data["tenant_game"]
        expected_str = f"{test_data['tenant'].name} - {test_data['game'].title}"
        assert str(tg) == expected_str

    def test_unique_active_tenant_game_constraint(self, test_data):
        with pytest.raises(IntegrityError):
            TenantGame.objects.create(
                tenant=test_data["tenant"], game=test_data["game"]
            )

    def test_tenant_game_deletion_protected(self, test_data):
        tg = test_data["tenant_game"]

        UserGame.objects.create(
            user=test_data["user"],
            tenant_game=tg,
            platform=test_data["platform"],
            tenant=test_data["tenant"],
        )

        with pytest.raises(ProtectedError):
            tg.delete()

    def test_tenant_game_soft_delete(self, test_data):
        tg = test_data["tenant_game"]
        tg_id = tg.id
        tg.delete()

        assert tg.deleted_at is not None
        assert TenantGame.objects.filter(id=tg_id).count() == 0
        assert TenantGame.all_objects.filter(id=tg_id).count() == 1
