from rest_framework.permissions import BasePermission, SAFE_METHODS
from core.enums import Roles


class IsAdminRole(BasePermission):
    """
    Allows access only to users with the `admin` role,
    as declared in the JWT access token.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.auth
            and request.auth.get("role") == Roles.ADMIN
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Allows read-only access to all users.
    Write operations are restricted to admin users only.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated
            and request.auth
            and request.auth.get("role") == Roles.ADMIN
        )
