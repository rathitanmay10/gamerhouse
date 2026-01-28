import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdminRole
from payments.exceptions import (
    InvalidStateTransitionError,
    PaymentVerificationError,
    TenantAlreadyPremiumError,
    TenantMismatchError,
)
from payments.serializers import CreateOrderSerializer, VerifyPaymentSerializer
from payments.services import PaymentService
from payments.tasks import activate_premium_task

logger = logging.getLogger(__name__)


class CreateOrderAPIView(APIView):
    """
    Create a Razorpay order for premium subscription purchase.

    Only tenant admins can create orders (not super admins).
    Blocks creation if tenant is already premium.
    """

    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        tenant = request.user.tenant
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]

        try:
            order_data = PaymentService.create_order(
                tenant=tenant, admin=request.user, amount=amount
            )

            logger.info(
                f"Order created successfully for tenant {tenant} by user {request.user}"
            )

            return Response(order_data, status=status.HTTP_201_CREATED)

        except TenantAlreadyPremiumError as e:
            logger.warning(f"Tenant {tenant} already premium")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(
                f"Error creating order for tenant {tenant}: {e}", exc_info=True
            )
            return Response(
                {"error": "Failed to create order. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyPaymentAPIView(APIView):
    """
    Verify payment signature and activate premium subscription.

    Called by frontend after successful payment.
    Uses atomic transactions to prevent race conditions with webhooks.
    Only tenant admins can verify payments (not super admins).
    """

    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        tenant = request.user.tenant

        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        razorpay_order_id = serializer.validated_data["razorpay_order_id"]
        razorpay_payment_id = serializer.validated_data["razorpay_payment_id"]
        razorpay_signature = serializer.validated_data["razorpay_signature"]

        try:
            payment = PaymentService.verify_payment(
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
                tenant=tenant,
            )
            activate_premium_task.delay(str(payment.id))

            logger.info(
                f"Payment {payment.id} verified successfully for tenant {tenant.id}"
            )

            return Response(
                {
                    "status": "success",
                    "message": "Payment verified successfully",
                    "payment_id": str(payment.id),
                }
            )

        except PaymentVerificationError as e:
            logger.error(f"Payment verification failed: {e}")
            return Response(
                {"error": "Invalid payment signature"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TenantMismatchError as e:
            logger.error(f"Tenant mismatch during verification: {e}")
            return Response(
                {"error": "Payment does not belong to your tenant"},
                status=status.HTTP_403_FORBIDDEN,
            )
        except InvalidStateTransitionError as e:
            logger.error(f"Invalid state transition: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error verifying payment: {e}", exc_info=True)
            return Response(
                {"error": "Failed to verify payment. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
