import pytest

from tests.factories.user_games import UserGameFactory, UserGameNoteFactory


@pytest.mark.django_db
class TestUserGameNoteModel:
    def test_user_game_note_creation(self):
        """
        Verify that creating a UserGameNote sets the note text, associates it with the specified UserGame, and uses the same tenant as the UserGame.
        
        Creates a UserGame via factory and a UserGameNote linked to it, then asserts:
        - the note text matches the provided string,
        - the UserGameNote references the created UserGame,
        - the UserGameNote.tenant equals the linked UserGame.tenant.
        """
        ug = UserGameFactory()
        note = UserGameNoteFactory(user_game=ug, note="Excited to play this!")

        assert note.note == "Excited to play this!"
        assert note.user_game == ug
        assert note.tenant == note.user_game.tenant
