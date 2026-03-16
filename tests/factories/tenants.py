import factory
from tenants.models import Tenant
from core.enums import TenantStatus


class TenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenant

    name = factory.Faker("company")
    status = TenantStatus.ACTIVE
