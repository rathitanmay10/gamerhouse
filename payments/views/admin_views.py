from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from core.enums import Roles
from core.permissions import IsSuperAdminRole, IsSuperAdminRoleOrAdminRole
from payments.models import Payment, Subscription, WebhookEvent
from payments.serializers import (
    PaymentSerializer,
    SubscriptionSerializer,
    WebhookEventSerializer,
)


class PaymentViewSet(ReadOnlyModelViewSet):
    """
    Super admin read-only view for monitoring payments across all tenants.
    Regular admins can only view their own tenant's payments.
    """

    permission_classes = [IsAuthenticated, IsSuperAdminRoleOrAdminRole]
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {"status": ["exact", "in"]}
    search_fields = ["tenant__name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Super admins see all payments, regular admins see only their tenant's."""
        user = self.request.user
        qs = Payment.objects.select_related("tenant", "admin")

        if user.role == Roles.SUPER_ADMIN:
            return qs
        elif user.role == Roles.ADMIN and user.tenant:
            return qs.filter(tenant=user.tenant)
        else:
            return Payment.objects.none()


class SubscriptionViewSet(ReadOnlyModelViewSet):
    """
    Super admin read-only view for monitoring subscriptions across all tenants.
    Regular admins can only view their own tenant's subscription.
    """

    permission_classes = [IsAuthenticated, IsSuperAdminRoleOrAdminRole]
    serializer_class = SubscriptionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {"status": ["exact", "in"]}
    search_fields = ["tenant__name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Super admins see all subscriptions, regular admins see only their tenant's."""
        user = self.request.user
        qs = Subscription.objects.select_related("tenant", "payment")

        if user.role == Roles.SUPER_ADMIN:
            return qs
        elif user.role == Roles.ADMIN and user.tenant:
            return qs.filter(tenant=user.tenant)
        else:
            return Subscription.objects.none()


class WebhookEventViewSet(ReadOnlyModelViewSet):
    """
    Super admin read-only view for monitoring webhook events.
    Only accessible to super admins.
    """

    permission_classes = [IsAuthenticated, IsSuperAdminRole]
    serializer_class = WebhookEventSerializer
    queryset = WebhookEvent.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {"status": ["exact", "in"]}
    ordering = ["-created_at"]
