import factory

from payments.enums import PaymentStatus, SubscriptionStatus, WebhookEventStatus
from payments.models.payment_models import Payment
from payments.models.subscription_models import Subscription
from payments.models.webhook_models import WebhookEvent
from tests.factories.tenants import TenantFactory
from tests.factories.users import UserFactory


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    tenant = factory.SelfAttribute("admin.tenant")
    admin = factory.SubFactory(UserFactory)
    razorpay_order_id = factory.Sequence(lambda n: f"order_{n}")
    amount = 50000  # 500 INR in paise
    status = PaymentStatus.CREATED
    metadata = factory.LazyAttribute(
        lambda o: {
            "razorpay_order": {
                "id": o.razorpay_order_id,
                "amount": o.amount,
                "currency": "INR",
            },
            "admin_email": o.admin.email,
        }
    )


class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subscription

    tenant = factory.SubFactory(TenantFactory)
    status = SubscriptionStatus.ACTIVE


class WebhookEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebhookEvent

    event_id = factory.Sequence(lambda n: f"evt_{n}")
    event_type = "payment.captured"
    payload = factory.LazyAttribute(
        lambda o: {
            "event": o.event_type,
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_dummy",
                        "order_id": "order_dummy",
                        "amount": 50000,
                    }
                }
            },
        }
    )
    raw_body = "{}"
    status = WebhookEventStatus.PENDING
