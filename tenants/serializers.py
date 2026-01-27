from rest_framework import serializers

from tenants.models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ("id", "name", "status", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value):
        normalized = " ".join(value.split())

        qs = Tenant.objects.filter(name__iexact=normalized)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Tenant with this name already exists.")

        return normalized


class TenantDetailSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField(read_only=True)
    tenant_games_count = serializers.SerializerMethodField(read_only=True)
    user_games_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tenant
        fields = (
            "id",
            "name",
            "status",
            "created_at",
            "updated_at",
            "user_count",
            "tenant_games_count",
            "user_games_count",
        )
        read_only_fields = fields

    def get_user_count(self, obj):
        return obj.users.filter(tenant_id=obj.id).count()

    def get_tenant_games_count(self, obj):
        return obj.tenant_games.filter(tenant_id=obj.id).count()

    def get_user_games_count(self, obj):
        return obj.user_games.filter(tenant_id=obj.id).count()
