"""
Custom exceptions for payment processing.
"""


class PaymentError(Exception):
    """Base exception for payment-related errors."""

    pass


class PaymentVerificationError(PaymentError):
    """Raised when payment signature verification fails."""

    pass


class InvalidStateTransitionError(PaymentError):
    """Raised when attempting an invalid payment state transition."""

    pass


class DuplicatePaymentError(PaymentError):
    """Raised when attempting to create a duplicate payment."""

    pass


class TenantMismatchError(PaymentError):
    """Raised when payment doesn't belong to the current tenant."""

    pass


class TenantAlreadyPremiumError(PaymentError):
    """Raised when attempting to purchase premium for an already premium tenant."""

    pass
