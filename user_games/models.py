from django.db import models

from core.enums import Status
from core.models import BaseModel


class UserGame(BaseModel):
    user = models.ForeignKey(
        "users.User", related_name="user_games", on_delete=models.CASCADE
    )
    game = models.ForeignKey(
        "catalog.Game", related_name="user_games", on_delete=models.CASCADE
    )
    platform = models.ForeignKey(
        "catalog.Platform", related_name="user_games", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WISHLIST
    )
    hours_played = models.PositiveIntegerField(blank=True, null=True)
    personal_rating = models.PositiveSmallIntegerField(blank=True, null=True)
    started_on = models.DateField(blank=True, null=True)
    completed_on = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "user_games"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.game.title}"


class UserGameNote(BaseModel):
    user_game = models.ForeignKey(
        "user_games.UserGame", related_name="notes", on_delete=models.CASCADE
    )
    note = models.TextField()

    class Meta:
        db_table = "user_game_notes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note for {self.user_game.user.username} - {self.user_game.game.title}"
