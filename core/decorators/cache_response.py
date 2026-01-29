from functools import wraps

from django.core.cache import cache
from rest_framework.response import Response
from core.constants import CACHE_RESPONSE_TTL

def drf_cache_response(prefix: str, ttl: int = CACHE_RESPONSE_TTL):
    """
    Caches DRF responses with full query param support.
    Example cache key:
    cache:genres:list:page=2&page_size=50
    """

    def decorator(view_method):
        @wraps(view_method)
        def wrapper(self, request, *args, **kwargs):
            query_string = request.query_params.urlencode()

            if "pk" in kwargs:
                suffix = f"{prefix}:{kwargs['pk']}"
            else:
                suffix = prefix

            cache_key = f"cache:{suffix}:{query_string}"

            cached = cache.get(cache_key)
            if cached is not None:
                return Response(cached)

            response = view_method(self, request, *args, **kwargs)

            if isinstance(response, Response):
                cache.set(cache_key, response.data, ttl)

            return response

        return wrapper

    return decorator
