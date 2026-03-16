import pytest
from django.db.models import ProtectedError

from catalog.models import Game, Genre, Platform


@pytest.mark.django_db
class TestPlatformModel:
    def test_platform_creation(self):
        platform = Platform.objects.create(name="PlayStation 5")
        assert platform.name == "PlayStation 5"
        assert platform.id is not None

    def test_platform_str(self):
        platform = Platform.objects.create(name="Xbox Series X")
        assert str(platform) == "Xbox Series X"

    def test_platform_deletion_protected(self):
        genre = Genre.objects.create(name="Racing")
        platform = Platform.objects.create(name="PC")

        game = Game.objects.create(title="Speed Racer", genre=genre)
        game.platforms.add(platform)

        with pytest.raises(ProtectedError):
            platform.delete()

    def test_platform_deletion_allowed(self):
        platform = Platform.objects.create(name="Nintendo Switch")
        platform.delete()

        assert platform.deleted_at is not None
        assert Platform.objects.filter(id=platform.id).count() == 0
        assert Platform.all_objects.filter(id=platform.id).count() == 1
