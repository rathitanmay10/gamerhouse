from catalog.models import Game, Genre, Platform


class TestGameModel:
    def test_game_creation(self):
        genre = Genre.objects.create(name="Adventure")
        platform1 = Platform.objects.create(name="PC")
        platform2 = Platform.objects.create(name="Console")

        game = Game.objects.create(
            title="Epic Quest",
            description="A very long journey.",
            release_date="2024-01-01",
            genre=genre,
        )
        game.platforms.add(platform1, platform2)

        assert game.title == "Epic Quest"
        assert game.description == "A very long journey."
        assert str(game.release_date) == "2024-01-01"
        assert game.genre == genre
        assert game.platforms.count() == 2

    def test_game_str(self):
        genre = Genre.objects.create(name="Simulation")
        game = Game.objects.create(title="City Builder XYZ", genre=genre)
        assert str(game) == "City Builder XYZ"

    def test_game_soft_delete(self):
        genre = Genre.objects.create(name="Sports")
        game = Game.objects.create(title="Football 2024", genre=genre)

        game.delete()

        assert game.deleted_at is not None
        assert Game.objects.filter(id=game.id).count() == 0
        assert Game.all_objects.filter(id=game.id).count() == 1
