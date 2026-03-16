import factory
from tenant_games.models import TenantGame
from tests.factories.tenants import TenantFactory
from tests.factories.catalog import GameFactory


class TenantGameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TenantGame

    tenant = factory.SubFactory(TenantFactory)
    game = factory.SubFactory(GameFactory)
