from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from users.serializers.self import SelfUserSerializer, ChangePasswordSerializer


class MeAPIView(APIView):
    """
    Self-service endpoint for the authenticated user.

    Allows an authenticated user to:
    - Retrieve their own profile
    - Partially update their profile
    - Delete their own account

    Account deletion requires a valid refresh token belonging to the
    authenticated user. On successful deletion, the refresh token is
    blacklisted to immediately revoke access.
    """

    def get(self, request):
        serializer = SelfUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = SelfUserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"detail": "Refresh token required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh)
            if str(token["user_id"]) != str(request.user.id):
                return Response(
                    {"detail": "Token does not belong to authenticated user"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid or expired refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordAPIView(APIView):
    """
    Change the authenticated user's password.

    Verifies the current password and updates it to a new value.
    On success, no response body is returned.
    """

    def post(self, request):
        serializer = ChangePasswordSerializer(user=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
