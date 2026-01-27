import uuid

from django.db import models
from django.utils import timezone

from payments.enums import PaymentStatus
from tenants.models import Tenant
from users.models import User


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, db_index=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE)

    razorpay_order_id = models.CharField(max_length=100, unique=True, db_index=True)
    razorpay_payment_id = models.CharField(
        max_length=100, null=True, blank=True, db_index=True
    )
    razorpay_signature = models.CharField(max_length=200, null=True, blank=True)

    amount = models.IntegerField()  # in paise
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.CREATED,
        db_index=True,
    )

    # Lifecycle timestamps
    verified_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    # Error tracking
    error_message = models.TextField(null=True, blank=True)

    # Additional metadata (for debugging and audit)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.tenant.name} - {self.status}"

    def can_transition_to(self, new_status: str) -> bool:
        """
        Validates if the payment can transition to the new status.

        Valid transitions:
        CREATED → PAID, FAILED, CANCELLED
        PAID → VERIFIED, FAILED
        VERIFIED → ACTIVATED, FAILED
        ACTIVATED → (terminal state)
        FAILED → (terminal state)
        CANCELLED → (terminal state)
        """
        valid_transitions = {
            PaymentStatus.CREATED: [
                PaymentStatus.PAID,
                PaymentStatus.FAILED,
                PaymentStatus.CANCELLED,
            ],
            PaymentStatus.PAID: [PaymentStatus.VERIFIED, PaymentStatus.FAILED],
            PaymentStatus.VERIFIED: [PaymentStatus.ACTIVATED, PaymentStatus.FAILED],
            PaymentStatus.ACTIVATED: [],  # Terminal state
            PaymentStatus.FAILED: [],  # Terminal state
            PaymentStatus.CANCELLED: [],  # Terminal state
        }

        return new_status in valid_transitions.get(self.status, [])

    def is_terminal_state(self) -> bool:
        """Check if payment is in a terminal state."""
        return self.status in [
            PaymentStatus.ACTIVATED,
            PaymentStatus.FAILED,
            PaymentStatus.CANCELLED,
            PaymentStatus.REFUNDED,
        ]

    def mark_verified(self):
        """Mark payment as verified with timestamp."""
        if self.can_transition_to(PaymentStatus.VERIFIED):
            self.status = PaymentStatus.VERIFIED
            self.verified_at = timezone.now()

    def mark_activated(self):
        """Mark payment as activated with timestamp."""
        if self.can_transition_to(PaymentStatus.ACTIVATED):
            self.status = PaymentStatus.ACTIVATED
            self.activated_at = timezone.now()
