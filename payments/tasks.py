import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .constants import (
    CELERY_MAX_RETRIES,
    CELERY_RETRY_BACKOFF_BASE,
    PAYMENT_ABANDON_MINUTES,
    POLLING_BATCH_SIZE,
    POLLING_CUTOFF_MINUTES,
    POLLING_INTERVAL_THRESHOLD_1,
    POLLING_INTERVAL_THRESHOLD_2,
    POLLING_INTERVAL_THRESHOLD_3,
    POLLING_MODULO_1,
    POLLING_MODULO_2,
    POLLING_MODULO_3,
)
from .enums import PaymentStatus, WebhookEventStatus
from .models import Payment, WebhookEvent
from .services import PaymentService, WebhookService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=CELERY_MAX_RETRIES)
def activate_premium_task(self, payment_id: str):
    """
    Activate premium subscription for a verified payment.

    This task is triggered after payment verification (either from client or webhook).
    It uses exponential backoff for retries.

    Args:
        payment_id: UUID of the payment
    """
    try:
        logger.info(f"Activating premium for payment {payment_id}")

        activated = PaymentService.activate_premium(payment_id)

        if activated:
            logger.info(f"Premium activated successfully for payment {payment_id}")
        else:
            logger.info(f"Premium already activated for payment {payment_id}")

    except Exception as e:
        logger.error(
            f"Error activating premium for payment {payment_id}: {e}", exc_info=True
        )

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2**self.request.retries * CELERY_RETRY_BACKOFF_BASE)


@shared_task(bind=True, max_retries=CELERY_MAX_RETRIES)
def process_webhook_task(self, payload: dict, webhook_event_id: str):
    """
    Process webhook event asynchronously.

    Args:
        payload: Webhook payload from Razorpay
        webhook_event_id: ID of the WebhookEvent record
    """
    try:
        logger.info(f"Processing webhook event {webhook_event_id}")

        # Get webhook event
        webhook_event = WebhookEvent.objects.get(id=webhook_event_id)

        # Update status to processing
        webhook_event.status = WebhookEventStatus.PROCESSING
        webhook_event.save()

        # Process based on event type
        event_type = payload.get("event")

        if event_type == "payment.captured":
            WebhookService.process_payment_captured(payload, webhook_event)
        elif event_type == "payment.failed":
            WebhookService.process_payment_failed(payload, webhook_event)
        else:
            logger.info(f"Ignoring webhook event type: {event_type}")
            webhook_event.status = WebhookEventStatus.PROCESSED
            webhook_event.processed_at = timezone.now()
            webhook_event.save()

    except WebhookEvent.DoesNotExist:
        logger.error(f"WebhookEvent {webhook_event_id} not found")
    except Exception as e:
        logger.error(f"Error processing webhook {webhook_event_id}: {e}", exc_info=True)

        # Update webhook event with error
        try:
            webhook_event = WebhookEvent.objects.get(id=webhook_event_id)
            webhook_event.status = WebhookEventStatus.FAILED
            webhook_event.error_message = str(e)
            webhook_event.retry_count += 1
            webhook_event.save()
        except Exception:
            pass

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2**self.request.retries * CELERY_RETRY_BACKOFF_BASE)


@shared_task
def polling_reconcile_task():
    """
    Polling task to reconcile payment status with Razorpay.

    This is a fallback mechanism in case webhooks fail or are delayed.
    Uses exponential backoff to avoid hammering the Razorpay API.

    Only polls payments that:
    - Are in non-terminal states (CREATED, PAID)
    - Have a razorpay_payment_id (can't poll without it)
    - Haven't been updated very recently (to avoid race conditions)
    """
    logger.info("Starting payment reconciliation polling task")

    # Find payments that need reconciliation
    # Exclude very recent payments (< 2 minutes old) to avoid race conditions
    cutoff_time = timezone.now() - timedelta(minutes=POLLING_CUTOFF_MINUTES)

    pending_payments = Payment.objects.filter(
        status__in=[PaymentStatus.CREATED, PaymentStatus.PAID],
        razorpay_payment_id__isnull=False,  # Must have payment ID to poll
        updated_at__lt=cutoff_time,  # Not updated very recently
    ).order_by("updated_at")[:POLLING_BATCH_SIZE]

    reconciled_count = 0

    for payment in pending_payments:
        # Calculate backoff based on payment age
        payment_age_minutes = (timezone.now() - payment.created_at).total_seconds() / 60

        # Skip if payment is too old (> 24 hours) - likely abandoned
        if payment_age_minutes > PAYMENT_ABANDON_MINUTES:
            logger.info(
                f"Payment {payment.id} is too old ({payment_age_minutes:.0f} min), skipping"
            )
            continue

        # Exponential backoff: poll less frequently as payment gets older
        if payment_age_minutes > POLLING_INTERVAL_THRESHOLD_3 and payment.updated_at.minute % POLLING_MODULO_3 != 0:
            continue
        elif payment_age_minutes > POLLING_INTERVAL_THRESHOLD_2 and payment.updated_at.minute % POLLING_MODULO_2 != 0:
            continue
        elif payment_age_minutes > POLLING_INTERVAL_THRESHOLD_1 and payment.updated_at.minute % POLLING_MODULO_1 != 0:
            continue

        try:
            updated = PaymentService.reconcile_payment(str(payment.id))

            if updated:
                reconciled_count += 1
                logger.info(f"Reconciled payment {payment.id}")

        except Exception as e:
            logger.error(f"Error reconciling payment {payment.id}: {e}")
            continue

    logger.info(
        f"Polling reconciliation complete. Reconciled {reconciled_count} payments"
    )
    return reconciled_count
