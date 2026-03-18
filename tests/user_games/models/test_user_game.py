import pytest

from core.enums import Status
from tests.factories.user_games import UserGameFactory


@pytest.mark.django_db
class TestUserGameModel:
    def test_user_game_creation(self):
        ug = UserGameFactory()
        assert ug.status == Status.WISHLIST
        assert ug.id is not None
        assert ug.hours_played is None
