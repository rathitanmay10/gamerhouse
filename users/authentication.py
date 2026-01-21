from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class BlacklistJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None

        user, validated_token = result
        jti = validated_token.get("jti")

        if cache.get(f"blacklist:{jti}"):
            raise AuthenticationFailed("Token has been revoked")

        return user, validated_token
