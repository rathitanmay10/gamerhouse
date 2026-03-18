import pytest

from tests.factories.catalog import GameFactory, GenreFactory, PlatformFactory


@pytest.mark.django_db
class TestGameModel:
    def test_game_creation(self):
        genre = GenreFactory(name="Adventure")
        p1 = PlatformFactory(name="PC")
        p2 = PlatformFactory(name="Console")

        game = GameFactory(
            title="Epic Quest",
            description="A very long journey.",
            genre=genre,
            platforms=[p1, p2],
        )

        assert game.title == "Epic Quest"
        assert game.description == "A very long journey."
        assert game.genre == genre
        assert game.platforms.count() == 2

    def test_game_str(self):
        game = GameFactory(title="City Builder XYZ")
        assert str(game) == "City Builder XYZ"

    def test_game_soft_delete(self):
        game = GameFactory()
        game.delete()

        assert game.deleted_at is not None
        from catalog.models import Game

        assert Game.objects.filter(id=game.id).count() == 0
        assert Game.all_objects.filter(id=game.id).count() == 1
