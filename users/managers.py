from django.contrib.auth.models import BaseUserManager
from core.enums import Roles


class UserManager(BaseUserManager):
    """
    User manager with:
    - soft-delete filtering
    - required Django auth creation methods
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")

        email = self.normalize_email(email)
        extra_fields.setdefault("role", Roles.GAMER)
        extra_fields.setdefault("is_active", True)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Roles.ADMIN)

        if extra_fields.get("role") != Roles.ADMIN:
            raise ValueError("Superuser must have ADMIN role")

        return self.create_user(username, email, password, **extra_fields)
