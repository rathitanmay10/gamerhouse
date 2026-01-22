from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.views import TokenRefreshView

from core.constants import (
    EMAIL_VERIFY_TTL,
    LOGIN_OTP_TTL,
    MAX_OTP_ATTEMPTS,
    PASSWORD_RESET_TTL,
)
from core.enums import Roles, TenantStatus
from users.helper.auth_tokens import blacklist_all_refresh_tokens_for_user
from users.helper.cache_keys import (
    login_otp_attempts_key,
    login_otp_key,
    reset_email_key,
    reset_token_key,
    verify_email_key,
    verify_token_key,
)
from users.helper.otp_token import (
    generate_email_verification_token,
    generate_otp,
    generate_otp_hash,
    generate_password_reset_token,
    verify_otp_hash,
)
from users.serializers import (
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
)
from users.tasks import (
    send_otp_email,
    send_password_reset_email,
    send_verification_email,
)

User = get_user_model()


def send_otp(email: str):
    """
    Generates OTP, stores hashed OTP in cache, and sends email.
    """
    otp = generate_otp()
    hashed_otp = generate_otp_hash(otp)
    cache.set(login_otp_key(email), hashed_otp, timeout=LOGIN_OTP_TTL)
    # otp_key = login_otp_key(email)
    # print("Retrieved OTP:", cache.get(otp_key))
    send_otp_email.delay(email, otp)
    return otp


class RegisterAPIView(APIView):
    """
    Public registration endpoint for normal users (gamers).

    Creates an unverified user under a tenant
    and sends an email verification link.
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, tenant_id):
        serializer = RegisterSerializer(
            data=request.data,
            context={"tenant_id": tenant_id},
        )
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()

        if cache.get(verify_email_key(email)):
            return Response(
                {"message": "Verification mail already sent. Verify or resend."},
                status=status.HTTP_200_OK,
            )

        serializer.save()
        token = generate_email_verification_token(email)
        cache.set(verify_token_key(token), email, timeout=EMAIL_VERIFY_TTL)
        cache.set(verify_email_key(email), token, timeout=EMAIL_VERIFY_TTL)
        send_verification_email.delay(email, token)

        return Response(
            {"message": "Registration successful. Please verify your email."},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def get(self, request):
        token = request.query_params.get("token")
        if not token:
            raise ValidationError("Token is required")

        email = cache.get(verify_token_key(token))
        if not email:
            raise ValidationError("Invalid or expired token")

        try:
            user = User.all_objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("User does not exist")

        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        cache.delete(verify_token_key(token))
        cache.delete(verify_email_key(email))

        return Response(
            {"message": "Email verified successfully"},
            status=status.HTTP_200_OK,
        )


class ResendVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            raise ValidationError({"email": "This field is required."})

        email = email.lower()

        user = User.all_objects.filter(email=email).first()

        if not user or user.is_verified:
            return Response(
                {"message": "Verification mail sent."},
                status=status.HTTP_200_OK,
            )

        if cache.get(verify_email_key(email)):
            return Response(
                {"message": "Verification mail already sent. Please check your inbox."},
                status=status.HTTP_200_OK,
            )

        token = generate_email_verification_token(email)
        cache.set(verify_token_key(token), email, timeout=EMAIL_VERIFY_TTL)
        cache.set(verify_email_key(email), token, timeout=EMAIL_VERIFY_TTL)

        send_verification_email.delay(email, token)

        return Response(
            {"message": "Verification mail sent."},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    """
    Authenticate a user and issue JWT tokens.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        if cache.get(login_otp_key(email)):
            return Response(
                {"message": "OTP already sent to email, verify or resend otp."},
                status=status.HTTP_200_OK,
            )
        send_otp(email)
        return Response(
            {"message": "OTP sent to email."},
            status=status.HTTP_200_OK,
        )


class LoginVerifyAPIView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        email = request.data.get("email", "").lower()
        otp = request.data.get("otp")
        if not email or not otp:
            raise ValidationError("Email and OTP required.")

        otp_key = login_otp_key(email)
        attempts_key = login_otp_attempts_key(email)

        cached_otp = cache.get(otp_key)
        if cached_otp is None:
            cache.delete(attempts_key)
            raise ValidationError("OTP expired. Please request a new one.")

        try:
            user = User.objects.get(
                email=email,
                is_active=True,
                is_verified=True,
            )
        except User.DoesNotExist:
            raise ValidationError("Authentication failed. Please try again.")

        current_attempts = cache.get(attempts_key) or 0
        current_attempts = int(current_attempts)

        if current_attempts >= MAX_OTP_ATTEMPTS:
            cache.delete_many([otp_key, attempts_key])
            raise ValidationError("Too many invalid attempts. OTP expired.")

        if not verify_otp_hash(otp, cached_otp):
            current_attempts += 1
            cache.set(attempts_key, current_attempts, timeout=LOGIN_OTP_TTL)
            remaining = MAX_OTP_ATTEMPTS - current_attempts
            if remaining <= 0:
                cache.delete_many([otp_key, attempts_key])
                raise ValidationError("Too many invalid attempts. OTP expired.")
            raise ValidationError(f"Invalid OTP. {remaining} attempt(s) remaining.")

        cache.delete_many([otp_key, attempts_key])
        refresh = CustomTokenObtainPairSerializer().get_token(user)
        return Response(
            {"refresh": str(refresh), "access": str(refresh.access_token)},
            status=status.HTTP_200_OK,
        )


class ResendLoginOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            raise ValidationError({"email": "This field is required."})
        email = email.lower()
        if cache.get(login_otp_key(email)):
            return Response(
                {"message": "OTP already sent to email, please wait before resending."},
                status=status.HTTP_200_OK,
            )
        send_otp(email)
        return Response(
            {"message": "OTP sent to email."},
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    """
    Log out the authenticated user.

    Invalidates the provided refresh token.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_200_OK)


class TenantTokenRefreshView(TokenRefreshView):
    """
    Overrides token refresh to enforce tenant status.
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            from rest_framework_simplejwt.tokens import AccessToken

            access_token_str = response.data.get("access")
            token = AccessToken(access_token_str)
            user_id = token["user_id"]

            from users.models import User

            user = User.objects.select_related("tenant").get(id=user_id)

            if user.role != Roles.SUPER_ADMIN:
                if not user.tenant:
                    raise InvalidToken("User is not associated with any tenant.")
                if user.tenant.status != TenantStatus.ACTIVE:
                    raise InvalidToken("Tenant is not active. Please contact support.")

        return response


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()

        existing_token = cache.get(reset_email_key(email))
        if existing_token:
            return Response(
                {"message": "A reset link has been sent."},
                status=status.HTTP_200_OK,
            )
        user_exists = User.objects.filter(email=email).exists()
        if not user_exists:
            return Response(
                {"message": "A reset link has been sent."},
                status=status.HTTP_200_OK,
            )

        token = generate_password_reset_token(email)
        cache.set(reset_token_key(token), email, timeout=PASSWORD_RESET_TTL)
        cache.set(reset_email_key(email), token, timeout=PASSWORD_RESET_TTL)
        send_password_reset_email.delay(email, token)

        return Response(
            {"message": "A reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        email = cache.get(reset_token_key(token))
        if not email:
            raise ValidationError("Invalid or expired token")
        user = User.objects.filter(email=email, is_active=True).first()
        if not user:
            raise ValidationError("Invalid or expired token")
        with transaction.atomic():
            user.set_password(serializer.validated_data["password"])
            user.save(update_fields=["password"])
            cache.delete(reset_token_key(token))
            cache.delete(reset_email_key(email))
            blacklist_all_refresh_tokens_for_user(user)
        return Response(
            {"message": "Password reset successful"},
            status=status.HTTP_200_OK,
        )
