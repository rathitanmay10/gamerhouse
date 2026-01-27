"""
Thread-local context management for request lifecycle.

This module manages context variables that need to be accessible
across the request lifecycle (middleware, views, logging, etc).
"""

from contextvars import ContextVar

# Context variable for correlation ID (request tracing)
correlation_id_var = ContextVar("correlation_id", default=None)
current_tenant = ContextVar("tenant", default=None)


def get_correlation_id():
    """
    Get the current correlation ID from context.

    Set by RequestResponseLoggingMiddleware for request tracing.

    Returns:
        Correlation ID (UUID string) or None if not yet set
    """
    return correlation_id_var.get()


def set_correlation_id(correlation_id):
    """
    Set the correlation ID in context.

    Called by RequestResponseLoggingMiddleware at the start of each request.

    Args:
        correlation_id: UUID string for request tracing
    """
    correlation_id_var.set(correlation_id)
