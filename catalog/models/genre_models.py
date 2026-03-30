from django.db import models
from django.db.models import ProtectedError

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

    def delete(self, *args, **kwargs):
        """
        Override delete to respect on_delete=PROTECT for soft deletes.

        Raises ProtectedError if any active games reference this genre.
        """
        if self.games.exists():
            raise ProtectedError(
                "Cannot delete Genre because it is referenced by active Games.",
                [self],
            )
        super().delete(*args, **kwargs)
