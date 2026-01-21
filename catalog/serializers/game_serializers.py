from rest_framework import serializers

from catalog.models import Game, Genre, Platform


class GameSerializer(serializers.ModelSerializer):
    """
    Serializer for Games
    """

    class Meta:
        model = Game
        fields = (
            "id",
            "title",
            "description",
            "release_date",
            "genre",
            "platforms",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_title(self, value):
        normalized = " ".join(value.split())

        qs = Game.objects.filter(title__iexact=normalized)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Game with this name already exists.",
                code="unique",
            )

        return normalized
