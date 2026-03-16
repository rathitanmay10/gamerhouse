import pytest
from django.db.models import ProtectedError

from catalog.models import Game, Genre, Platform


@pytest.mark.django_db
class TestGenreModel:
    def test_genre_creation(self):
        genre = Genre.objects.create(name="Action RPG")
        assert genre.name == "Action RPG"
        assert genre.id is not None
        assert genre.created_at is not None
        assert genre.updated_at is not None

    def test_genre_str(self):
        genre = Genre.objects.create(name="Strategy")
        assert str(genre) == "Strategy"

    def test_genre_deletion_protected(self):
        genre = Genre.objects.create(name="Shooter")
        platform = Platform.objects.create(name="PC")

        game = Game.objects.create(title="Test Game", genre=genre)
        game.platforms.add(platform)

        with pytest.raises(ProtectedError):
            genre.delete()

    def test_genre_deletion_allowed(self):
        genre = Genre.objects.create(name="Puzzle")
        genre.delete()

        assert genre.deleted_at is not None
        assert Genre.objects.filter(id=genre.id).count() == 0
        assert Genre.all_objects.filter(id=genre.id).count() == 1
