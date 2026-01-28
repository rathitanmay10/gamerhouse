from rest_framework import status
from rest_framework.exceptions import APIException


class PaymentError(APIException):
    """Base exception for payment-related errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A payment error occurred."
    default_code = "payment_error"


class PaymentVerificationError(PaymentError):
    """Raised when payment signature verification fails."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Payment verification failed."
    default_code = "payment_verification_failed"


class InvalidStateTransitionError(PaymentError):
    """Raised when attempting an invalid payment state transition."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid payment state transition."
    default_code = "invalid_state_transition"


class DuplicatePaymentError(PaymentError):
    """Raised when attempting to create a duplicate payment."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Payment already exists."
    default_code = "duplicate_payment"


class TenantMismatchError(PaymentError):
    """Raised when payment doesn't belong to the current tenant."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Payment does not belong to this tenant."
    default_code = "tenant_mismatch"


class TenantAlreadyPremiumError(PaymentError):
    """Raised when attempting to purchase premium for an already premium tenant."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Tenant is already premium."
    default_code = "tenant_already_premium"
