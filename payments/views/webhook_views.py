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

        # Verify webhook signature
        try:
            client.utility.verify_webhook_signature(
                body.decode("utf-8"), signature, settings.RAZORPAY_WEBHOOK_SECRET
            )
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            # Return 200 to prevent Razorpay from retrying invalid requests
            return Response({"error": "Invalid signature"}, status=200)

        try:
            payload = request.data

            # Extract event details
            # Razorpay webhook payload structure:
            # {
            #   "entity": "event",
            #   "account_id": "...",
            #   "event": "payment.captured",
            #   "contains": ["payment"],
            #   "payload": { ... },
            #   "created_at": 1234567890
            # }
            event_type = payload.get("event")

            # Generate unique event ID from Razorpay's event data
            # Razorpay doesn't provide a unique event ID, so we create one
            # from the payment ID and event type
            payment_entity = (
                payload.get("payload", {}).get("payment", {}).get("entity", {})
            )
            payment_id = payment_entity.get("id", "")
            event_id = f"{event_type}_{payment_id}_{payload.get('created_at', '')}"

            logger.info(f"Received webhook: {event_type}, event_id: {event_id}")

            # Check idempotency
            if WebhookService.is_duplicate_event(event_id):
                logger.info(f"Duplicate webhook event {event_id}, skipping")
                return Response({"status": "duplicate"}, status=200)

            # Log webhook event
            webhook_event = WebhookService.log_webhook_event(
                event_id=event_id,
                event_type=event_type,
                payload=payload,
                raw_body=body.decode("utf-8"),
            )

            # Process webhook asynchronously
            if event_type == "payment.captured":
                process_webhook_task.delay(payload, str(webhook_event.id))
                logger.info(f"Queued webhook processing for event {event_id}")
            else:
                logger.info(f"Ignoring webhook event type: {event_type}")

            return Response({"status": "ok"}, status=200)

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            # Always return 200 to prevent Razorpay from retrying
            return Response({"status": "error"}, status=200)
