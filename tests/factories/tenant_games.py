import factory

from tenant_games.models import TenantGame
from tests.factories.catalog import GameFactory
from tests.factories.tenants import TenantFactory


class TenantGameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TenantGame

    tenant = factory.SubFactory(TenantFactory)
    game = factory.SubFactory(GameFactory)
