from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from core.enums import Roles
from core.models import BaseModel
from users.managers import UserManager


class User(BaseModel, AbstractUser):
    """
    Custom user model extending AbstractUser with:
    - UUID primary key
    - Unique email
    - Role-based access via Roles enum
    - Soft deletion support
    """

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.GAMER)
    tenant = models.ForeignKey(
        "tenants.Tenant",
        related_name="users",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    is_verified = models.BooleanField(default=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    objects = UserManager()

    def soft_delete(self):
        """Soft delete the user by disabling login and recording deletion time."""
        now = timezone.now()
        self.deleted_at = now
        self.is_active = False
        self.save()

    def delete(self, *args, **kwargs):
        """Override delete to enforce soft deletion."""
        self.soft_delete()

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "role"], name="idx_user_tenant_role"),
            models.Index(
                fields=["email", "is_verified"], name="idx_user_email_verified"
            ),
        ]
