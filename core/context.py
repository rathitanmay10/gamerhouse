"""
Thread-local context management for request lifecycle.

This module manages thread-local storage for context that needs to be
accessible across the request lifecycle (authentication, views, models, etc).
"""

from threading import local

# Thread-local storage for request context
_thread_local = local()


def get_current_tenant():
    """
    Get the current tenant from thread-local storage.

    Set by TenantJWTAuthentication during request authentication.
    Used by ActiveManager to automatically filter queries by tenant.

    Returns:
        Tenant object or None if not authenticated or no tenant
    """
    return getattr(_thread_local, "tenant", None)


def set_current_tenant(tenant):
    """
    Set the current tenant in thread-local storage.

    Called by TenantJWTAuthentication after successful JWT authentication.

    Args:
        tenant: Tenant object to store in thread-local
    """
    _thread_local.tenant = tenant


def get_correlation_id():
    """
    Get the current correlation ID from thread-local storage.

    Set by RequestResponseLoggingMiddleware for request tracing.

    Returns:
        Correlation ID (UUID) or None if not yet set
    """
    return getattr(_thread_local, "correlation_id", None)


def set_correlation_id(correlation_id):
    """
    Set the correlation ID in thread-local storage.

    Called by RequestResponseLoggingMiddleware.

    Args:
        correlation_id: UUID string for request tracing
    """
    _thread_local.correlation_id = correlation_id


def clear_context():
    """Clear all thread-local context (optional, for cleanup)."""
    _thread_local.tenant = None
    _thread_local.correlation_id = None
