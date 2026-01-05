import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from core.enums import Roles
from users.managers import AllUserManager, UserManager


class User(AbstractUser):
    """
    Custom user model extending AbstractUser with:
    - UUID primary key
    - Unique email
    - Role-based access via Roles enum
    - Soft deletion support
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.GAMER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = UserManager()
    all_objects = AllUserManager()

    def soft_delete(self):
        """Soft delete the user by disabling login and recording deletion time."""
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save()

    def delete(self, *args, **kwargs):
        """Override delete to enforce soft deletion."""
        self.soft_delete()

    class Meta:
        db_table = "users"
