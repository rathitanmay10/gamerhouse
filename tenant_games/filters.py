import uuid

from django_filters.rest_framework import CharFilter, FilterSet

from tenant_games.models import TenantGame


class TenantGameFilter(FilterSet):
    tenant = CharFilter(field_name="tenant_id", method="filter_tenant_safe")
    genres = CharFilter(field_name="game__genre_id", method="filter_genres_safe")
    platforms = CharFilter(field_name="game__platforms", method="filter_platforms_safe")
    search = CharFilter(field_name="game__title", method="filter_search_safe")

    class Meta:
        model = TenantGame
        fields = ["tenant", "genres", "platforms", "search"]

    def filter_tenant_safe(self, qs, name, value):
        try:
            uuid_val = uuid.UUID(str(value))
            return qs.filter(tenant_id=uuid_val)
        except (ValueError, TypeError):
            return qs

    def filter_genres_safe(self, qs, name, value):
        valid_uuids = []
        for g in value.split(","):
            try:
                valid_uuids.append(uuid.UUID(g.strip()))
            except (ValueError, TypeError):
                continue
        if valid_uuids:
            return qs.filter(game__genre_id__in=valid_uuids)
        return qs

    def filter_platforms_safe(self, qs, name, value):
        valid_uuids = []
        for p in value.split(","):
            try:
                valid_uuids.append(uuid.UUID(p.strip()))
            except (ValueError, TypeError):
                continue
        if valid_uuids:
            return qs.filter(game__platforms__id__in=valid_uuids)
        return qs

    def filter_search_safe(self, qs, name, value):
        if value:
            return qs.filter(game__title__icontains=value)
        return qs
