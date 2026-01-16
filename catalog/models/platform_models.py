from django.db import models

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
