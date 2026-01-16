from rest_framework import serializers

from catalog.models import Platform


class PlatformSerializer(serializers.ModelSerializer):
    """
    Serializer for Genre reference data.
    """

    class Meta:
        model = Platform
        fields = ("id", "name", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value):
        normalized = " ".join(value.split())

        qs = Platform.objects.filter(name__iexact=normalized)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Platform with this name already exists.",
                code="unique",
            )

        return normalized
