import factory

from core.enums import Status
from tests.factories.catalog import PlatformFactory
from tests.factories.tenant_games import TenantGameFactory
from tests.factories.users import UserFactory
from user_games.models import UserGame, UserGameNote


class UserGameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserGame

    user = factory.SubFactory(UserFactory)
    tenant_game = factory.SubFactory(
        TenantGameFactory, tenant=factory.SelfAttribute("..user.tenant")
    )
    platform = factory.SubFactory(PlatformFactory)
    status = Status.WISHLIST
    tenant = factory.SelfAttribute("user.tenant")


class UserGameNoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserGameNote

    user_game = factory.SubFactory(UserGameFactory)
    note = factory.Faker("paragraph")
    tenant = factory.SelfAttribute("user_game.tenant")
