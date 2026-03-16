import pytest

from core.enums import TenantStatus
from tenants.models import Tenant


@pytest.mark.django_db
class TestTenantModel:
    def test_tenant_creation(self):
        tenant = Tenant.objects.create(name="Sample Tenant")
        assert tenant.name == "Sample Tenant"
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.id is not None
        assert tenant.created_at is not None
        assert tenant.updated_at is not None

    def test_tenant_str(self):
        tenant = Tenant.objects.create(name="Cyber Cafe")
        assert str(tenant) == "Cyber Cafe"

    def test_tenant_soft_delete(self):
        tenant = Tenant.objects.create(name="To Be Deleted")
        tenant.delete()

        assert tenant.deleted_at is not None
        assert Tenant.objects.filter(id=tenant.id).count() == 0
        assert Tenant.all_objects.filter(id=tenant.id).count() == 1
