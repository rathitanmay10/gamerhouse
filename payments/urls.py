from django.urls import include, path
from rest_framework.routers import DefaultRouter

from payments.views import (
    CreateOrderAPIView,
    PaymentViewSet,
    RazorpayWebhookAPIView,
    SubscriptionViewSet,
    VerifyPaymentAPIView,
    WebhookEventViewSet,
)
from payments.views.views_ui import PremiumCheckoutPage

router = DefaultRouter()
router.register(r"admin/payments", PaymentViewSet, basename="admin-payment")
router.register(
    r"admin/subscriptions", SubscriptionViewSet, basename="admin-subscription"
)
router.register(r"admin/webhooks", WebhookEventViewSet, basename="admin-webhook")

urlpatterns = [
    path(
        "payments/create-order/",
        CreateOrderAPIView.as_view(),
        name="payments-create-order",
    ),
    path("payments/verify/", VerifyPaymentAPIView.as_view(), name="payments-verify"),
    path(
        "payments/webhook/", RazorpayWebhookAPIView.as_view(), name="payments-webhook"
    ),
    path("payments/checkout/", PremiumCheckoutPage.as_view(), name="premium-checkout"),
    path("", include(router.urls)),
]
