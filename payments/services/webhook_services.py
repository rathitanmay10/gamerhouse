"""
Business logic for webhook event processing.

This module contains webhook-related business logic for handling Razorpay
webhook events, ensuring idempotency, and processing payment.captured events.
"""

import logging
from typing import Any, Dict

from django.db import transaction
from django.utils import timezone

from payments.enums import PaymentStatus, WebhookEventStatus
from payments.models import Payment, WebhookEvent

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for handling webhook events."""

    @staticmethod
    def is_duplicate_event(event_id: str) -> bool:
        """Check if webhook event already processed."""
        return WebhookEvent.objects.filter(event_id=event_id).exists()

    @staticmethod
    @transaction.atomic
    def log_webhook_event(
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        raw_body: str,
        status: str = WebhookEventStatus.PENDING,
    ) -> WebhookEvent:
        """
        Log webhook event for idempotency and audit.

        Args:
            event_id: Unique event ID from Razorpay
            event_type: Event type (e.g., "payment.captured")
            payload: Parsed JSON payload
            raw_body: Raw request body
            status: Initial status

        Returns:
            WebhookEvent object
        """
        webhook_event = WebhookEvent.objects.create(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            raw_body=raw_body,
            status=status,
        )

        logger.info(f"Logged webhook event {event_id} - {event_type}")
        return webhook_event

    @staticmethod
    @transaction.atomic
    def process_payment_captured(
        payload: Dict[str, Any], webhook_event: WebhookEvent
    ) -> bool:
        """
        Process payment.captured webhook event.

        Args:
            payload: Webhook payload
            webhook_event: WebhookEvent object

        Returns:
            True if processed successfully
        """
        try:
            # Extract payment data
            payment_entity = (
                payload.get("payload", {}).get("payment", {}).get("entity", {})
            )

            razorpay_order_id = payment_entity.get("order_id")
            razorpay_payment_id = payment_entity.get("id")

            if not razorpay_order_id or not razorpay_payment_id:
                logger.error("Missing order_id or payment_id in webhook payload")
                webhook_event.status = WebhookEventStatus.FAILED
                webhook_event.error_message = "Missing required fields in payload"
                webhook_event.save()
                return False

            # Find and lock payment
            try:
                payment = Payment.objects.select_for_update().get(
                    razorpay_order_id=razorpay_order_id
                )
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for order_id: {razorpay_order_id}")
                webhook_event.status = WebhookEventStatus.FAILED
                webhook_event.error_message = f"Payment not found: {razorpay_order_id}"
                webhook_event.save()
                return False

            # Check if already processed (idempotency)
            if payment.status in [PaymentStatus.VERIFIED, PaymentStatus.ACTIVATED]:
                logger.info(
                    f"Payment {payment.id} already verified/activated, skipping webhook"
                )
                webhook_event.status = WebhookEventStatus.PROCESSED
                webhook_event.processed_at = timezone.now()
                webhook_event.save()
                return True

            # Update payment to PAID status
            if payment.can_transition_to(PaymentStatus.PAID):
                payment.status = PaymentStatus.PAID
                payment.razorpay_payment_id = razorpay_payment_id
                payment.save()
                logger.info(f"Payment {payment.id} marked as PAID via webhook")

            # Mark webhook as processed
            webhook_event.status = WebhookEventStatus.PROCESSED
            webhook_event.processed_at = timezone.now()
            webhook_event.save()

            logger.info(
                f"Webhook event {webhook_event.event_id} processed successfully"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error processing webhook event {webhook_event.event_id}: {e}"
            )
            webhook_event.status = WebhookEventStatus.FAILED
            webhook_event.error_message = str(e)
            webhook_event.retry_count += 1
            webhook_event.save()
            return False
