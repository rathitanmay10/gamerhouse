from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.enums import Roles
from tenant_games.filters import TenantGameFilter
from tenant_games.models import TenantGame
from tenant_games.permissions import TenantGamePermission
from tenant_games.serializers import (
    TenantGameBulkAddSerializer,
    TenantGameBulkDeleteSerializer,
    TenantGameMappingSerializer,
    TenantGameSerializer,
)


class TenantGameViewSet(ModelViewSet):
    """
    Tenant Game ViewSet
    """

    permission_classes = [TenantGamePermission]
    serializer_class = TenantGameMappingSerializer
    http_method_names = ["get", "post", "delete", "options", "head"]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TenantGameFilter

    def get_queryset(self):
        """
        Get queryset for TenantGameViewSet
        """
        user = self.request.user

        qs = TenantGame.objects.select_related(
            "tenant", "game", "game__genre"
        ).prefetch_related("game__platforms")

        # qs = TenantGame.objects.all()

        if user.role == Roles.SUPER_ADMIN:
            return qs

        elif user.role in [Roles.ADMIN, Roles.GAMER]:
            return qs.filter(tenant=user.tenant)
        else:
            raise PermissionDenied("Not allowed.")

    def get_serializer_class(self):
        """
        Get serializer class based on user role and action
        """
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

    @action(methods=["post"], detail=False, url_path="bulk-add")
    def bulk_add(self, request):
        """
        Bulk add games to tenant games
        """
        serializer = TenantGameBulkAddSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=False, url_path="bulk-delete")
    def bulk_delete(self, request):
        """
        Bulk delete games from tenant games
        """
        serializer = TenantGameBulkDeleteSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
