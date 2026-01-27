from django.utils import timezone
from rest_framework import serializers

from core.constants import MAX_FREE_USER_GAMES
from core.enums import Roles, Status, TenantStatus
from user_games.models import UserGame, UserGameNote


class UserGameSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating a user's game entry.
    """

    class Meta:
        model = UserGame
        fields = (
            "id",
            "user",
            "tenant_game",
            "platform",
            "status",
            "hours_played",
            "personal_rating",
            "started_on",
            "completed_on",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            "user": {"required": False},
        }

    def validate_status(self, value):
        """
        Ensure the status value is one of the allowed enum choices.
        """
        if value not in Status.values:
            raise serializers.ValidationError(
                f"Invalid status. Allowed values: {Status.values}"
            )
        return value

    def validate_personal_rating(self, value):
        """
        Validate that personal rating is between 0 and 5.
        """
        if value is not None and not 0 <= value <= 5:
            raise serializers.ValidationError(
                "Personal rating must be between 0 and 5."
            )
        return value

    def validate_completed_on(self, value):
        if value is None:
            return value
        present_date = timezone.now().date()
        if value > present_date:
            raise serializers.ValidationError(
                f"Completed date cannot be in the future. (Present Date: {present_date})"
            )
        return value

    def validate_hours_played(self, value):
        if value is not None and value > 100000:
            raise serializers.ValidationError("Hours played cannot exceed 100,000.")
        return value

    def validate_started_on(self, value):
        if value is None:
            return value
        present_date = timezone.now().date()
        if value > present_date:
            raise serializers.ValidationError(
                f"Started date cannot be in the future. (Present Date: {present_date})"
            )
        return value

    def validate(self, attrs):
        """
        Keep `status`, `started_on` and `completed_on` in sync.
        """
        request_user = self.context["request"].user
        instance = self.instance
        user = attrs.get("user") or (instance.user if instance else request_user)
        if request_user.role == Roles.GAMER:
            if user != request_user:
                raise serializers.ValidationError(
                    "Gamers cannot assign games to other users."
                )
            user = request_user

        if request_user.role == Roles.ADMIN:
            if user.tenant != request_user.tenant:
                raise serializers.ValidationError(
                    "Cannot assign a game to a user outside your tenant."
                )

        attrs["user"] = user
        tenant = user.tenant
        attrs["tenant"] = tenant

        # Check if gamer has reached the maximum limit of 10 active games
        # Only applies when creating a new game (not updating) and tenant status is ACTIVE
        if not self.instance and user.role == Roles.GAMER:
            if tenant.status == TenantStatus.ACTIVE:
                # Count active user_games (deleted_at__isnull=True, which is objects.all())
                active_games_count = UserGame.objects.filter(user=user).count()
                if active_games_count >= MAX_FREE_USER_GAMES:
                    raise serializers.ValidationError(
                        f"You have reached the maximum limit of {MAX_FREE_USER_GAMES} active games. "
                        "Please delete some games before adding new ones."
                    )

        status = attrs.get("status", instance.status if instance else None)
        completed_on = attrs.get(
            "completed_on", instance.completed_on if instance else None
        )
        started_on = attrs.get("started_on", instance.started_on if instance else None)
        tenant_game = attrs.get(
            "tenant_game", instance.tenant_game if instance else None
        )
        platform = attrs.get("platform", instance.platform if instance else None)

        if not tenant_game:
            raise serializers.ValidationError("tenant_game is required.")

        if tenant_game.tenant != user.tenant:
            raise serializers.ValidationError("Game does not belong to your tenant.")

        if status == Status.COMPLETED:
            if completed_on is None:
                attrs["completed_on"] = timezone.now().date()
                completed_on = attrs["completed_on"]
        else:
            if completed_on is not None:
                attrs["completed_on"] = None
                completed_on = None

        if status in [Status.PLAYING, Status.COMPLETED, Status.DROPPED]:
            if started_on is None:
                attrs["started_on"] = timezone.now().date()
                started_on = attrs["started_on"]
        else:
            if started_on is not None:
                attrs["started_on"] = None
                started_on = None

        if started_on and completed_on and started_on > completed_on:
            raise serializers.ValidationError(
                "Started date cannot be after completed date."
            )

        if tenant_game and platform:
            if not tenant_game.game.platforms.filter(id=platform.id).exists():
                raise serializers.ValidationError(
                    f"Platform '{platform.name}' is not available for the game '{tenant_game.game.title}'."
                )

            qs = UserGame.objects.filter(
                user=user,
                tenant=user.tenant,
                tenant_game=tenant_game,
                platform=platform,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    f"You already have this game '{tenant_game.game.title}' on platform '{platform.name}'."
                )

        return attrs


class UserGameNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGameNote
        fields = ("id", "note", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        """
        Assign user_game automatically from context.
        Expect context to include 'user_game' set in the ViewSet.
        """
        user_game = self.context.get("user_game")
        if not user_game:
            raise serializers.ValidationError("UserGame not provided in context.")

        return UserGameNote.objects.create(
            user_game=user_game, tenant=user_game.tenant, **validated_data
        )
