from rest_framework.permissions import BasePermission

from core.enums import Roles


class IsTenantAdminOrGamer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.role in [Roles.ADMIN, Roles.GAMER]

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == Roles.ADMIN:
            return obj.tenant == user.tenant

        return (
            user.role == Roles.GAMER
            and obj.user == request.user
            and obj.tenant == user.tenant
        )
