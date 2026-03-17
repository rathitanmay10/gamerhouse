import pytest

from core.enums import TenantStatus
from payments.enums import PaymentStatus
from payments.models.payment_models import Payment
from tenants.models import Tenant
from users.models import User


@pytest.fixture
def payment_test_data(db):
    tenant = Tenant.objects.create(name="Gaming Corp", status=TenantStatus.ACTIVE)
    admin_user = User.objects.create(
        email="admin@gamingcorp.com", username="admin", tenant=tenant
    )
    return {"tenant": tenant, "admin": admin_user}


class TestPaymentModel:
    def test_payment_creation(self, payment_test_data):
        """Payment is created with default status."""
        payment = Payment.objects.create(
            tenant=payment_test_data["tenant"],
            admin=payment_test_data["admin"],
            razorpay_order_id="order_12345",
            amount=50000,  # 500.00 INR
        )
        assert payment.status == PaymentStatus.CREATED
        assert payment.amount == 50000
        assert payment.verified_at is None
        assert payment.activated_at is None

    def test_payment_str(self, payment_test_data):
        """__str__ returns payment identifier information."""
        payment = Payment.objects.create(
            tenant=payment_test_data["tenant"],
            admin=payment_test_data["admin"],
            razorpay_order_id="order_abc",
            amount=10000,
        )
        expected_str = f"Payment {payment.id} - Gaming Corp - {PaymentStatus.CREATED}"
        assert str(payment) == expected_str

    def test_can_transition_to(self, payment_test_data):
        """Transition checks enforce valid state flow."""
        payment = Payment.objects.create(
            tenant=payment_test_data["tenant"],
            admin=payment_test_data["admin"],
            razorpay_order_id="order_xyz",
            amount=10000,
        )

        assert payment.can_transition_to(PaymentStatus.PAID) is True
        assert payment.can_transition_to(PaymentStatus.ACTIVATED) is False

        payment.status = PaymentStatus.PAID
        assert payment.can_transition_to(PaymentStatus.VERIFIED) is True

    def test_is_terminal_state(self, payment_test_data):
        """Terminal states are correctly identified."""
        payment = Payment.objects.create(
            tenant=payment_test_data["tenant"],
            admin=payment_test_data["admin"],
            razorpay_order_id="order_term",
            amount=10000,
        )
        assert payment.is_terminal_state() is False

        payment.status = PaymentStatus.FAILED
        assert payment.is_terminal_state() is True

        payment.status = PaymentStatus.ACTIVATED
        assert payment.is_terminal_state() is True

    def test_mark_verified(self, payment_test_data):
        """mark_verified changes status and sets timestamp."""
        payment = Payment.objects.create(
            tenant=payment_test_data["tenant"],
            admin=payment_test_data["admin"],
            razorpay_order_id="order_verify",
            amount=10000,
            status=PaymentStatus.PAID,
        )
        payment.mark_verified()
        assert payment.status == PaymentStatus.VERIFIED
        assert payment.verified_at is not None

    def test_mark_activated(self, payment_test_data):
        """mark_activated changes status and sets timestamp."""
        payment = Payment.objects.create(
            tenant=payment_test_data["tenant"],
            admin=payment_test_data["admin"],
            razorpay_order_id="order_activate",
            amount=10000,
            status=PaymentStatus.VERIFIED,
        )
        payment.mark_activated()
        assert payment.status == PaymentStatus.ACTIVATED
        assert payment.activated_at is not None
