import factory
from users.models import User
from core.enums import Roles
from tests.factories.tenants import TenantFactory


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    role = Roles.GAMER
    tenant = factory.SubFactory(TenantFactory)
    is_verified = True
    is_active = True
