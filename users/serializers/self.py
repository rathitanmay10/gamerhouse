from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class SelfUserSerializer(serializers.ModelSerializer):
    """
    Serializer for self-service user profile operations.

    Used by authenticated users to view and update their own profile.
    Identity and audit fields are read-only and cannot be modified
    through this serializer.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "created_at",
        )
        read_only_fields = ("id", "username", "email", "created_at")


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing the authenticated user's password.

    Requires the current password for verification and validates the
    new password using Django's configured password validators.
    """

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password]
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def validate_old_password(self, value):
        """
        Ensure the provided current password matches the user's password.
        """
        if not self.user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def save(self, **kwargs):
        """
        Set and persist the new password for the authenticated user.
        """
        self.user.set_password(self.validated_data["new_password"])
        self.user.save(update_fields=["password"])
