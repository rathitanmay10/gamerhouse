from enum import StrEnum

from django.db.models import TextChoices


class Roles(TextChoices):
    """
    Defines role choices for the User model.

    Roles:
    - ADMIN: System administrator with elevated privileges.
    - GAMER: Regular user with access to personal gaming features.
    """

    SUPER_ADMIN = "super admin", "Super Admin"
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


class TenantStatus(TextChoices):
    """
    Tenant status values used to track a tenant's status.
    """

    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    PREMIUM = "premium", "Premium"


class UserStatus(StrEnum):
    """
    User status used for filtering via the `status` query parameter.

    ACTIVE  → not soft-deleted (deleted_at IS NULL)
    DELETED → soft-deleted (deleted_at IS NOT NULL)
    """

    ACTIVE = "active"
    DELETED = "deleted"
