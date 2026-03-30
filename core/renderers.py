from rest_framework.renderers import JSONRenderer


class StandardJSONRenderer(JSONRenderer):
    """
    Global response renderer that enforces a
    consistent API response structure.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response")

        if data is None:
            return super().render(data, accepted_media_type, renderer_context)

        if response and response.exception:
            return super().render(data, accepted_media_type, renderer_context)

        if isinstance(data, dict) and "message" in data:
            return super().render(data, accepted_media_type, renderer_context)

        if isinstance(data, dict) and "error" in data:
            return super().render(data, accepted_media_type, renderer_context)

        if isinstance(data, dict) and "data" in data and "count" in data:
            return super().render(data, accepted_media_type, renderer_context)

        return super().render(
            {
                "data": data,
            },
            accepted_media_type,
            renderer_context,
        )
