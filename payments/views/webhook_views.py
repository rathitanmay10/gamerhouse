import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.razorpay_client import client
from payments.services import WebhookService
from payments.tasks import process_webhook_task

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class RazorpayWebhookAPIView(APIView):
    """
    Handle Razorpay webhook events.

    This endpoint receives webhook notifications from Razorpay.
    It verifies the signature, logs the event for idempotency, and processes it asynchronously.

    Note: Authentication is disabled as Razorpay uses signature verification.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        signature = request.headers.get("X-Razorpay-Signature", "")
        body = request.body

        try:
            client.utility.verify_webhook_signature(
                body.decode("utf-8"), signature, settings.RAZORPAY_WEBHOOK_SECRET
            )
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return Response({"error": "Invalid signature"}, status=200)

        try:
            payload = request.data
            event_type = payload.get("event")
            payment_entity = (
                payload.get("payload", {}).get("payment", {}).get("entity", {})
            )
            payment_id = payment_entity.get("id", "")
            event_id = f"{event_type}_{payment_id}_{payload.get('created_at', '')}"

            logger.info(f"Received webhook: {event_type}, event_id: {event_id}")

            if WebhookService.is_duplicate_event(event_id):
                logger.info(f"Duplicate webhook event {event_id}, skipping")
                return Response({"status": "duplicate"}, status=200)
            webhook_event = WebhookService.log_webhook_event(
                event_id=event_id,
                event_type=event_type,
                payload=payload,
                raw_body=body.decode("utf-8"),
            )

            if event_type in ["payment.captured", "payment.failed"]:
                process_webhook_task.delay(payload, str(webhook_event.id))
                logger.info(f"Queued webhook processing for event {event_id}")
            else:
                logger.info(f"Ignoring webhook event type: {event_type}")

            return Response({"status": "ok"}, status=200)

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return Response({"status": "error"}, status=200)
