import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.enums import TenantStatus


@pytest.fixture(autouse=True)
def mock_auth_dependencies(mocker):
    """
    Provide test-wide mocks for external authentication side effects and return the patched cache.
    
    Mocks verification, OTP, and password-reset email senders' Celery `.delay` calls, refresh-token blacklist/revocation helpers, and disables DRF scoped throttling. The returned mock is the patched `users.views.auth_views.cache` with `get()` defaulting to `0`.
    
    Returns:
        mock_cache (Mock): The patched cache object for use in tests.
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

    def test_user_registration_no_email(self, api_client, tenant):
        data = {"username": "newgamer", "password": "Password123!"}
        headers = {"HTTP_X_TENANT_ID": str(tenant.id)}
        response = api_client.post(self.url, data=data, **headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

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

    def test_user_registration_password_mismatch(self, api_client, tenant):
        """
        Verify that registration fails with HTTP 400 when `password` and `confirm_password` do not match.
        
        Asserts the tenant-scoped registration endpoint rejects mismatched passwords and responds with 400 Bad Request.
        """
        data = {
            "username": "newgamer",
            "email": "gamer@example.com",
            "password": "Password123!",
            "confirm_password": "Password321!",
        }
        headers = {"HTTP_X_TENANT_ID": str(tenant.id)}
        response = api_client.post(self.url, data=data, **headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_registration_existing_verified_user(self, api_client, tenant, user):
        data = {
            "username": "another_user",
            "email": user.email,
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
        headers = {"HTTP_X_TENANT_ID": str(tenant.id)}
        response = api_client.post(self.url, data=data, **headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_registration_missing_tenant_header(self, api_client):
        """
        Checks that user registration is rejected when the tenant header is omitted.
        
        Sends registration data without the required tenant header and asserts the response status is 400 Bad Request and the response contains the text "Tenant header missing".
        """
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
        user.is_verified = False
        user.save()
        token = "valid_token"
        mock_auth_dependencies.get.return_value = user.email

        url = reverse("verify-email")
        response = api_client.get(f"{url}?token={token}")

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_verified is True

    def test_verify_email_user_not_found(self, api_client, mock_auth_dependencies):
        token = "valid_token"
        mock_auth_dependencies.get.return_value = "nonexistent@example.com"

        url = reverse("verify-email")
        response = api_client.get(f"{url}?token={token}")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "User does not exist" in str(response.data)

    def test_verify_email_missing_token(self, api_client, mock_auth_dependencies):
        url = reverse("verify-email")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not mock_auth_dependencies.get.called

    def test_verify_email_invalid_token(self, api_client, mock_auth_dependencies):
        token = "invalid_token"
        url = reverse("verify-email")
        response = api_client.get(f"{url}?token={token}")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert mock_auth_dependencies.get.called

    def test_resend_verification_email_success(
        self, api_client, user, mock_auth_dependencies
    ):
        user.is_verified = False
        user.save()

        url = reverse("resend-verification")
        data = {"email": user.email}
        response = api_client.post(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert "Verification mail sent" in response.data["message"]
        assert mock_auth_dependencies.set.called

    def test_resend_verification_already_verified(
        self, api_client, user, mock_auth_dependencies
    ):
        user.is_verified = True
        user.save()

        url = reverse("resend-verification")
        data = {"email": user.email}
        response = api_client.post(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert not mock_auth_dependencies.get.called

    def test_resend_verification_no_email(self, api_client):
        url = reverse("resend-verification")
        response = api_client.post(url, data={})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in str(response.data)

    def test_resend_verification_already_sent_cache(
        self, api_client, user, mock_auth_dependencies
    ):
        user.is_verified = False
        user.save()

        mock_auth_dependencies.get.return_value = "existing_token"

        url = reverse("resend-verification")
        data = {"email": user.email}
        response = api_client.post(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert "already sent" in str(response.data)
        assert not mock_auth_dependencies.set.called


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

    def test_login_unverified_user(self, api_client, user):
        user.is_verified = False
        user.save()

        data = {"email": user.email, "password": "password"}
        response = api_client.post(self.login_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not verified" in str(response.data).lower()

    def test_login_otp_already_sent(self, api_client, user, mock_auth_dependencies):
        user.is_verified = True
        user.save()

        mock_auth_dependencies.get.return_value = "cached_otp"

        data = {"email": user.email, "password": "password"}
        response = api_client.post(self.login_url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert not mock_auth_dependencies.set.called

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

    def test_verify_otp_missing_fields(self, api_client):
        data = {"email": "test@example.com"}
        response = api_client.post(self.verify_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_otp_expired(self, api_client, user, mock_auth_dependencies):
        user.is_verified = True
        user.save()

        mock_auth_dependencies.get.return_value = None

        data = {"email": user.email, "otp": "123456"}
        response = api_client.post(self.verify_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_step_2_invalid_otp(self, api_client, user, mocker):
        user.is_verified = True
        user.save()

        mocker.patch("users.views.auth_views.verify_otp_hash", return_value=False)

        data = {"email": user.email, "otp": "wrong"}
        response = api_client.post(self.verify_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid OTP" in str(response.data)

    def test_verify_otp_user_not_found(self, api_client, user, mock_auth_dependencies):
        mock_auth_dependencies.get.return_value = "hashed_otp"

        data = {"email": "nonexistent@example.com", "otp": "123456"}
        response = api_client.post(self.verify_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Authentication failed" in str(response.data)

    def test_verify_otp_max_attempts(
        self, api_client, user, mocker, mock_auth_dependencies
    ):
        user.is_verified = True
        user.save()

        mock_auth_dependencies.get.return_value = 5

        data = {"email": user.email, "otp": "any"}

        response = api_client.post(self.verify_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Too many invalid attempts" in str(response.data)
        assert mock_auth_dependencies.delete_many.called


class TestPasswordReset:
    forgot_url = reverse("forgot-password")
    reset_url = reverse("reset-password")

    def test_forgot_password_success(self, api_client, user, mock_auth_dependencies):
        data = {"email": user.email}
        response = api_client.post(self.forgot_url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert "reset link has been sent" in response.data["message"]
        assert mock_auth_dependencies.set.called

    def test_forgot_password_existing_token(
        self, api_client, user, mock_auth_dependencies
    ):
        mock_auth_dependencies.get.return_value = "some_token"
        data = {"email": user.email}
        response = api_client.post(self.forgot_url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert not mock_auth_dependencies.set.called

    def test_forgot_password_non_existent_user(
        self, api_client, mock_auth_dependencies
    ):
        mock_auth_dependencies.get.return_value = None
        data = {"email": "nonexistent@example.com"}
        response = api_client.post(self.forgot_url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert not mock_auth_dependencies.set.called

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

    def test_reset_password_invalid_token(self, api_client, mock_auth_dependencies):
        mock_auth_dependencies.get.return_value = None
        data = {
            "token": "expired",
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }
        response = api_client.post(self.reset_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_password_user_not_found(self, api_client, mock_auth_dependencies):
        mock_auth_dependencies.get.return_value = "ghost@example.com"
        data = {
            "token": "valid_but_no_user",
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }
        response = api_client.post(self.reset_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


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
