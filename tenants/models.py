from django.db import models

from core.enums import TenantStatus
from core.models import BaseModel


class Tenant(BaseModel):
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=10, choices=TenantStatus.choices, default=TenantStatus.ACTIVE
    )

    class Meta:
        db_table = "tenants"
        ordering = ["name"]

    def __str__(self):
        return self.name
