from functools import wraps

from django.core.cache import cache


def drf_invalidate_cache(pattern: str):
    """
    Invalidate all cache keys matching a pattern.
    Use pattern like 'cache:genres*'
    """

    def decorator(view_method):
        @wraps(view_method)
        def wrapper(self, request, *args, **kwargs):
            response = view_method(self, request, *args, **kwargs)
            cache.delete_pattern(pattern)
            return response

        return wrapper

    return decorator
