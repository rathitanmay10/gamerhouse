from django.urls import reverse
from rest_framework import status

from tests.factories.payments import PaymentFactory, SubscriptionFactory
from tests.factories.tenants import TenantFactory


class TestPaymentViewSet:
    @property
    def url(self):
        """
        Builds the endpoint URL for the admin payment list view.
        
        Returns:
            url (str): The URL for the admin payment list endpoint.
        """
        return reverse("admin-payment-list")

    def test_superadmin_can_list_all_payments(self, superadmin_client, tenant):
        """Verify super admin sees all payments across tenets."""
        other_tenant = TenantFactory()
        PaymentFactory.create_batch(2, tenant=tenant)
        PaymentFactory.create_batch(3, tenant=other_tenant)

        response = superadmin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5

    def test_admin_can_list_only_own_tenant_payments(
        self, admin_client, admin_user, tenant
    ):
        """Verify admin can only see payments for their own tenant."""
        other_tenant = TenantFactory()
        PaymentFactory.create_batch(2, tenant=tenant)
        PaymentFactory.create_batch(3, tenant=other_tenant)

        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        for payment in response.data["data"]:
            assert str(payment["tenant"]) == str(tenant.id)

    def test_gamer_cannot_list_payments(self, authenticated_client):
        """
        Verify that a non-admin authenticated user cannot list payments via the admin payments endpoint.
        
        Asserts the response status code is HTTP 403 Forbidden.
        """
        response = authenticated_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSubscriptionViewSet:
    @property
    def url(self):
        """
        Builds the URL for the admin subscription list endpoint.
        
        Returns:
            str: The URL path for the admin subscription list view.
        """
        return reverse("admin-subscription-list")

    def test_superadmin_can_list_all_subscriptions(self, superadmin_client, tenant):
        """Verify that a superadmin can list subscriptions for all tenants."""
        t1, t2, t3, t4 = TenantFactory.create_batch(4)
        SubscriptionFactory(tenant=tenant)
        SubscriptionFactory(tenant=t1)
        SubscriptionFactory(tenant=t2)
        SubscriptionFactory(tenant=t3)
        SubscriptionFactory(tenant=t4)

        response = superadmin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5

    def test_admin_can_list_only_own_tenant_subscriptions(
        self, admin_client, admin_user, tenant
    ):
        """Verify admin can only see subscriptions for their own tenant."""
        t1, t2, t3 = TenantFactory.create_batch(3)
        SubscriptionFactory(tenant=tenant)
        SubscriptionFactory(tenant=t1)
        SubscriptionFactory(tenant=t2)
        SubscriptionFactory(tenant=t3)

        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        for sub in response.data["data"]:
            assert str(sub["tenant"]) == str(tenant.id)


class TestWebhookEventViewSet:
    @property
    def url(self):
        """
        Builds the URL for the admin webhook event list endpoint.
        
        Returns:
            url (str): The URL for the admin webhook list view.
        """
        return reverse("admin-webhook-list")

    def test_superadmin_can_list_webhook_events(self, superadmin_client):
        """Verify super admin sees webhook events."""
        from payments.models import WebhookEvent

        WebhookEvent.objects.create(
            event_id="test1", event_type="payment.captured", payload={}
        )
        WebhookEvent.objects.create(
            event_id="test2", event_type="payment.failed", payload={}
        )

        response = superadmin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_admin_cannot_list_webhook_events(self, admin_client):
        """Verify regular tenant admin cannot access webhook events."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
