from django.db.models import TextChoices


class PaymentStatus(TextChoices):
    CREATED = "created", "Created"
    AUTHORIZED = "authorized", "Authorized"
    PAID = "paid", "Paid"
    VERIFIED = "verified", "Verified"
    ACTIVATED = "activated", "Activated"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"
    CANCELLED = "cancelled", "Cancelled"


class SubscriptionStatus(TextChoices):
    NONE = "none", "No Subscription"
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"


class WebhookEventStatus(TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    PROCESSED = "processed", "Processed"
    FAILED = "failed", "Failed"
