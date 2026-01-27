from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken


def revoke_access_token(validated_token):
    """
    Revoke the currently authenticated access token using jti + Redis TTL.
    """
    if not validated_token:
        return

    jti = validated_token.get("jti")
    exp = validated_token.get("exp")

    if not jti or not exp:
        return

    now = int(timezone.now().timestamp())
    ttl = exp - now

    if ttl > 0:
        cache.set(f"blacklist:{jti}", "1", timeout=ttl)


def blacklist_refresh_token(refresh_token_str):
    """
    Blacklist a single refresh token (logout).
    """
    token = RefreshToken(refresh_token_str)
    token.blacklist()


def blacklist_all_refresh_tokens_for_user(user):
    """
    Blacklist all outstanding refresh tokens for a user
    (password change, delete account, admin action).
    """
    with transaction.atomic():
        tokens = OutstandingToken.objects.filter(
            user=user,
            expires_at__gt=timezone.now(),
            blacklistedtoken__isnull=True,
        )

        BlacklistedToken.objects.bulk_create(
            (BlacklistedToken(token=token) for token in tokens),
            ignore_conflicts=True,
        )
