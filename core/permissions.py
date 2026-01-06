from rest_framework.permissions import SAFE_METHODS, BasePermission

from core.enums import Roles


class IsAdminRole(BasePermission):
    """
    Allows access only to users with the ADMIN role.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == Roles.ADMIN


class IsAdminOrReadOnly(BasePermission):
    """
    Allows read-only access to all users.
    Write operations are restricted to admin users only.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return request.user.is_authenticated and request.user.role == Roles.ADMIN


class IsAdminReadOnlyOrOwner(BasePermission):
    """
    Admin:
    - Read-only access to all objects

    Gamer:
    - Full access to own objects only
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == Roles.ADMIN:
            return request.method in SAFE_METHODS

        return True

    def has_object_permission(self, request, view, obj):
        if request.user.role == Roles.ADMIN:
            return request.method in SAFE_METHODS

        return obj.user == request.user
