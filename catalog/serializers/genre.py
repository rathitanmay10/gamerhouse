from rest_framework import serializers

from catalog.models import Genre


class GenreSerializer(serializers.ModelSerializer):
    """
    Serializer for Genre reference data.
    """

    class Meta:
        model = Genre
        fields = ("id", "name", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value):
        normalized = " ".join(value.split())

        qs = Genre.objects.filter(name__iexact=normalized)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Genre with this name already exists.",
                code="unique",
            )

        return normalized
