import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.enums import TenantStatus


@pytest.fixture(autouse=True)
def mock_auth_dependencies(mocker):
    """
    Mock external side effects like emails and token blacklist/revocation.
    """
    mocker.patch("users.views.auth_views.send_verification_email.delay")
    mocker.patch("users.views.auth_views.send_otp_email.delay")
    mocker.patch("users.views.auth_views.send_password_reset_email.delay")
    mocker.patch("users.views.auth_views.blacklist_all_refresh_tokens_for_user")
    mocker.patch("users.serializers.auth_serializers.revoke_access_token")
    mocker.patch("users.serializers.auth_serializers.blacklist_refresh_token")

    # Disable Throttling globally for these tests
    mocker.patch(
        "rest_framework.throttling.ScopedRateThrottle.allow_request", return_value=True
    )

    mock_cache = mocker.patch("users.views.auth_views.cache")
    mock_cache.get.return_value = 0
    return mock_cache


class TestRegistration:
    url = reverse("tenant-register")

    def test_user_registration_success(
        self, api_client, tenant, mock_auth_dependencies
    ):
        data = {
            "username": "newgamer",
            "email": "gamer@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "first_name": "New",
            "last_name": "Gamer",
        }
        headers = {"HTTP_X_TENANT_ID": str(tenant.id)}
        response = api_client.post(self.url, data=data, **headers)

        assert response.status_code == status.HTTP_201_CREATED
        assert "Registration successful" in response.data["message"]

        assert mock_auth_dependencies.set.called

    def test_user_registration_already_sent(
        self, api_client, tenant, mock_auth_dependencies
    ):
        # Mock that verification mail was already sent
        mock_auth_dependencies.get.return_value = "some_token"
        data = {
            "username": "newgamer",
            "email": "gamer@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
        headers = {"HTTP_X_TENANT_ID": str(tenant.id)}
        response = api_client.post(self.url, data=data, **headers)
        assert response.status_code == status.HTTP_200_OK
        assert "already sent" in response.data["message"]

    def test_user_registration_missing_tenant_header(self, api_client):
        data = {
            "username": "fail",
            "email": "fail@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
        response = api_client.post(self.url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Tenant header missing" in str(response.data)

    def test_verify_email_success(self, api_client, user, mock_auth_dependencies):
        token = "valid_token"
        mock_auth_dependencies.get.return_value = user.email

        url = reverse("verify-email")
        response = api_client.get(f"{url}?token={token}")

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_verified is True


class TestLoginFlow:
    login_url = reverse("login")
    verify_url = reverse("login_verify")

    def test_login_step_1_success(self, api_client, user, mock_auth_dependencies):
        user.is_verified = True
        user.save()

        data = {"email": user.email, "password": "password"}
        response = api_client.post(self.login_url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert "OTP sent" in response.data["message"]
        assert mock_auth_dependencies.set.called

    def test_login_step_2_verify_otp_success(self, api_client, user, mocker):
        user.is_verified = True
        user.save()

        fixed_otp = "123456"
        mocker.patch("users.views.auth_views.verify_otp_hash", return_value=True)

        data = {"email": user.email, "otp": fixed_otp}
        response = api_client.post(self.verify_url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_step_2_invalid_otp(self, api_client, user, mocker):
        user.is_verified = True
        user.save()

        mocker.patch("users.views.auth_views.verify_otp_hash", return_value=False)

        data = {"email": user.email, "otp": "wrong"}
        response = api_client.post(self.verify_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid OTP" in str(response.data)


class TestPasswordReset:
    forgot_url = reverse("forgot-password")
    reset_url = reverse("reset-password")

    def test_forgot_password_success(self, api_client, user, mock_auth_dependencies):
        data = {"email": user.email}
        response = api_client.post(self.forgot_url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert "reset link has been sent" in response.data["message"]
        assert mock_auth_dependencies.set.called

    def test_reset_password_success(self, api_client, user, mock_auth_dependencies):
        token = "valid_reset_token"
        mock_auth_dependencies.get.return_value = user.email

        data = {
            "token": token,
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }
        response = api_client.post(self.reset_url, data=data)

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("NewPassword123!") is True


class TestTokenOperations:
    refresh_url = reverse("token-refresh")
    logout_url = reverse("logout")

    def test_token_refresh_success(self, api_client, user):
        refresh = RefreshToken.for_user(user)

        data = {"refresh": str(refresh)}
        response = api_client.post(self.refresh_url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_token_refresh_inactive_tenant(self, api_client, user):
        user.tenant.status = TenantStatus.INACTIVE
        user.tenant.save()
        refresh = RefreshToken.for_user(user)

        data = {"refresh": str(refresh)}
        response = api_client.post(self.refresh_url, data=data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Tenant is not active" in str(response.data)

    def test_logout(self, authenticated_client, user):
        data = {"refresh": "fake_refresh_token"}
        response = authenticated_client.post(self.logout_url, data=data)
        assert response.status_code == status.HTTP_200_OK
