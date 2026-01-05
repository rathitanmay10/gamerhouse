from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def is_unique_field_error(exc) -> bool:
    """
    Detect DRF UniqueValidator errors using error codes (safe & explicit).
    """
    for field_errors in exc.detail.values():
        for error in field_errors:
            if error.code == "unique":
                return True

    return False


def normalize_jwt_error(exc):
    """
    Extract a clean, stable message from SimpleJWT errors.
    """
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
    - 409 for unique constraint violations
    - 400 for other validation errors
    - Normalized responses for auth, permission, and not-found errors
    """
    if isinstance(exc, ValidationError) and is_unique_field_error(exc):
        return Response(
            {
                "error": {
                    "code": "conflict",
                    "message": "Resource already exists",
                    "details": exc.detail,
                }
            },
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, ValidationError):
        return Response(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Invalid request data",
                    "details": exc.detail,
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, (TokenError, InvalidToken)):
        return Response(
            {
                "error": {
                    "code": "token_not_valid",
                    "message": normalize_jwt_error(exc),
                    "details": None,
                }
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, APIException):
        return Response(
            {
                "error": {
                    "code": exc.default_code,
                    "message": exc.detail,
                    "details": None,
                }
            },
            status=exc.status_code,
        )

    return exception_handler(exc, context)
