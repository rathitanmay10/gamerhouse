from django.db.models import TextChoices


class Roles(TextChoices):
    """
    Defines role choices for the User model.

    Roles:
    - ADMIN: System administrator with elevated privileges.
    - GAMER: Regular user with access to personal gaming features.
    """

    ADMIN = "admin", "Admin"
    GAMER = "gamer", "Gamer"


class Status(TextChoices):
    """
    Game status values used to track a user's progress.
    """

    WISHLIST = "wishlist", "Wishlist"
    PLAYING = "playing", "Playing"
    COMPLETED = "completed", "Completed"
    DROPPED = "dropped", "Dropped"
