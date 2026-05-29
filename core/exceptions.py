import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from core.context import get_correlation_id

logger = logging.getLogger(__name__)


def normalize_jwt_error(exc):
    """
    Return a normalized, client-facing message extracted from a SimpleJWT token exception.
    
    Inspects the exception's `detail` attribute and extracts a stable message suitable for API responses:
    - If `detail` is a string, that string is returned.
    - If `detail` is a dict and contains a `"detail"` key, that value is returned.
    - If `detail` is a dict and contains a non-empty `"messages"` list, the first element's `"message"` is returned.
    - Otherwise returns the fallback message "Invalid or expired token.".
    
    Parameters:
        exc: Exception instance from SimpleJWT/DRF that exposes a `detail` attribute.
    
    Returns:
        str: A cleaned token error message for client consumption.
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
    Map DRF and Django exceptions to consistent JSON error responses with appropriate HTTP status codes.
    
    Converts common exception types into Response objects with a JSON body of the form {"error": <message>} and an appropriate HTTP status:
    - ValidationError -> 400 with the original `detail`.
    - ProtectedError -> 400 with the first exception argument or a default deletion constraint message.
    - IntegrityError -> 400 with a generic constraint violation message.
    - ObjectDoesNotExist or Http404 -> 404 with the exception string or "Not Found".
    - TokenError or InvalidToken -> 401 with a normalized JWT error message.
    - NotFound -> 404 with the original `detail`.
    - APIException -> status from `exc.status_code` with `exc.detail`.
    If not handled above, delegates to DRF's default handler; if that produces a response with a `detail` key, it is transformed to {"error": detail}. If no response is produced, logs the unexpected error (including a correlation_id) and returns a 500 Internal Server Error with {"error": "Internal server error."}.
    
    Parameters:
        exc: The exception instance raised.
        context: The DRF exception context (contains request and view information).
    
    Returns:
        rest_framework.response.Response: A DRF Response containing a JSON error payload and the appropriate HTTP status code.
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
    logger.error(
        f"Unexpected exception 500: {exc}",
        extra={"correlation_id": get_correlation_id()},
    )
    return Response(
        {"error": "Internal server error."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
