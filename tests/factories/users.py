import factory

from core.enums import Roles
from tests.factories.tenants import TenantFactory
from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    role = Roles.GAMER
    tenant = factory.SubFactory(TenantFactory)
    is_verified = True
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted if extracted else "password"
        self.set_password(password)
        if create:
            self.save()
