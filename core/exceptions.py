from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def normalize_jwt_error(exc):
    """
    Extract a clean, stable message from SimpleJWT errors.
    """
    if isinstance(exc.detail, str):
        return exc.detail

    if isinstance(exc.detail, dict):
        if "detail" in exc.detail:
            return exc.detail["detail"]

        messages = exc.detail.get("messages")
        if messages and isinstance(messages, list):
            return messages[0].get("message")

    return "Invalid or expired token."


def custom_exception_handler(exc, context):
    """
    Global DRF exception handler with clean HTTP semantics.
    - 400 for validation errors
    - Normalized responses for auth, permission, and not-found errors
    """
    if isinstance(exc, ValidationError):
        return Response(
            {"error": exc.detail},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, ProtectedError):
        error_message = (
            exc.args[0]
            if exc.args
            else "Cannot delete this resource because it is referenced by other objects."
        )
        return Response(
            {"error": error_message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, IntegrityError):
        return Response(
            {"error": "Invalid data or constraint violation."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(exc, (ObjectDoesNotExist, Http404)):
        message = str(exc).strip() or "Not Found"
        return Response(
            {"error": message},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, (TokenError, InvalidToken)):
        return Response(
            {"error": normalize_jwt_error(exc)},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, NotFound):
        return Response(
            {"error": exc.detail},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, APIException):
        return Response(
            {"error": exc.detail},
            status=exc.status_code,
        )

    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(response.data, dict) and "detail" in response.data:
            response.data = {"error": response.data["detail"]}
        return response

    return Response(
        {"error": "Internal server error."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
