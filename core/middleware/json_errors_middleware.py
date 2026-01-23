from django.http import JsonResponse


class JsonErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Convert Django HTML errors to JSON only for non-DRF errors
        if response.status_code >= 400 and response.get("content-type", "").startswith(
            "text/html"
        ):
            return JsonResponse(
                {"error": response.reason_phrase}, status=response.status_code
            )

        return response
