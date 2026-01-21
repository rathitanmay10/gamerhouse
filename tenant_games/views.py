from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet

from core.enums import Roles
from tenant_games.filters import TenantGameFilter
from tenant_games.models import TenantGame
from tenant_games.permissions import TenantGamePermission
from tenant_games.serializers import TenantGameMappingSerializer, TenantGameSerializer


class TenantGameViewSet(ModelViewSet):
    permission_classes = [TenantGamePermission]
    serializer_class = TenantGameMappingSerializer
    http_method_names = ["get", "post", "delete", "options", "head"]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TenantGameFilter

    def get_queryset(self):
        user = self.request.user

        qs = TenantGame.objects.select_related(
            "tenant", "game", "game__genre"
        ).prefetch_related("game__platforms")
        if user.role == Roles.SUPER_ADMIN:
            return qs

        elif user.role in [Roles.ADMIN, Roles.GAMER]:
            return qs.filter(tenant=user.tenant)
        else:
            raise PermissionDenied("Not allowed.")

    def get_serializer_class(self):
        user = self.request.user
        if self.action == "create":
            return TenantGameMappingSerializer
        if user.role == Roles.SUPER_ADMIN:
            return TenantGameMappingSerializer

        return TenantGameSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == Roles.SUPER_ADMIN:
            serializer.save()
        elif user.role == Roles.ADMIN:
            serializer.save(tenant=user.tenant)
        else:
            raise PermissionDenied("Not allowed.")
