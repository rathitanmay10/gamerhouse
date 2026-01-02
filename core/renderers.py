from rest_framework.renderers import JSONRenderer


class StandardJSONRenderer(JSONRenderer):
    """
    Global response renderer that enforces a
    consistent API response structure.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response")

        if response and response.status_code == 204:
            return b""

        if response and response.exception:
            return super().render(data, accepted_media_type, renderer_context)

        if isinstance(data, dict) and {"count", "page", "page_size"}.issubset(
            data.keys()
        ):
            return super().render(data, accepted_media_type, renderer_context)

        return super().render(
            {
                "data": data,
            },
            accepted_media_type,
            renderer_context,
        )
