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
    - Request/response lifecycle logging with proper log levels (INFO/WARNING/ERROR)
    - Error logging with stack traces (debugging production issues)
    - Async-safe logging (works with Celery & async views via thread-local storage)
    """

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
        tenant_id = request.user.tenant_id if request.user.is_authenticated else None
        user_id = request.user.id if request.user.is_authenticated else None

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
        tenant_id = request.user.tenant_id if request.user.is_authenticated else None
        user_id = request.user.id if request.user.is_authenticated else None

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
        tenant_id = request.user.tenant_id if request.user.is_authenticated else None
        user_id = request.user.id if request.user.is_authenticated else None

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
