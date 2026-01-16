from django.db import models

from core.models import BaseModel


class Genre(BaseModel):
    """
    Represents a game genre.

    Used as a reference entity to categorize games.
    Each genre has a unique, human-readable name.
    """

    name = models.CharField(max_length=255)

    class Meta:
        db_table = "genres"
        ordering = ["name"]

    def __str__(self):
        return self.name
