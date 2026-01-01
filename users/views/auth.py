"""
{
  "username": "tanmay_rathi",
  "email": "tanmay.rathi@example.com",
  "password": "StrongPassword@123",
  "confirm_password": "StrongPassword@123"
}

"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from users.serializers.auth import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
)


class RegisterAPIView(APIView):
    """
    API endpoint for user registration.

    Accepts user credentials and profile information,
    creates a new user account, and returns a minimal
    confirmation response on success.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully",
                "data": {
                    "username": user.username,
                    "email": user.email,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """
    JWT-based login endpoint.

    Authenticates user credentials and returns
    an access/refresh token pair.
    """

    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class LogoutAPIView(APIView):
    """
    API endpoint for logging out an authenticated user.

    Requires a valid refresh token and invalidates it
    by adding it to the blacklist.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
