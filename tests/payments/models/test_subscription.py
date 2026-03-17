import pytest

from core.enums import TenantStatus
from payments.enums import SubscriptionStatus
from payments.models.payment_models import Payment
from payments.models.subscription_models import Subscription
from tenants.models import Tenant
from users.models import User


@pytest.fixture
def payment_test_data(db):
    tenant = Tenant.objects.create(name="Gaming Corp", status=TenantStatus.ACTIVE)
    admin_user = User.objects.create(
        email="admin@gamingcorp.com", username="admin", tenant=tenant
    )
    return {"tenant": tenant, "admin": admin_user}


class TestSubscriptionModel:
    def test_subscription_creation(self, payment_test_data):
        """Subscription created with default NONE status."""
        sub = Subscription.objects.create(tenant=payment_test_data["tenant"])
        assert sub.status == SubscriptionStatus.NONE
        assert sub.activated_at is None
        assert sub.payment is None

    def test_subscription_str(self, payment_test_data):
        """__str__ returns identifying tenant string."""
        sub = Subscription.objects.create(tenant=payment_test_data["tenant"])
        assert str(sub) == f"Subscription for Gaming Corp - {SubscriptionStatus.NONE}"

    def test_subscription_activate(self, payment_test_data):
        """activate() transitions status to active and links payment."""
        sub = Subscription.objects.create(tenant=payment_test_data["tenant"])
        payment = Payment.objects.create(
            tenant=payment_test_data["tenant"],
            admin=payment_test_data["admin"],
            razorpay_order_id="order_sub",
            amount=10000,
        )

        sub.activate(payment=payment)

        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.activated_at is not None
        assert sub.payment == payment
