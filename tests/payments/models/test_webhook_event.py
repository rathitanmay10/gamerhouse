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
