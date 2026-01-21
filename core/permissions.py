from rest_framework.permissions import SAFE_METHODS, BasePermission

from core.enums import Roles


class IsSuperAdminRoleOrAdminRole(BasePermission):
    """
    Allows access only to users with the SUPER ADMIN and ADMIN role.
    """

    def has_permission(self, request, view):
        return request.user.role in [Roles.SUPER_ADMIN, Roles.ADMIN]


class IsSuperAdminOrAdminReadOnly(BasePermission):
    """
    Allows read-only access to all admins.
    Write operations are restricted to super admin users only.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS and request.user.role in [
            Roles.SUPER_ADMIN,
            Roles.ADMIN,
        ]:
            return True

        return request.user.is_authenticated and request.user.role == Roles.SUPER_ADMIN


class IsSuperAdminOrReadOnly(BasePermission):
    """
    Allows read-only access to all users.
    Write operations are restricted to super admin users only.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return request.user.is_authenticated and request.user.role == Roles.SUPER_ADMIN
