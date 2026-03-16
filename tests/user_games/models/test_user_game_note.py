import pytest

from catalog.models import Game, Genre, Platform
from tenant_games.models import TenantGame
from tenants.models import Tenant
from user_games.models import UserGame, UserGameNote
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
        "platform": platform,
        "tenant": tenant,
        "user": user,
        "tenant_game": tenant_game,
    }


@pytest.mark.django_db
class TestUserGameNoteModel:
    def test_user_game_note_creation(self, test_data):
        ug = UserGame.objects.create(
            user=test_data["user"],
            tenant_game=test_data["tenant_game"],
            platform=test_data["platform"],
            tenant=test_data["tenant"],
        )

        note = UserGameNote.objects.create(
            user_game=ug, note="Excited to play this!", tenant=test_data["tenant"]
        )

        assert note.note == "Excited to play this!"
        assert note.user_game == ug
        assert note.tenant == test_data["tenant"]
