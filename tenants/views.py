from django.db import transaction
from rest_framework.viewsets import ModelViewSet

from core.enums import Roles, TenantStatus
from tenants.models import Tenant
from tenants.permissions import IsSuperAdminOrTenantAdminGetOwnTenant
from tenants.serializers import TenantDetailSerializer, TenantSerializer


class TenantViewSet(ModelViewSet):
    """
    Tenant ViewSet which handles CRUD operations for tenants.
    Admin can only read their own tenant.
    Super Admin can CRUD any tenant.
    """
    permission_classes = [IsSuperAdminOrTenantAdminGetOwnTenant]
    serializer_class = TenantSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == Roles.SUPER_ADMIN:
            return Tenant.objects.all()

        if user.role == Roles.ADMIN:
            return Tenant.objects.filter(id=user.tenant_id)

        return Tenant.objects.none()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TenantDetailSerializer
        return TenantSerializer

    @transaction.atomic
    def perform_destroy(self, instance):
        """
        Soft-delete tenant by marking it INACTIVE instead of deleting.
        """
        if instance.status != TenantStatus.INACTIVE:
            instance.status = TenantStatus.INACTIVE
            instance.save(update_fields=["status"])
