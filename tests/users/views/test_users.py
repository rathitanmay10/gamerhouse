import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.enums import Roles
from tests.factories.tenants import TenantFactory
from tests.factories.users import UserFactory


@pytest.fixture(autouse=True)
def mock_external_dependencies(mocker):
    """
    Mock common external dependencies globally for all tests in this file.
    """
    mocker.patch("users.views.user_views.cache")
    mocker.patch("users.views.user_views.send_verification_email.delay")
    mocker.patch("users.views.user_views.soft_delete_user_data.delay")
    mocker.patch(
        "users.serializers.user_serializers.blacklist_all_refresh_tokens_for_user"
    )
    mocker.patch("users.serializers.user_serializers.revoke_access_token")


class TestUserViewSet:
    """
    Tests for UserViewSet administrative actions.
    """

    @property
    def list_url(self):
        return reverse("users-list")

    def detail_url(self, pk):
        return reverse("users-detail", kwargs={"pk": pk})

    def restore_url(self, pk):
        return reverse("users-restore-user", kwargs={"pk": pk})

    def test_superadmin_can_list_admins(self, superadmin_client, tenant):
        """Verify super admin sees only admins across all tenants."""
        other_tenant = TenantFactory()
        UserFactory(tenant=other_tenant, role=Roles.ADMIN)
        UserFactory(tenant=tenant, role=Roles.GAMER)

        response = superadmin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        for user_data in response.data["data"]:
            assert user_data["role"] == Roles.ADMIN

    def test_admin_can_list_tenant_users(self, admin_client, admin_user, tenant):
        """Verify admin sees only their own tenant's users."""
        UserFactory(tenant=tenant, role=Roles.GAMER)
        other_tenant = TenantFactory()
        UserFactory(tenant=other_tenant, role=Roles.GAMER)

        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        for user_data in response.data["data"]:
            assert str(user_data["tenant"]) == str(tenant.id)

    def test_admin_can_create_gamer_user(self, admin_client, tenant, mocker):
        """Verify admin can create a gamer user in their tenant."""
        mock_email = mocker.patch(
            "users.views.user_views.send_verification_email.delay"
        )
        mocker.patch("users.views.user_views.cache.get", return_value=None)

        data = {
            "username": "newgamer",
            "email": "gamer@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
        response = admin_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        mock_email.assert_called_once()

    def test_superadmin_can_create_admin_user(self, superadmin_client, tenant, mocker):
        """Verify superadmin can create an admin for any tenant."""
        mock_email = mocker.patch(
            "users.views.user_views.send_verification_email.delay"
        )
        mocker.patch("users.views.user_views.cache.get", return_value=None)

        data = {
            "username": "newadmin",
            "email": "admin@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "tenant": str(tenant.id),
        }
        response = superadmin_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        mock_email.assert_called_once()

    def test_admin_cannot_delete_self(self, admin_client, admin_user):
        """Verify admin cannot delete their own account via UserViewSet."""
        response = admin_client.delete(self.detail_url(admin_user.id))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Admins cannot delete their own account" in str(response.data)

    def test_admin_can_soft_delete_other_user(self, admin_client, tenant, mocker):
        """Verify admin can soft-delete a gamer in their tenant."""
        mocker.patch("users.views.user_views.soft_delete_user_data.delay")
        target_user = UserFactory(tenant=tenant, role=Roles.GAMER)
        response = admin_client.delete(self.detail_url(target_user.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        target_user.refresh_from_db()
        assert target_user.is_active is False
        assert target_user.deleted_at is not None

    def test_admin_can_restore_user(self, admin_client, tenant):
        """Verify admin can restore a soft-deleted user."""
        target_user = UserFactory(tenant=tenant, role=Roles.GAMER, is_active=False)
        target_user.delete()

        response = admin_client.post(self.restore_url(target_user.id))
        assert response.status_code == status.HTTP_200_OK
        target_user.refresh_from_db()
        assert target_user.is_active is True
        assert target_user.deleted_at is None


class TestMeAPIView:
    """
    Tests for authenticated user self-actions.
    """

    url = reverse("me")

    def test_user_can_retrieve_self(self, authenticated_client, user):
        response = authenticated_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        if "data" in response.data:
            assert response.data["data"]["id"] == str(user.id)
        else:
            assert response.data["id"] == str(user.id)

    def test_user_can_update_self(self, authenticated_client, user):
        data = {"first_name": "NewName"}
        response = authenticated_client.patch(self.url, data=data)
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "NewName"

    def test_user_can_delete_self(self, authenticated_client, user, mocker):
        mocker.patch("users.views.user_views.soft_delete_user_data.delay")

        refresh = RefreshToken.for_user(user)
        data = {"refresh": str(refresh)}

        response = authenticated_client.delete(self.url, data=data)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        user.refresh_from_db()
        assert user.deleted_at is not None
        assert user.is_active is False


class TestChangePasswordAPIView:
    """
    Tests for password change.
    """

    url = reverse("change-password")

    def test_user_can_change_password(self, authenticated_client, user, mocker):
        mock_blacklist = mocker.patch(
            "users.serializers.user_serializers.blacklist_all_refresh_tokens_for_user"
        )
        mock_revoke = mocker.patch(
            "users.serializers.user_serializers.revoke_access_token"
        )

        data = {
            "old_password": "password",
            "new_password": "NewPass456!",
        }
        response = authenticated_client.post(self.url, data=data)
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("NewPass456!") is True
        mock_blacklist.assert_called_once_with(user)
        mock_revoke.assert_called_once()
