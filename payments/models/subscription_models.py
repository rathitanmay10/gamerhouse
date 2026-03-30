import uuid

from django.db import models
from django.utils import timezone

from payments.enums import SubscriptionStatus
from tenants.models import Tenant


class Subscription(models.Model):
    """
    ONE subscription per TENANT.
    Lifetime = never expires.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="subscription"
    )

    # Track which payment activated this subscription
    payment = models.ForeignKey(
        "payments.Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions",
    )

    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.NONE,
        db_index=True,
    )

    activated_at = models.DateTimeField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscriptions"
        indexes = [
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self):
        return f"Subscription for {self.tenant.name} - {self.status}"

    def activate(self, payment=None):
        """Activate subscription (idempotent)."""
        if self.status != SubscriptionStatus.ACTIVE:
            self.status = SubscriptionStatus.ACTIVE
            self.activated_at = timezone.now()
            if payment:
                self.payment = payment
            self.save()
