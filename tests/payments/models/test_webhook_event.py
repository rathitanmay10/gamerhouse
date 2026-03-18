import pytest

from payments.enums import WebhookEventStatus
from tests.factories.payments import WebhookEventFactory


@pytest.mark.django_db
class TestWebhookEventModel:
    def test_webhook_event_creation(self):
        event = WebhookEventFactory()
        assert event.status == WebhookEventStatus.PENDING
        assert event.retry_count == 0
        assert event.processed_at is None

    def test_webhook_event_str(self):
        event = WebhookEventFactory(event_id="evt_str", event_type="payment.failed")
        assert str(event) == "WebhookEvent evt_str - payment.failed - pending"
