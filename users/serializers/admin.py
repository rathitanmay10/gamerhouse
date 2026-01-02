from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer for administrative user state management.

    Allows admins to enable, disable, or restore users.
    All identity and profile fields are read-only.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "deleted_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "created_at",
            "updated_at",
        )
