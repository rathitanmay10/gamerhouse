from django.db import models

from core.models import BaseModel


class Game(BaseModel):
    """
    Represents a game with genre and platform associations.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    release_date = models.DateField(blank=True, null=True)
    genre = models.ForeignKey(
        "catalog.Genre", related_name="games", on_delete=models.PROTECT
    )
    platforms = models.ManyToManyField("catalog.Platform", related_name="games")

    class Meta:
        db_table = "games"
        ordering = ["title"]

    def __str__(self):
        return self.title
