import uuid

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils import timezone

from core.context import get_current_tenant


class ActiveManager(models.Manager):
    def get_queryset(self):
        tenant = get_current_tenant()
        qs = super().get_queryset().filter(deleted_at__isnull=True)

        if tenant:
            try:
                self.model._meta.get_field("tenant")
                qs = qs.filter(tenant=tenant)
            except FieldDoesNotExist:
                pass
        return qs


class BaseModel(models.Model):
    """
    Abstract base model providing a UUID primary key and timestamp fields.

    Features:
    - `id`: UUID primary key for globally unique identification
    - `created_at`: Timestamp set when the record is first created
    - `updated_at`: Timestamp automatically updated on each save
    - `deleted_at`: Timestamp set when the record is deleted(soft delete)

    This model is abstract and does not create a database table.
    Intended to be inherited by concrete domain models.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    def soft_delete(self):
        """
        Mark as deleted without removing the database record.
        """
        self.deleted_at = timezone.now()
        self.save()

    def delete(self, *args, **kwargs):
        """
        Override delete to enforce soft deletion.
        """
        self.soft_delete()

    class Meta:
        abstract = True
