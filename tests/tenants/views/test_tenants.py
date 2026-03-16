import pytest
from django.urls import reverse
from rest_framework import status

from core.enums import TenantStatus
from tests.factories.tenants import TenantFactory


class TestTenantViewSet:
    @property
    def list_url(self):
        return reverse("tenant-list")

    def detail_url(self, pk):
        return reverse("tenant-detail", kwargs={"pk": pk})

    # --- Super Admin Permissions ---

    def test_superadmin_can_list_all_tenants(self, superadmin_client, tenant):
        """Verify super admin sees all tenants."""
        TenantFactory()
        response = superadmin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert len(response.data["data"]) == 2

    def test_superadmin_can_retrieve_any_tenant(self, superadmin_client):
        """Verify super admin can retrieve any tenant."""
        other_tenant = TenantFactory()
        response = superadmin_client.get(self.detail_url(other_tenant.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(other_tenant.id)

    def test_superadmin_can_create_tenant(self, superadmin_client):
        """Verify super admin can create a tenant."""
        data = {"name": "New Dynamic Tenant", "status": TenantStatus.ACTIVE}
        response = superadmin_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Dynamic Tenant"

    def test_superadmin_can_update_tenant(self, superadmin_client, tenant):
        """Verify super admin can update a tenant."""
        data = {"name": "Updated Name"}
        response = superadmin_client.patch(self.detail_url(tenant.id), data=data)
        assert response.status_code == status.HTTP_200_OK
        tenant.refresh_from_db()
        assert tenant.name == "Updated Name"

    def test_superadmin_can_soft_delete_tenant(self, superadmin_client, tenant):
        """Verify super admin can soft-delete a tenant."""
        response = superadmin_client.delete(self.detail_url(tenant.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        tenant.refresh_from_db()
        assert tenant.status == TenantStatus.INACTIVE

    # --- Tenant Admin Permissions ---

    def test_admin_can_list_only_own_tenant(self, admin_client, admin_user):
        """Verify admin sees only their own tenant."""
        TenantFactory()
        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["data"][0]["id"] == str(admin_user.tenant.id)

    def test_admin_can_retrieve_own_tenant(self, admin_client, admin_user):
        """Verify admin can retrieve their own tenant."""
        response = admin_client.get(self.detail_url(admin_user.tenant.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(admin_user.tenant.id)

    def test_admin_cannot_retrieve_other_tenant(self, admin_client):
        """Verify admin cannot retrieve another tenant."""
        other_tenant = TenantFactory()
        response = admin_client.get(self.detail_url(other_tenant.id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_cannot_create_tenant(self, admin_client):
        """Verify admin cannot create a tenant."""
        data = {"name": "Forbidden Tenant"}
        response = admin_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cannot_update_any_tenant(self, admin_client, admin_user):
        """Verify admin cannot update any tenant (even their own)."""
        data = {"name": "Hacked name"}
        # Own tenant
        response = admin_client.patch(self.detail_url(admin_user.tenant.id), data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Other tenant
        other_tenant = TenantFactory()
        response = admin_client.patch(self.detail_url(other_tenant.id), data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cannot_delete_any_tenant(self, admin_client, admin_user):
        """Verify admin cannot delete any tenant."""
        response = admin_client.delete(self.detail_url(admin_user.tenant.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # --- Unauthenticated ---

    def test_unauthenticated_user_cannot_access_tenants(self, api_client, tenant):
        """Verify anonymous user is blocked."""
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        response = api_client.get(self.detail_url(tenant.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
