from django.db import transaction
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet

from core.enums import Roles
from tenants.models import Tenant
from tenants.permissions import IsSuperAdminOrTenantAdminGetOwnTenant
from tenants.serializers import TenantSerializer


class TenantViewSet(ModelViewSet):
    permission_classes = [IsSuperAdminOrTenantAdminGetOwnTenant]
    serializer_class = TenantSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == Roles.SUPER_ADMIN:
            return Tenant.objects.all()

        if user.role == Roles.ADMIN:
            return Tenant.objects.filter(id=user.tenant_id)

        return Tenant.objects.none()

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.delete()
