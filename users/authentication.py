from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.context import set_current_tenant
from core.enums import Roles, TenantStatus


class TenantJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that also:
    - Rejects blacklisted tokens
    - Rejects users without tenants
    - Rejects users whose tenant is inactive
    - Allows SUPER_ADMIN bypass
    - Sets tenant in thread-local storage for global access
    """

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None  # token missing or invalid

        user, validated_token = result

        # Check if token is blacklisted
        jti = validated_token.get("jti")
        if cache.get(f"blacklist:{jti}"):
            raise AuthenticationFailed("Token has been revoked")

        # SUPER_ADMIN bypass - no tenant required
        if user.role == Roles.SUPER_ADMIN:
            return user, validated_token

        # Must have a tenant
        if not getattr(user, "tenant", None):
            raise AuthenticationFailed("User is not associated with any tenant.")

        # Tenant must be ACTIVE
        if user.tenant.status != TenantStatus.ACTIVE:
            raise AuthenticationFailed("Tenant is not active. Please contact support.")

        # Set tenant in thread-local storage for global access
        self._set_tenant_context(user.tenant)

        return user, validated_token

    def _set_tenant_context(self, tenant):
        """Set tenant in thread-local storage for global access throughout request."""
        set_current_tenant(tenant)
