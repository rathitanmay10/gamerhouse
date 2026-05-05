import pytest
from django.urls import reverse
from rest_framework import status

from payments.constants import PREMIUM_PRICE_INR
from tests.factories.payments import PaymentFactory


@pytest.fixture(autouse=True)
def mock_payment_services(mocker):
    """
    Mock external side effects like celery tasks.
    """
    mocker.patch("payments.views.order_views.activate_premium_task.delay")


class TestCreateOrderAPIView:
    @property
    def url(self):
        return reverse("payments-create-order")

    def test_admin_can_create_order(self, admin_client, mocker):
        """Verify that a tenant admin can successfully create a razorpay order."""
        mock_create_order = mocker.patch(
            "payments.services.PaymentService.create_order"
        )
        mock_create_order.return_value = {
            "order_id": "order_test_123",
            "amount": PREMIUM_PRICE_INR,
            "currency": "INR",
        }

        data = {"amount": PREMIUM_PRICE_INR}
        response = admin_client.post(self.url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["order_id"] == "order_test_123"
        mock_create_order.assert_called_once()

    def test_non_admin_cannot_create_order(self, authenticated_client):
        """Verify that a regular user (gamer) cannot create an order."""
        data = {"amount": PREMIUM_PRICE_INR}
        response = authenticated_client.post(self.url, data=data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_already_premium_tenant_cannot_create_order(self, admin_client, mocker):
        """Verify that an order cannot be created if the tenant is already premium."""
        from payments.exceptions import TenantAlreadyPremiumError

        mock_create_order = mocker.patch(
            "payments.services.PaymentService.create_order"
        )
        mock_create_order.side_effect = TenantAlreadyPremiumError(
            "Tenant is already premium"
        )

        data = {"amount": PREMIUM_PRICE_INR}
        response = admin_client.post(self.url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already premium" in str(response.data)


class TestVerifyPaymentAPIView:
    @property
    def url(self):
        return reverse("payments-verify")

    def test_admin_can_verify_payment(self, admin_client, tenant, mocker):
        """Verify that an admin can successfully verify a payment to activate premium."""
        payment = PaymentFactory(tenant=tenant)
        mock_verify_payment = mocker.patch(
            "payments.services.PaymentService.verify_payment"
        )
        mock_verify_payment.return_value = payment

        mock_task = mocker.patch(
            "payments.views.order_views.activate_premium_task.delay"
        )

        data = {
            "razorpay_order_id": "order_123",
            "razorpay_payment_id": "pay_123",
            "razorpay_signature": "sig_123",
        }

        response = admin_client.post(self.url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"
        mock_verify_payment.assert_called_once()
        mock_task.assert_called_once_with(str(payment.id))

    def test_non_admin_cannot_verify_payment(self, authenticated_client):
        """Verify that a regular user cannot verify a payment."""
        data = {
            "razorpay_order_id": "order_123",
            "razorpay_payment_id": "pay_123",
            "razorpay_signature": "sig_123",
        }
        response = authenticated_client.post(self.url, data=data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verification_fails_with_invalid_signature(self, admin_client, mocker):
        """Verify that verification fails cleanly on bad signature."""
        from payments.exceptions import PaymentVerificationError

        mock_verify_payment = mocker.patch(
            "payments.services.PaymentService.verify_payment"
        )
        mock_verify_payment.side_effect = PaymentVerificationError("Invalid signature")

        data = {
            "razorpay_order_id": "order_123",
            "razorpay_payment_id": "pay_123",
            "razorpay_signature": "bad_sig",
        }

        response = admin_client.post(self.url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid payment signature" in str(response.data)
