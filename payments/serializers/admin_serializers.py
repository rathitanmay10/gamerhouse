from rest_framework import serializers

from payments.models import Payment, Subscription, WebhookEvent


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model with tenant and admin details."""

    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    tenant_status = serializers.CharField(source="tenant.status", read_only=True)
    admin_email = serializers.EmailField(source="admin.email", read_only=True)
    admin_name = serializers.CharField(source="admin.name", read_only=True)
    amount_inr = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "tenant_status",
            "admin",
            "admin_email",
            "admin_name",
            "razorpay_order_id",
            "razorpay_payment_id",
            "razorpay_signature",
            "amount",
            "amount_inr",
            "status",
            "verified_at",
            "activated_at",
            "error_message",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_amount_inr(self, obj):
        """Convert paise to INR for display."""
        return f"₹{obj.amount / 100:.2f}"


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model with tenant and payment details."""

    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    tenant_status = serializers.CharField(source="tenant.status", read_only=True)
    payment_id = serializers.UUIDField(source="payment.id", read_only=True)
    payment_status = serializers.CharField(source="payment.status", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "tenant_status",
            "payment",
            "payment_id",
            "payment_status",
            "status",
            "activated_at",
            "deactivated_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class WebhookEventSerializer(serializers.ModelSerializer):
    """Serializer for WebhookEvent model."""

    class Meta:
        model = WebhookEvent
        fields = [
            "id",
            "event_id",
            "event_type",
            "payload",
            "raw_body",
            "status",
            "error_message",
            "retry_count",
            "processed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
