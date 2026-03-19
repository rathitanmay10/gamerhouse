import json

from django.urls import reverse
from rest_framework import status


class TestRazorpayWebhookAPIView:
    @property
    def url(self):
        return reverse("payments-webhook")

    def test_webhook_processes_valid_signature(self, api_client, mocker):
        """Verify that webhooks with a valid Razorpay signature are processed."""
        # Mock successful signature verification
        mocker.patch("payments.razorpay_client.client.utility.verify_webhook_signature")

        # Mock that this is not a duplicate event
        mocker.patch(
            "payments.services.WebhookService.is_duplicate_event", return_value=False
        )

        # Mock the service that logs the event to DB
        mock_log = mocker.patch("payments.services.WebhookService.log_webhook_event")
        mock_event = mocker.MagicMock()
        mock_event.id = 1
        mock_log.return_value = mock_event

        mock_task = mocker.patch(
            "payments.views.webhook_views.process_webhook_task.delay"
        )

        payload = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"id": "pay_testwebhook123"}}},
            "created_at": 1629815024,
        }

        headers = {"HTTP_X_RAZORPAY_SIGNATURE": "valid_signature"}
        response = api_client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            **headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"
        mock_log.assert_called_once()
        mock_task.assert_called_once()

    def test_webhook_fails_with_invalid_signature(self, api_client, mocker):
        """Verify that webhooks with invalid signatures return error cleanly."""
        from razorpay.errors import SignatureVerificationError

        mock_verify = mocker.patch(
            "payments.razorpay_client.client.utility.verify_webhook_signature"
        )
        mock_verify.side_effect = SignatureVerificationError("Invalid signature")

        mock_task = mocker.patch(
            "payments.views.webhook_views.process_webhook_task.delay"
        )

        payload = {"event": "payment.captured"}
        headers = {"HTTP_X_RAZORPAY_SIGNATURE": "invalid_signature"}
        response = api_client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            **headers,
        )

        # Razorpay expects 200 OK even on failure, but we return an error payload
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] == "Invalid signature"
        mock_task.assert_not_called()
