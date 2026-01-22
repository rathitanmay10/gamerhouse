from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.enums import Roles, TenantStatus


class TenantJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that also:
    - Rejects blacklisted tokens
    - Rejects users without tenants
    - Rejects users whose tenant is inactive
    - Allows SUPER_ADMIN bypass
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

        # SUPER_ADMIN bypass
        if user.role == Roles.SUPER_ADMIN:
            return user, validated_token

        # Must have a tenant
        if not getattr(user, "tenant", None):
            raise AuthenticationFailed("User is not associated with any tenant.")

        # Tenant must be ACTIVE
        if user.tenant.status != TenantStatus.ACTIVE:
            raise AuthenticationFailed("Tenant is not active. Please contact support.")

        return user, validated_token
