from django.contrib.auth import get_user_model, authenticate
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
    - Validate password strength
    - Ensure password and confirm_password match
    - Enforce username and email uniqueness
    - Create user via UserManager
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
        extra_kwargs = {
            "username": {"validators": []},
            "email": {"validators": []},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return attrs

    def validate_username(self, value):
        """
        Reject registration if the username already exists.
        """
        user = User.all_objects.filter(username=value).first()

        if user:
            if not user.is_active:
                raise serializers.ValidationError(
                    "This account is disabled. Please contact support.",
                    code="inactive",
                )
            raise serializers.ValidationError(
                "Username already exists.",
                code="unique",
            )

        return value

    def validate_email(self, value):
        """
        Reject registration if the email already exists.
        """
        user = User.all_objects.filter(email=value).first()

        if user:
            if not user.is_active:
                raise serializers.ValidationError(
                    "This account is disabled. Please contact support.",
                    code="inactive",
                )
            raise serializers.ValidationError(
                "Email already exists.",
                code="unique",
            )

        return value

    def create(self, validated_data):
        """
        Create user using the UserManager to ensure
        proper password hashing and defaults.
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


class LoginSerializer(serializers.Serializer):
    """
    Validate credentials and return JWT access and refresh tokens.
    """

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username", "").strip()
        password = attrs.get("password")
        if not username or not password:
            raise serializers.ValidationError("Username and password are required.")
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active or user.deleted_at:
            raise serializers.ValidationError("Account is inactive.")
        refresh = CustomTokenObtainPairSerializer().get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


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
