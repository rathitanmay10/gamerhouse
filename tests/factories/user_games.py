import factory
from user_games.models import UserGame, UserGameNote
from core.enums import Status
from tests.factories.users import UserFactory
from tests.factories.tenant_games import TenantGameFactory
from tests.factories.catalog import PlatformFactory
from tests.factories.tenants import TenantFactory


class UserGameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserGame

    user = factory.SubFactory(UserFactory)
    tenant_game = factory.SubFactory(TenantGameFactory)
    platform = factory.SubFactory(PlatformFactory)
    status = Status.WISHLIST
    tenant = factory.SubFactory(TenantFactory)


class UserGameNoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserGameNote

    user_game = factory.SubFactory(UserGameFactory)
    note = factory.Faker("paragraph")
    tenant = factory.SubFactory(TenantFactory)
