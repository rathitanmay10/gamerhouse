from django.db import models

from core.models import BaseModel


class TenantGame(BaseModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", related_name="tenant_games", on_delete=models.CASCADE
    )
    game = models.ForeignKey(
        "catalog.Game", related_name="tenant_games", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "tenant_games"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "game"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_tenant_game",
            )
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.game.title}"
