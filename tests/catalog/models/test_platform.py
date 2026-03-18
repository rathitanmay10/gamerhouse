import pytest
from django.db.models import ProtectedError

from tests.factories.catalog import GameFactory, PlatformFactory


@pytest.mark.django_db
class TestPlatformModel:
    def test_platform_creation(self):
        platform = PlatformFactory(name="PlayStation 5")
        assert platform.name == "PlayStation 5"
        assert platform.id is not None

    def test_platform_deletion_protected(self):
        platform = PlatformFactory()
        # GameFactory post_generation adds a platform by default if none provided
        GameFactory(platforms=[platform])

        with pytest.raises(ProtectedError):
            platform.delete()

    def test_platform_deletion_allowed(self):
        platform = PlatformFactory()
        platform.delete()

        assert platform.deleted_at is not None
        from catalog.models.platform_models import Platform

        assert Platform.objects.filter(id=platform.id).count() == 0
        assert Platform.all_objects.filter(id=platform.id).count() == 1
