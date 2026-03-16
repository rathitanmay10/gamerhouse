import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.enums import Roles
from tests.factories.tenants import TenantFactory
from tests.factories.users import UserFactory


@pytest.fixture(autouse=True)
def clear_context_vars():
    """
    Clears context variables between tests to prevent leaks.
    """
    from core.context import correlation_id_var, current_tenant

    current_tenant.set(None)
    correlation_id_var.set(None)
    yield
    current_tenant.set(None)
    correlation_id_var.set(None)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Globally enables database access for all tests.
    """
    pass


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant():
    return TenantFactory()


@pytest.fixture
def user(tenant):
    return UserFactory(tenant=tenant)


@pytest.fixture
def get_auth_headers():
    def _get_headers(user):
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

    return _get_headers


@pytest.fixture
def authenticated_client(api_client, user, get_auth_headers):
    api_client.credentials(**get_auth_headers(user))
    return api_client


@pytest.fixture
def admin_user(tenant):
    return UserFactory(tenant=tenant, role=Roles.ADMIN)


@pytest.fixture
def admin_client(api_client, admin_user, get_auth_headers):
    api_client.credentials(**get_auth_headers(admin_user))
    api_client.raise_request_exception = True
    return api_client


@pytest.fixture
def superadmin_user(tenant):
    return UserFactory(tenant=tenant, role=Roles.SUPER_ADMIN)


@pytest.fixture
def superadmin_client(api_client, superadmin_user, get_auth_headers):
    api_client.credentials(**get_auth_headers(superadmin_user))
    return api_client
