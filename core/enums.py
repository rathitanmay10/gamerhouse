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
