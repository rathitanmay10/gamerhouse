import pytest

from core.enums import TenantStatus
from tests.factories.tenants import TenantFactory


@pytest.mark.django_db
class TestTenantModel:
    def test_tenant_creation(self):
        """
        Verify that TenantFactory creates a Tenant with the expected attributes.
        
        Asserts that the created tenant has the provided name, a default status of `TenantStatus.ACTIVE`, and non-null `id` and `created_at` fields.
        """
        tenant = TenantFactory(name="Sample Tenant")
        assert tenant.name == "Sample Tenant"
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.id is not None
        assert tenant.created_at is not None

    def test_tenant_soft_delete(self):
        tenant = TenantFactory()
        tenant.delete()

        assert tenant.deleted_at is not None
        from tenants.models import Tenant

        assert Tenant.objects.filter(id=tenant.id).count() == 0
        assert Tenant.all_objects.filter(id=tenant.id).count() == 1
