import pytest
from django.db import IntegrityError

from tests.factories.tenants import TenantFactory
from tests.factories.users import UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_user_creation(self):
        tenant = TenantFactory()
        user = UserFactory(email="gamer@example.com", tenant=tenant)
        assert user.email == "gamer@example.com"
        assert user.is_verified is True
        assert user.tenant == tenant

    def test_email_uniqueness(self):
        UserFactory(email="duplicate@example.com")
        with pytest.raises(IntegrityError):
            UserFactory(email="duplicate@example.com")

    def test_user_soft_delete(self):
        user = UserFactory()
        assert user.is_active is True

        user.soft_delete()
        user.refresh_from_db()

        assert user.is_active is False
        assert user.deleted_at is not None
        from users.models import User

        assert User.objects.filter(id=user.id).count() == 0
        assert User.all_objects.filter(id=user.id).count() == 1

    def test_user_delete_override(self):
        user = UserFactory()
        user.delete()
        user.refresh_from_db()

        assert user.is_active is False
        assert user.deleted_at is not None
