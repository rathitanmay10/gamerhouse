"""
Health-check endpoint.

GET /health/  →  200 {"status": "ok", "db": "ok", "redis": "ok"}
              →  503 {"status": "error", "db": "...", "redis": "..."}

Used by Docker Compose healthcheck and the EC2 deploy script.
"""

from django.core.cache import cache
from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # no auth overhead on a health probe

    def get(self, request):
        """
        Report PostgreSQL and Redis/cache health and return an HTTP Response summarizing the results.
        
        Performs connectivity checks for the primary database and the configured cache; any failure is captured and included in the response body.
        
        Returns:
            rest_framework.response.Response: JSON body with keys:
                - "status": `"ok"` if both checks succeed, `"error"` otherwise.
                - "db": `"ok"` when the database check succeeds, otherwise the exception text from the database check.
                - "redis": `"ok"` when the cache check succeeds, otherwise the exception text from the cache check.
            The response uses HTTP 200 when both checks succeed and HTTP 503 if either check fails.
        """
        status = {"db": "ok", "redis": "ok"}
        http_status = 200

        # --- PostgreSQL check ---
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as exc:
            status["db"] = str(exc)
            http_status = 503

        # --- Redis check ---
        try:
            cache.set("__health_check__", "ok", timeout=5)
            if cache.get("__health_check__") != "ok":
                raise ValueError("Cache read-back mismatch")
        except Exception as exc:
            status["redis"] = str(exc)
            http_status = 503

        status["status"] = "ok" if http_status == 200 else "error"
        return Response(status, status=http_status)
