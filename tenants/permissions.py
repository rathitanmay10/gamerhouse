from rest_framework.permissions import SAFE_METHODS, BasePermission

from core.enums import Roles


class IsSuperAdminOrTenantAdminGetOwnTenant(BasePermission):
    """
    Tenant endpoint permissions:
    - SUPER_ADMIN: full CRUD
    - ADMIN: GET only, own tenant only
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user = request.user

        if user.role == Roles.SUPER_ADMIN:
            return True

        if user.role == Roles.ADMIN:
            return request.method in SAFE_METHODS

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role == Roles.SUPER_ADMIN:
            return True

        if user.role == Roles.ADMIN:
            return request.method in SAFE_METHODS and obj.id == user.tenant_id

        return False
