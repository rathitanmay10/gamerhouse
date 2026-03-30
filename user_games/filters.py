import uuid

from django_filters.rest_framework import CharFilter, FilterSet, NumberFilter

from core.enums import Status
from user_games.models import UserGame


class UserGameFilter(FilterSet):
    platform = CharFilter(field_name="platform_id", method="filter_platform_safe")
    status = CharFilter(method="filter_status_safe")
    min_hours_played = NumberFilter(
        field_name="hours_played", lookup_expr="gte", method="filter_min_hours_played"
    )
    min_rating = NumberFilter(
        field_name="personal_rating", lookup_expr="gte", method="filter_min_rating"
    )

    class Meta:
        model = UserGame
        fields = ["status", "platform", "hours_played", "personal_rating"]

    def filter_platform_safe(self, queryset, name, value):
        uuids = []
        for val in value.split(","):
            try:
                uuids.append(uuid.UUID(val.strip()))
            except (ValueError, TypeError):
                continue
        if uuids:
            return queryset.filter(platform_id__in=uuids)
        return queryset

    def filter_status_safe(self, queryset, name, value):
        statuses = [
            v.strip() for v in value.split(",") if v.strip() in dict(Status.choices)
        ]
        if statuses:
            return queryset.filter(status__in=statuses)
        return queryset

    def filter_min_hours_played(self, queryset, name, value):
        try:
            return queryset.filter(hours_played__gte=int(value))
        except (ValueError, TypeError):
            return queryset

    def filter_min_rating(self, queryset, name, value):
        try:
            return queryset.filter(personal_rating__gte=int(value))
        except (ValueError, TypeError):
            return queryset
