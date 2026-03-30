import pytest

from tests.factories.user_games import UserGameFactory, UserGameNoteFactory


@pytest.mark.django_db
class TestUserGameNoteModel:
    def test_user_game_note_creation(self):
        ug = UserGameFactory()
        note = UserGameNoteFactory(user_game=ug, note="Excited to play this!")

        assert note.note == "Excited to play this!"
        assert note.user_game == ug
        assert note.tenant == note.user_game.tenant
