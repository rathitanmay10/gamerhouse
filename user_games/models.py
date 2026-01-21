from django.db import models

from core.enums import Status
from core.models import BaseModel


class UserGame(BaseModel):
    user = models.ForeignKey(
        "users.User", related_name="user_games", on_delete=models.CASCADE
    )
    tenant_game = models.ForeignKey(
        "tenant_games.TenantGame",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    platform = models.ForeignKey(
        "catalog.Platform", related_name="user_games", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WISHLIST
    )
    tenant = models.ForeignKey(
        "tenants.Tenant", related_name="user_games", on_delete=models.CASCADE
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
            models.Index(fields=["user", "tenant"]),
        ]


class UserGameNote(BaseModel):
    user_game = models.ForeignKey(
        "user_games.UserGame", related_name="notes", on_delete=models.CASCADE
    )
    note = models.TextField()
    tenant = models.ForeignKey(
        "tenants.Tenant", related_name="notes", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "user_game_notes"
        ordering = ["-created_at"]
