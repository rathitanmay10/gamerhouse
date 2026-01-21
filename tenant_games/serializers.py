from django.db import transaction
from rest_framework import serializers

from catalog.models import Game
from core.enums import Roles
from tenant_games.models import TenantGame


class TenantGameMappingSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request and request.user.role == Roles.ADMIN:
            self.fields.pop("tenant")

    class Meta:
        model = TenantGame
        fields = ("id", "tenant", "game")

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        if user.role == Roles.ADMIN:
            tenant = user.tenant
        else:
            tenant = attrs.get("tenant")

        game = attrs.get("game")

        if TenantGame.objects.filter(tenant=tenant, game=game).exists():
            raise serializers.ValidationError(
                "This game is already mapped to the tenant."
            )
        attrs["tenant"] = tenant

        return attrs

    def create(self, validated_data):
        tenant = validated_data.get("tenant")
        game = validated_data.get("game")

        with transaction.atomic():
            existing = (
                TenantGame.all_objects.select_for_update()
                .filter(tenant=tenant, game=game, deleted_at__isnull=False)
                .first()
            )

            if existing:
                existing.deleted_at = None
                existing.save(update_fields=["deleted_at"])
                return existing

        return super().create(validated_data)


class GameDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = (
            "title",
            "description",
            "release_date",
            "genre",
            "platforms",
        )


class TenantGameSerializer(serializers.ModelSerializer):
    game = GameDetailSerializer(read_only=True)

    class Meta:
        model = TenantGame
        fields = (
            "id",
            "game",
        )
