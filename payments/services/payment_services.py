"""
Business logic for payment processing.

This module contains payment-related business logic for creating orders,
verifying payments, activating premium subscriptions, and reconciling payments.
"""

import logging
from typing import Any, Dict

from django.conf import settings
from django.db import transaction

from core.context import get_correlation_id
from core.enums import TenantStatus
from payments.constants import PAYMENT_CAPTURE_MODE, PAYMENT_CURRENCY
from payments.enums import PaymentStatus, SubscriptionStatus
from payments.exceptions import (
    InvalidStateTransitionError,
    PaymentVerificationError,
    TenantAlreadyPremiumError,
    TenantMismatchError,
)
from payments.models import Payment, Subscription
from payments.razorpay_client import client
from tenants.models import Tenant
from users.models import User

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for handling payment operations."""

    @staticmethod
    @transaction.atomic
    def create_order(tenant: Tenant, admin: User, amount: int) -> Dict[str, Any]:
        """
        Create a Razorpay order and Payment record.
        """
        # Check if tenant is already premium
        if tenant.status == TenantStatus.PREMIUM:
            logger.warning(
                f"Tenant {tenant.id} is already premium",
                extra={"correlation_id": get_correlation_id(), "tenant_id": tenant.id},
            )
            raise TenantAlreadyPremiumError("Tenant is already premium")

        amount_paise = amount * 100

        try:
            razorpay_order = client.order.create(
                {
                    "amount": amount_paise,
                    "currency": PAYMENT_CURRENCY,
                    "payment_capture": PAYMENT_CAPTURE_MODE,
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to create Razorpay order: {e}",
                extra={"correlation_id": get_correlation_id(), "tenant_id": tenant.id},
            )
            raise

        payment = Payment.objects.create(
            tenant=tenant,
            admin=admin,
            razorpay_order_id=razorpay_order["id"],
            amount=amount_paise,
            status=PaymentStatus.CREATED,
            metadata={
                "razorpay_order": razorpay_order,
                "admin_email": admin.email,
            },
        )

        logger.info(
            f"Created payment {payment.id} for tenant {tenant.id}, "
            f"order_id: {razorpay_order['id']}",
            extra={
                "correlation_id": get_correlation_id(),
                "payment_id": str(payment.id),
                "tenant_id": tenant.id,
                "order_id": razorpay_order["id"],
            },
        )

        return {
            "payment_id": str(payment.id),
            "order_id": razorpay_order["id"],
            "amount": amount_paise,
            "key": settings.RAZORPAY_KEY_ID,
        }

    @staticmethod
    @transaction.atomic
    def verify_payment(
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        tenant: Tenant,
    ) -> Payment:
        """
        Correct Razorpay verification flow:
        1. Lock payment
        2. Check tenant match
        3. Save payment_id + signature early
        4. Verify signature (MUST come first)
        5. Fetch payment from Razorpay
        6. Ensure payment is captured
        7. Mark VERIFIED (idempotent)
        """

        payment = Payment.objects.select_for_update().get(
            razorpay_order_id=razorpay_order_id
        )

        if payment.tenant_id != tenant.id:
            raise TenantMismatchError("Payment does not belong to this tenant")

        if payment.status in [PaymentStatus.VERIFIED, PaymentStatus.ACTIVATED]:
            return payment

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.save()

        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                }
            )
        except Exception:
            payment.status = PaymentStatus.FAILED
            payment.error_message = "Invalid payment signature"
            payment.save()
            raise PaymentVerificationError("Invalid payment signature")

        rp_payment = client.payment.fetch(razorpay_payment_id)
        if rp_payment.get("status") != "captured":
            raise PaymentVerificationError("Payment not captured yet")
        payment.mark_verified()
        payment.save()

        return payment

    @staticmethod
    @transaction.atomic
    def activate_premium(payment_id: str) -> bool:
        """
        Activate premium subscription for a verified payment.
        This operation is idempotent.
        """
        payment = Payment.objects.select_for_update().get(id=payment_id)
        if payment.status == PaymentStatus.ACTIVATED:
            logger.info(
                f"Payment {payment.id} already activated",
                extra={
                    "correlation_id": get_correlation_id(),
                    "payment_id": str(payment.id),
                },
            )
            return False
        if payment.status != PaymentStatus.VERIFIED:
            logger.error(
                f"Cannot activate payment {payment.id} in state {payment.status}",
                extra={
                    "correlation_id": get_correlation_id(),
                    "payment_id": str(payment.id),
                    "status": payment.status,
                },
            )
            raise InvalidStateTransitionError(
                f"Payment must be verified before activation (current: {payment.status})"
            )

        tenant = payment.tenant

        if tenant.status != TenantStatus.PREMIUM:
            tenant.status = TenantStatus.PREMIUM
            tenant.save()
            logger.info(
                f"Tenant {tenant.id} status updated to PREMIUM",
                extra={"correlation_id": get_correlation_id(), "tenant_id": tenant.id},
            )
        subscription, created = Subscription.objects.get_or_create(
            tenant=tenant, defaults={"status": SubscriptionStatus.NONE}
        )

        if subscription.status != SubscriptionStatus.ACTIVE:
            subscription.activate(payment=payment)
            logger.info(
                f"Subscription activated for tenant {tenant.id}",
                extra={"correlation_id": get_correlation_id(), "tenant_id": tenant.id},
            )

        payment.mark_activated()
        payment.save()

        logger.info(
            f"Premium activated for tenant {tenant.id} via payment {payment.id}",
            extra={
                "correlation_id": get_correlation_id(),
                "tenant_id": tenant.id,
                "payment_id": str(payment.id),
            },
        )

        return True

    @staticmethod
    @transaction.atomic
    def reconcile_payment(payment_id: str) -> bool:
        """
        Reconcile payment status with Razorpay (for polling).
        """
        try:
            payment = Payment.objects.select_for_update().get(id=payment_id)

            if payment.is_terminal_state():
                logger.debug(
                    f"Payment {payment.id} in terminal state, skipping reconciliation"
                )
                return False

            if not payment.razorpay_payment_id:
                logger.debug(
                    f"Payment {payment.id} has no razorpay_payment_id, skipping"
                )
                return False

            razorpay_payment = client.payment.fetch(payment.razorpay_payment_id)

            razorpay_status = razorpay_payment.get("status")
            logger.info(
                f"Reconciling payment {payment.id}: "
                f"local={payment.status}, razorpay={razorpay_status}"
            )

            if razorpay_status == "captured":
                if payment.status == PaymentStatus.CREATED:
                    payment.status = PaymentStatus.PAID
                    payment.mark_verified()
                    payment.save()

                    PaymentService.activate_premium(str(payment.id))

                    logger.info(
                        f"Payment {payment.id} reconciled, verified, and activated"
                    )
                    return True
                elif payment.status == PaymentStatus.PAID:
                    return False

            elif razorpay_status == "failed":
                payment.status = PaymentStatus.FAILED
                payment.error_message = razorpay_payment.get(
                    "error_description", "Payment failed"
                )
                payment.save()
                logger.info(f"Payment {payment.id} marked as FAILED via reconciliation")
                return True

            return False

        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found for reconciliation")
            return False
        except Exception as e:
            logger.error(f"Error reconciling payment {payment_id}: {e}")
            return False
