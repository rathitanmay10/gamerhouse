from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from core.constants import EMAIL_VERIFY_TTL
from core.enums import Roles, UserStatus
from core.permissions import IsSuperAdminRoleOrAdminRole
from users.helper.auth_tokens import (
    blacklist_all_refresh_tokens_for_user,
    revoke_access_token,
)
from users.helper.cache_keys import verify_email_key, verify_token_key
from users.helper.otp_token import generate_email_verification_token
from users.serializers import (
    ChangePasswordSerializer,
    SelfUserSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from users.tasks import send_verification_email, soft_delete_user_data

User = get_user_model()


class UserViewSet(ModelViewSet):
    """
    Admin-only endpoints for managing user accounts.

    Supports listing, retrieving, updating, and deleting users.
    User deletion revokes all issued JWTs for immediate access removal.
    """

    permission_classes = [IsSuperAdminRoleOrAdminRole]
    http_method_names = ["get", "post", "patch", "delete", "options", "head"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer

        return UserSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == Roles.SUPER_ADMIN:
            qs = User.all_objects.filter(role=Roles.ADMIN)
        elif user.role == Roles.ADMIN:
            qs = (
                User.all_objects.filter(tenant_id=user.tenant_id)
                .exclude(role=Roles.SUPER_ADMIN)
                .exclude(pk=user.pk)
            )
        else:
            return User.objects.none()

        status_param = self.request.query_params.get("status")

        if status_param == UserStatus.DELETED:
            return qs.filter(deleted_at__isnull=False)

        if status_param == UserStatus.ACTIVE:
            return qs.filter(deleted_at__isnull=True)

        return qs

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        if cache.get(verify_email_key(email)):
            return Response(
                {"message": "Verification mail already sent. Verify or resend."},
                status=status.HTTP_200_OK,
            )
        serializer.save()
        token = generate_email_verification_token(email)
        cache.set(key=verify_token_key(token), value=email, timeout=EMAIL_VERIFY_TTL)
        cache.set(key=verify_email_key(email), value=token, timeout=EMAIL_VERIFY_TTL)
        send_verification_email.delay(email, token)
        return Response(
            {"message": "Verification mail sent."}, status=status.HTTP_201_CREATED
        )

    @transaction.atomic
    def perform_destroy(self, instance):
        """
        Soft-delete the user and revoke all outstanding JWTs.
        """
        if instance == self.request.user:
            raise ValidationError("Admins cannot delete their own account")

        blacklist_all_refresh_tokens_for_user(instance)
        transaction.on_commit(lambda: soft_delete_user_data.delay(instance.id))
        instance.delete()

    @transaction.atomic
    @action(methods=["post"], detail=True, url_path="restore-user")
    def restore_user(self, request, pk):
        user = self.get_object()
        try:
            user.is_active = True
            user.deleted_at = None
            user.save(update_fields=["is_active", "deleted_at"])

            return Response(
                {"message": "User restored successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeAPIView(APIView):
    """
    Self-service endpoint for the authenticated user.

    Allows viewing, updating, and deleting the user's own account.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = SelfUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = SelfUserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request):
        """
        Delete the authenticated user's account.

        Requires a valid refresh token belonging to the user.
        """
        if request.user.role == Roles.ADMIN or request.user.role == Roles.SUPER_ADMIN:
            raise PermissionDenied("Admin accounts cannot be deleted via this endpoint")
        refresh = request.data.get("refresh")
        if not refresh:
            raise ValidationError({"refresh": "Refresh token required"})

        try:
            token = RefreshToken(refresh)
            if str(token["user_id"]) != str(request.user.id):
                raise PermissionDenied("Token does not belong to authenticated user")
            token.blacklist()
        except TokenError:
            raise ValidationError({"refresh": "Invalid or expired refresh token"})
        revoke_access_token(request.auth)
        blacklist_all_refresh_tokens_for_user(request.user)
        transaction.on_commit(lambda: soft_delete_user_data.delay(request.user.id))
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordAPIView(APIView):
    """
    Change the authenticated user's password.

    Verifies the current password and updates it to a new value.
    On success, no response body is returned.
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(None, status=status.HTTP_200_OK)
