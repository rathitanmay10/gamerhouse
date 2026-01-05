from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new user.

    Responsibilities:
    - Validate password strength using Django validators
    - Ensure password and confirm_password match
    - Prevent registration if username/email already exists
    - Block registration for inactive users
    - Create user using the UserManager
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "confirm_password",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return attrs

    def validate_username(self, value):
        """
        Field-level validation for username.

        - Blocks registration if an inactive user exists
        - Raises a unique constraint error for active users
        """
        user = User.all_objects.filter(username=value).first()

        if user:
            if not user.is_active:
                raise serializers.ValidationError(
                    "User exists already, contact admin.",
                    code="unique",
                )
            raise serializers.ValidationError(
                "Username already exists.",
                code="unique",
            )

        return value

    def validate_email(self, value):
        """
        Field-level validation for email.

        - Blocks registration if an inactive user exists
        - Raises a unique constraint error for active users
        """
        user = User.all_objects.filter(email=value).first()

        if user:
            if not user.is_active:
                raise serializers.ValidationError(
                    "User exists already, contact admin.",
                    code="unique",
                )
            raise serializers.ValidationError(
                "Email already exists.",
                code="unique",
            )

        return value

    def create(self, validated_data):
        """
        Create user via UserManager to ensure:
        - password hashing
        - default role assignment
        """

        validated_data.pop("confirm_password")
        return User.objects.create_user(**validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that injects user roles
    into the issued access and refresh tokens.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for refresh-token based logout (blacklisting).
    """

    refresh = serializers.CharField()

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError({"refresh": "Invalid or expired token"})
