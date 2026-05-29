from django.db import transaction
from django.utils import timezone
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
            "id",
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


class TenantGameBulkAddSerializer(serializers.Serializer):
    tenant = serializers.UUIDField(required=False)
    games = serializers.ListField(child=serializers.UUIDField(), required=False)
    platforms = serializers.ListField(child=serializers.UUIDField(), required=False)
    genres = serializers.ListField(child=serializers.UUIDField(), required=False)
    exclude_games = serializers.ListField(child=serializers.UUIDField(), required=False)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        if user.role == Roles.SUPER_ADMIN:
            tenant_id = attrs.get("tenant")
            if not tenant_id:
                raise serializers.ValidationError(
                    {"tenant": "Tenant is required for super admin."}
                )
        else:
            attrs["tenant"] = user.tenant.id

        if not any(attrs.get(k) for k in ("games", "platforms", "genres")):
            raise serializers.ValidationError(
                "At least one of games, platforms, or genres is required."
            )

        return attrs

    def create(self, validated_data):
        tenant_id = validated_data["tenant"]

        game_ids = set(validated_data.get("games", []))
        platform_ids = validated_data.get("platforms", [])
        genre_ids = validated_data.get("genres", [])
        exclude_ids = set(validated_data.get("exclude_games", []))

        game_qs = Game.objects.all()

        if platform_ids and genre_ids:
            derived_qs = game_qs.filter(
                platforms__id__in=platform_ids,
                genre__id__in=genre_ids,
            )
        elif platform_ids:
            derived_qs = game_qs.filter(platforms__id__in=platform_ids)
        elif genre_ids:
            derived_qs = game_qs.filter(genre__id__in=genre_ids)
        else:
            derived_qs = Game.objects.none()

        derived_ids = set(
            derived_qs.exclude(id__in=exclude_ids).values_list("id", flat=True)
        )

        final_game_ids = (game_ids | derived_ids) - exclude_ids

        if not final_game_ids:
            return {"created": 0, "restored": 0, "total": 0}

        with transaction.atomic():
            existing_qs = TenantGame.all_objects.select_for_update().filter(
                tenant_id=tenant_id,
                game_id__in=final_game_ids,
            )

            existing_by_game = {tg.game_id: tg for tg in existing_qs}

            to_restore = []
            to_create = []

            for game_id in final_game_ids:
                tg = existing_by_game.get(game_id)
                if tg:
                    if tg.deleted_at:
                        tg.deleted_at = None
                        to_restore.append(tg)
                else:
                    to_create.append(
                        TenantGame(
                            tenant_id=tenant_id,
                            game_id=game_id,
                        )
                    )

            if to_restore:
                TenantGame.all_objects.bulk_update(to_restore, ["deleted_at"])

            if to_create:
                TenantGame.objects.bulk_create(
                    to_create,
                    ignore_conflicts=True,
                )

        return {
            "created": len(to_create),
            "restored": len(to_restore),
            "total": len(to_create) + len(to_restore),
        }


class TenantGameBulkDeleteSerializer(serializers.Serializer):
    tenant = serializers.UUIDField(required=False)
    tenant_games = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )

    def validate(self, attrs):
        """
        Validate and normalize tenant information for the bulk-delete operation.
        
        If the requesting user is a super admin, require that `attrs` include a `tenant` key; otherwise set `attrs["tenant"]` to the current user's `tenant_id` and return the modified attributes.
        
        Parameters:
            attrs (dict): Incoming validated data from the serializer.
        
        Returns:
            dict: The validated and possibly augmented `attrs` mapping with `tenant` ensured.
        
        Raises:
            serializers.ValidationError: If the user is a super admin and `tenant` is not provided in `attrs`.
        """
        request = self.context["request"]
        user = request.user

        if user.role == Roles.SUPER_ADMIN:
            if not attrs.get("tenant"):
                raise serializers.ValidationError(
                    {"tenant": "Tenant is required for super admin."}
                )
        else:
            attrs["tenant"] = user.tenant_id
        return attrs

    def create(self, validated_data):
        """
        Soft-delete TenantGame mappings for a tenant by setting their `deleted_at` timestamp.
        
        Parameters:
            validated_data (dict): Expected keys:
                - tenant (UUID): ID of the tenant whose mappings will be deleted.
                - tenant_games (list[UUID]): List of TenantGame record IDs to soft-delete.
        
        Returns:
            int: Number of TenantGame rows updated (mappings marked as deleted).
        """
        tenant_id = validated_data["tenant"]
        tenant_game_ids = validated_data["tenant_games"]
        deleted = TenantGame.objects.filter(
            id__in=tenant_game_ids,
            tenant_id=tenant_id,
        ).update(deleted_at=timezone.now())
        return deleted
