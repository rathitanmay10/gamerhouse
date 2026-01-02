from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from core.permissions import IsAdminRole
from users.serializers.admin import AdminUserSerializer

User = get_user_model()


class AdminUserViewSet(ModelViewSet):
    """
    Admin user management endpoints.

    Allows admins to:
    - List users
    - Retrieve a specific user
    - Partially update user details
    - Delete users

    When a user is deleted, all outstanding JWTs issued to that user
    are blacklisted to immediately revoke access.
    """

    permission_classes = [IsAdminRole]
    queryset = User.all_objects.all()
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

    def perform_destroy(self, instance):
        """
        Revoke all active JWTs for the user and delete the account.

        All outstanding access and refresh tokens associated with the
        user are blacklisted before deletion to prevent further use.
        """

        tokens = OutstandingToken.objects.filter(user=instance)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
        instance.delete()
