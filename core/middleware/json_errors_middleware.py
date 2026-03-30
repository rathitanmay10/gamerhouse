from django.http import JsonResponse


class JsonErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            return JsonResponse(
                {"error": "Internal server error.", "details": str(exc)},
                status=500,
            )
