from django.utils import timezone
from rest_framework import serializers

from core.enums import Status
from games.models import Game


class GameSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating a user's game entry.
    """

    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Game
        fields = (
            "id",
            "user",
            "platform",
            "genre",
            "title",
            "description",
            "status",
            "hours_played",
            "personal_rating",
            "notes",
            "completed_at",
            "created_at",
            "updated_at",
            "deleted_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at", "deleted_at")

    def validate_title(self, value):
        request = self.context.get("request")
        user = request.user
        normalized = " ".join(value.split())
        qs = Game.objects.filter(user=user, title__iexact=normalized)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Game with this title already exists.",
                code="unique",
            )
        return normalized

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

    def validate_completed_at(self, value):
        if value is None:
            return value
        present_date = timezone.now().date()
        if value > present_date:
            raise serializers.ValidationError(
                f"Completed at cannot be in the future. (Present Date: {present_date})"
            )
        return value

    def validate(self, attrs):
        """
        Keep `status` and `completed_at` in sync.

        - completed_at is only allowed when status is COMPLETED
        - Auto-set completed_at when status becomes COMPLETED
        - Clear completed_at for all other statuses
        """
        instance = self.instance

        status = attrs.get(
            "status",
            instance.status if instance else None,
        )

        completed_at = attrs.get(
            "completed_at",
            instance.completed_at if instance else None,
        )

        if status == Status.COMPLETED:
            if completed_at is None:
                attrs["completed_at"] = timezone.now().date()
        else:
            if completed_at is not None:
                attrs["completed_at"] = None

        return attrs
