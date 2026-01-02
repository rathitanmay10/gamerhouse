import uuid
from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model providing a UUID primary key and timestamp fields.

    Features:
    - `id`: UUID primary key for globally unique identification
    - `created_at`: Timestamp set when the record is first created
    - `updated_at`: Timestamp automatically updated on each save

    This model is abstract and does not create a database table.
    Intended to be inherited by concrete domain models.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
