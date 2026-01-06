from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from core.enums import Roles
from core.permissions import IsAdminRole
from users.serializers import (
    AdminUserSerializer,
    ChangePasswordSerializer,
    SelfUserSerializer,
)

User = get_user_model()


class AdminUserViewSet(ModelViewSet):
    """
    Admin-only endpoints for managing user accounts.

    Supports listing, retrieving, updating, and deleting users.
    User deletion revokes all issued JWTs for immediate access removal.
    """

    permission_classes = [IsAdminRole]
    serializer_class = AdminUserSerializer
    http_method_names = ["get", "patch", "delete", "options", "head"]

    def get_queryset(self):
        """
        Optionally filter users by deletion status.

        Query params:
        - status=active   → non-deleted users
        - status=deleted  → soft-deleted users
        """
        qs = User.all_objects.all()
        status_param = self.request.query_params.get("status")

        if status_param == "deleted":
            return qs.filter(deleted_at__isnull=False)
        if status_param == "active":
            return qs.filter(deleted_at__isnull=True)

        return qs

    @transaction.atomic
    def perform_destroy(self, instance):
        """
        Soft-delete the user and revoke all outstanding JWTs.
        """
        if instance == self.request.user:
            raise ValidationError("Admins cannot delete their own account")

        tokens = OutstandingToken.objects.filter(user=instance)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
        instance.delete()


class MeAPIView(APIView):
    """
    Self-service endpoint for the authenticated user.

    Allows viewing, updating, and deleting the user's own account.
    """

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
        if request.user.role == Roles.ADMIN:
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

        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordAPIView(APIView):
    """
    Change the authenticated user's password.

    Verifies the current password and updates it to a new value.
    On success, no response body is returned.
    """

    def post(self, request):
        serializer = ChangePasswordSerializer(user=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
