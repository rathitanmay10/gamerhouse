from django.db import models
from django.db.models import ProtectedError

from core.models import BaseModel


class Platform(BaseModel):
    """
    Represents a gaming platform.

    Used as a reference entity to identify supported platforms
    such as PC, console, or mobile.
    Each platform has a unique name.
    """

    name = models.CharField(max_length=255)

    class Meta:
        db_table = "platforms"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        """
        Override delete to prevent deletion if referenced by active games.

        Raises ProtectedError if any active games use this platform.
        """
        if self.games.exists():
            raise ProtectedError(
                "Cannot delete Platform because it is referenced by active Games.",
                [self],
            )
        super().delete(*args, **kwargs)
