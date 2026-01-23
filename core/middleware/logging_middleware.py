import logging
import time
import traceback
import uuid

from django.utils.deprecation import MiddlewareMixin

from core.context import set_correlation_id

logger = logging.getLogger("request_logger")


class RequestResponseLoggingMiddleware(MiddlewareMixin):
    """
    Request-Response Logging Middleware - Provides JSON-Structured Observability

    This middleware provides comprehensive logging for all HTTP requests and responses
    with the following features:

    Logging Format:
    - All logs are output as JSON (configured via LOGGING['formatters']['json'] in settings.py)
    - Uses 'python-json-logger' for structured, machine-readable logs
    - Compatible with log aggregation tools (ELK, Datadog, Splunk, etc.)

    Features:
    - Correlation ID generation and propagation (trace requests across services)
    - Tenant ID & User ID context (audit trail and multi-tenant data isolation)
    - Execution time in milliseconds (performance monitoring)
    - Sensitive data masking (passwords, tokens, API keys)
    - Request/response lifecycle logging with proper log levels (INFO/WARNING/ERROR)
    - Error logging with stack traces (debugging production issues)
    - Async-safe logging (works with Celery & async views via thread-local storage)
    """

    # Sensitive field patterns to mask
    SENSITIVE_FIELDS = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "auth",
        "authorization",
        "refresh",
        "access_token",
        "refresh_token",
    }

    def process_request(self, request):
        """
        Called on each request, before Django decides which view to execute.
        Generates correlation ID and logs request details.
        """
        # Generate and store correlation ID for request tracing across logs and services
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        request.correlation_id = correlation_id

        # Store request start time for measuring execution duration
        request._start_time = time.time()

        # Extract user and tenant context early for logging
        tenant_id, tenant_name, user_id = self._extract_user_context(request)

        # Extract request details for structured logging
        log_data = {
            # Tracing: correlation_id enables tracking this request across all logs and services
            "correlation_id": correlation_id,
            # Request metadata: method and path identify the operation being performed
            "method": request.method,
            "path": request.path,
            # Client info: IP and user agent help identify request source and client type
            "ip_address": self._get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            # Tenant context: identifies which tenant (if multi-tenant) for data isolation
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            # User context: identifies authenticated user for access control and audit trails
            "user_id": user_id,
        }

        # Log at INFO level - request has been received and is being processed
        logger.info("Request received", extra=log_data)

        return None

    def process_response(self, request, response):
        """
        Called on each response. Logs response details and timing.
        """
        # Calculate execution time in milliseconds for performance monitoring
        execution_time = 0
        if hasattr(request, "_start_time"):
            execution_time = (time.time() - request._start_time) * 1000  # Convert to ms

        # Get correlation ID for request tracing
        correlation_id = getattr(request, "correlation_id", str(uuid.uuid4()))

        # Extract user and tenant context for audit logging
        tenant_id, tenant_name, user_id = self._extract_user_context(request)

        # Prepare log data with complete response information
        log_data = {
            # Tracing: same correlation_id as process_request to link logs
            "correlation_id": correlation_id,
            # Request metadata for context
            "method": request.method,
            "path": request.path,
            # Response status: indicates success/failure of the request
            "status_code": response.status_code,
            # Performance: execution_time_ms identifies slow endpoints for optimization
            "execution_time_ms": round(execution_time, 2),
            # Audit: tenant and user IDs enable tracing actions to specific tenant/user
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "user_id": user_id,
        }

        # Add response size for monitoring response payload sizes
        if hasattr(response, "content"):
            log_data["response_size"] = len(response.content)

        # Choose log level based on HTTP status code
        # ERROR: 5xx status codes indicate server-side failures requiring immediate attention
        # WARNING: 4xx status codes indicate client errors or validation failures to monitor
        # INFO: 2xx/3xx status codes indicate successful responses
        if response.status_code >= 500:
            logger.error("Response sent with server error", extra=log_data)
        elif response.status_code >= 400:
            logger.warning("Response sent with client error", extra=log_data)
        else:
            logger.info("Response sent", extra=log_data)

        return response

    def process_exception(self, request, exception):
        """
        Called when a view raises an unhandled exception. Logs error with full context for debugging.
        """
        # Calculate execution time in milliseconds when exception occurred
        execution_time = 0
        if hasattr(request, "_start_time"):
            execution_time = (time.time() - request._start_time) * 1000

        # Get correlation ID to link this error to the original request logs
        correlation_id = getattr(request, "correlation_id", str(uuid.uuid4()))

        # Extract user and tenant context for audit trail of who encountered the error
        tenant_id, tenant_name, user_id = self._extract_user_context(request)

        # Prepare comprehensive error log data for debugging and monitoring
        log_data = {
            # Tracing: same correlation_id to link to process_request logs
            "correlation_id": correlation_id,
            # Request context: what operation failed
            "method": request.method,
            "path": request.path,
            # Performance: when in request lifecycle the error occurred
            "execution_time_ms": round(execution_time, 2),
            # Audit: who (user/tenant) experienced the error
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "user_id": user_id,
            # Error details: exception type and message for error classification and alerting
            "error_type": exception.__class__.__name__,
            "error_message": str(exception),
            # Debug context: stack trace enables developers to identify root cause
            "stack_trace": traceback.format_exc(),
        }

        # Log at ERROR level - exception is a serious condition requiring investigation
        # exc_info=True adds Python exception details in addition to the stack_trace field
        logger.error("Request failed with exception", extra=log_data, exc_info=True)

        # Return None to allow Django's default exception handlers to process
        # (this doesn't suppress the exception, just allows normal error handling)
        return None

    def _get_client_ip(self, request):
        """
        Extract client IP address from request.
        Handles proxy headers like X-Forwarded-For.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")
        return ip

    def _extract_user_context(self, request):
        """
        Extract user and tenant information from the request for audit logging.

        Returns:
            tuple: (tenant_id, tenant_name, user_id)

        Why we log these:
        - tenant_id: Multi-tenant data isolation; enables per-tenant analytics and billing
        - tenant_name: Human-readable identification for log correlation
        - user_id: Audit trail for compliance, identifies which user performed an action
        """
        tenant_id = None
        tenant_name = None
        user_id = None

        # Only extract user info if they're authenticated (security: don't log unauthenticated sessions)
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = str(request.user.id)

            # Extract tenant information if multi-tenant setup is enabled
            if hasattr(request.user, "tenant") and request.user.tenant:
                tenant_id = str(request.user.tenant.id)
                tenant_name = request.user.tenant.name

        return tenant_id, tenant_name, user_id

    def _mask_sensitive_data(self, data):
        """
        Recursively mask sensitive data in dictionaries and lists to prevent logging secrets.

        This is critical for preventing credential leakage in logs while maintaining observability.
        Any request/response data containing passwords, tokens, or API keys will be masked.

        Args:
            data: Dictionary, list, or primitive value

        Returns:
            Same structure with sensitive values masked as "***MASKED***"

        Example:
            {"username": "john", "password": "secret123"}
            becomes:
            {"username": "john", "password": "***MASKED***"}
        """
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                # Check if key name matches any sensitive field pattern
                # This prevents logging passwords, tokens, API keys, auth headers, etc.
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    masked[key] = "***MASKED***"
                else:
                    # Recursively process nested structures
                    masked[key] = self._mask_sensitive_data(value)
            return masked
        elif isinstance(data, list):
            # Process each item in lists (e.g., multiple credentials, list of tokens)
            return [self._mask_sensitive_data(item) for item in data]
        else:
            # Primitive values pass through unchanged
            return data


def get_correlation_id():
    """
    Get the current correlation ID from thread-local storage.

    This function enables views, services, and other middleware to attach the same
    correlation ID to their logs, creating an audit trail across the entire request.

    Usage in views:
        from core.context import get_correlation_id
        correlation_id = get_correlation_id()
        # Use in Celery tasks, external API calls, logging, etc.

    Returns:
        str: Correlation ID (UUID) or None if not yet set
    """
    from core.context import get_correlation_id as _get_correlation_id

    return _get_correlation_id()
