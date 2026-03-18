import pytest

from payments.enums import SubscriptionStatus
from tests.factories.payments import PaymentFactory, SubscriptionFactory


@pytest.mark.django_db
class TestSubscriptionModel:
    def test_subscription_creation(self):
        sub = SubscriptionFactory(status=SubscriptionStatus.NONE)
        assert sub.status == SubscriptionStatus.NONE
        assert sub.activated_at is None
        assert sub.payment is None

    def test_subscription_activate(self):
        sub = SubscriptionFactory(status=SubscriptionStatus.NONE)
        payment = PaymentFactory(admin__tenant=sub.tenant)

        sub.activate(payment=payment)

        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.activated_at is not None
        assert sub.payment == payment
