from django.db import models

from payments.enums import WebhookEventStatus


class WebhookEvent(models.Model):
    """
    Stores webhook events from Razorpay for idempotency and audit trail.
    """

    event_id = models.CharField(max_length=100, unique=True, db_index=True)
    event_type = models.CharField(max_length=50, db_index=True)
    payload = models.JSONField()
    raw_body = models.TextField(help_text="Raw request body for debugging")

    status = models.CharField(
        max_length=20,
        choices=WebhookEventStatus.choices,
        default=WebhookEventStatus.PENDING,
        db_index=True,
    )

    error_message = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)

    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "webhook_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self):
        return f"WebhookEvent {self.event_id} - {self.event_type} - {self.status}"
