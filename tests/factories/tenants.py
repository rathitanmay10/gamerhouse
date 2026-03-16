import factory

from core.enums import TenantStatus
from tenants.models import Tenant


class TenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenant

    name = factory.Faker("company")
    status = TenantStatus.ACTIVE
