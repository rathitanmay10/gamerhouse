class GameQueryFilter:
    """
    Query-parameter filters for Game list endpoint.

    Supported query parameters:
    - search_query : case-insensitive match on game title
    - status       : comma-separated list
    - genre        : comma-separated genre IDs
    - platform     : comma-separated platform IDs
    - min_rating   : minimum personal rating (integer)
    - min_hours    : minimum hours played (integer)

    Behavior notes:
    - All filters are optional; missing parameters are ignored.
    - Comma-separated values are split, trimmed, and applied using `__in`.
    - Invalid values do not raise errors but result in an empty queryset
      (fail-soft behavior).

    Invalid values result in an empty queryset (fail-soft).
    """

    def __init__(self, queryset, params):
        self.qs = queryset
        self.params = params

    def apply(self):
        self.search_title()
        self.filter_status()
        self.filter_genre()
        self.filter_platform()
        self.filter_min_rating()
        self.filter_min_hours()
        return self.qs

    def search_title(self):
        value = self.params.get("search_query")
        if not value:
            return
        self.qs = self.qs.filter(title__icontains=value)

    def filter_status(self):
        value = self.params.get("status")
        if not value:
            return

        values = self.parse_str_list(value)

        self.qs = self.qs.filter(status__in=values)

    def filter_genre(self):
        value = self.params.get("genre")
        if not value:
            return

        ids = self.parse_str_list(value)

        self.qs = self.qs.filter(genre_id__in=ids)

    def filter_platform(self):
        value = self.params.get("platform")
        if not value:
            return

        ids = self.parse_str_list(value)

        self.qs = self.qs.filter(platform_id__in=ids)

    def filter_min_rating(self):
        value = self.params.get("min_rating")
        if not value:
            return

        number = self.parse_int(value)
        self.qs = self.qs.filter(personal_rating__gte=number)

    def filter_min_hours(self):
        value = self.params.get("min_hours")
        if not value:
            return

        number = self.parse_int(value)
        self.qs = self.qs.filter(hours_played__gte=number)

    def parse_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def parse_str_list(self, value):
        return [v.strip() for v in value.split(",") if v.strip()]
