import pytest
from django.db import IntegrityError

from tenants.models import Tenant
from users.models import User


@pytest.fixture
def test_data(db):
    tenant = Tenant.objects.create(name="Test Tenant")
    user = User.objects.create(
        email="gamer@example.com", username="gamer", tenant=tenant
    )

    return {
        "tenant": tenant,
        "user": user,
    }


class TestUserModel:
    def test_user_creation(self, test_data):
        user = test_data["user"]
        assert user.email == "gamer@example.com"
        assert not user.is_verified
        assert user.tenant == test_data["tenant"]

    def test_email_uniqueness(self, test_data):
        with pytest.raises(IntegrityError):
            User.objects.create(
                email="gamer@example.com",
                username="another_gamer",
                tenant=test_data["tenant"],
            )

    def test_user_soft_delete(self, test_data):
        user = test_data["user"]
        assert user.is_active is True

        user.soft_delete()
        user.refresh_from_db()

        assert user.is_active is False
        assert user.deleted_at is not None
        assert User.objects.filter(id=user.id).count() == 0
        assert User.all_objects.filter(id=user.id).count() == 1

    def test_user_delete_override(self, test_data):
        user = test_data["user"]
        user.delete()
        user.refresh_from_db()

        assert user.is_active is False
        assert user.deleted_at is not None
