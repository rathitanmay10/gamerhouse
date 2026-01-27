from rest_framework import serializers

from payments.constants import PREMIUM_PRICE_INR


class CreateOrderSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1, max_value=100000)

    def validate_amount(self, value):
        """Validate that amount matches premium price."""
        if value != PREMIUM_PRICE_INR:
            raise serializers.ValidationError(
                f"Invalid amount. Premium subscription costs ₹{PREMIUM_PRICE_INR}"
            )
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer for payment verification request."""

    razorpay_order_id = serializers.CharField(max_length=100, required=True)
    razorpay_payment_id = serializers.CharField(max_length=100, required=True)
    razorpay_signature = serializers.CharField(max_length=200, required=True)
