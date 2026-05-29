import pytest

from tests.factories.catalog import GameFactory, GenreFactory, PlatformFactory


@pytest.mark.django_db
class TestGameModel:
    def test_game_creation(self):
        """
        Verify that a Game can be created with the given title, description, genre, and platforms.
        
        Asserts that the created game's title and description match the provided values, that its genre is the supplied Genre instance, and that it is associated with exactly two Platform instances.
        """
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

    def test_game_soft_delete(self):
        game = GameFactory()
        game.delete()

        assert game.deleted_at is not None
        from catalog.models import Game

        assert Game.objects.filter(id=game.id).count() == 0
        assert Game.all_objects.filter(id=game.id).count() == 1
