import pytest

from payments.enums import WebhookEventStatus
from payments.models.webhook_models import WebhookEvent


@pytest.mark.django_db
class TestWebhookEventModel:
    def test_webhook_event_creation(self):
        """Webhook event creation default status is PENDING."""
        event = WebhookEvent.objects.create(
            event_id="evt_123",
            event_type="payment.captured",
            payload={"id": "pay_XYZ", "status": "captured"},
            raw_body='{"id":"pay_XYZ","status":"captured"}',
        )
        assert event.status == WebhookEventStatus.PENDING
        assert event.retry_count == 0
        assert event.processed_at is None

    def test_webhook_event_str(self):
        """__str__ identifies webhook event."""
        event = WebhookEvent.objects.create(
            event_id="evt_str", event_type="payment.failed", payload={}, raw_body="{}"
        )
        assert str(event) == "WebhookEvent evt_str - payment.failed - pending"
