from django.db import models
from django.utils import timezone

from core.enums import Status
from core.models import BaseModel


class ActiveGameManager(models.Manager):
    """
    Manager that returns only non-deleted games.
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class Game(BaseModel):
    """
    Stores a user's game entry with progress, rating, and status.

    Uses soft deletion via `deleted_at`.
    """

    user = models.ForeignKey(
        "users.User", related_name="games", on_delete=models.CASCADE
    )
    genre = models.ForeignKey(
        "catalog.Genre", related_name="games", on_delete=models.CASCADE
    )
    platform = models.ForeignKey(
        "catalog.Platform", related_name="games", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WISHLIST
    )
    hours_played = models.PositiveIntegerField(blank=True, null=True)
    personal_rating = models.PositiveSmallIntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    completed_at = models.DateField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = ActiveGameManager()
    all_objects = models.Manager()

    def soft_delete(self):
        """
        Mark the game as deleted without removing the database record.
        """
        self.deleted_at = timezone.now()
        self.save()

    def delete(self, *args, **kwargs):
        """
        Override delete to enforce soft deletion.
        """
        self.soft_delete()

    class Meta:
        db_table = "games"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["created_at"]),
        ]
