from rest_framework.permissions import SAFE_METHODS, BasePermission

from core.enums import Roles


class TenantGamePermission(BasePermission):
    """
    Permissions:
    - SUPER_ADMIN: full access
    - ADMIN: CRUD within own tenant
    - GAMER: read-only within own tenant
    """

    def has_permission(self, request, view):
        role = request.user.role

        if role in [Roles.SUPER_ADMIN, Roles.ADMIN]:
            return True

        if role == Roles.GAMER:
            return request.method in SAFE_METHODS

        return False

    def has_object_permission(self, request, view, obj):
        role = request.user.role

        if role == Roles.SUPER_ADMIN:
            return True

        if role == Roles.ADMIN:
            return obj.tenant_id == request.user.tenant_id

        if role == Roles.GAMER:
            return (
                request.method in SAFE_METHODS
                and obj.tenant_id == request.user.tenant_id
            )

        return False
