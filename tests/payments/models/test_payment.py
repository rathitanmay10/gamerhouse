import pytest

from payments.enums import PaymentStatus
from tests.factories.payments import PaymentFactory


@pytest.mark.django_db
class TestPaymentModel:
    def test_payment_creation(self):
        payment = PaymentFactory(amount=50000)
        assert payment.status == PaymentStatus.CREATED
        assert payment.amount == 50000
        assert payment.verified_at is None
        assert payment.activated_at is None

    def test_payment_str(self):
        payment = PaymentFactory()
        expected_str = (
            f"Payment {payment.id} - {payment.tenant.name} - {PaymentStatus.CREATED}"
        )
        assert str(payment) == expected_str

    def test_can_transition_to(self):
        payment = PaymentFactory(status=PaymentStatus.CREATED)
        assert payment.can_transition_to(PaymentStatus.PAID) is True
        assert payment.can_transition_to(PaymentStatus.ACTIVATED) is False

        payment.status = PaymentStatus.PAID
        assert payment.can_transition_to(PaymentStatus.VERIFIED) is True

    def test_is_terminal_state(self):
        payment = PaymentFactory(status=PaymentStatus.CREATED)
        assert payment.is_terminal_state() is False

        payment.status = PaymentStatus.FAILED
        assert payment.is_terminal_state() is True

    def test_mark_verified(self):
        payment = PaymentFactory(status=PaymentStatus.PAID)
        payment.mark_verified()
        assert payment.status == PaymentStatus.VERIFIED
        assert payment.verified_at is not None

    def test_mark_activated(self):
        payment = PaymentFactory(status=PaymentStatus.VERIFIED)
        payment.mark_activated()
        assert payment.status == PaymentStatus.ACTIVATED
        assert payment.activated_at is not None
