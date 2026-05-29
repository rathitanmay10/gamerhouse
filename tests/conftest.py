import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.enums import Roles
from tests.factories.tenants import TenantFactory
from tests.factories.users import UserFactory


@pytest.fixture(autouse=True)
def clear_context_vars():
    """
    Reset request-scoped context variables before and after each test.
    
    This pytest autouse fixture sets `current_tenant` and `correlation_id_var` to `None` prior to test execution and again after test completion to prevent cross-test state leakage.
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
    Enable database access for every test by declaring a dependency on the `db` fixture.
    """
    pass


@pytest.fixture
def api_client():
    """
    Provide a fresh unauthenticated Django REST Framework API client for tests.
    
    Returns:
        client (rest_framework.test.APIClient): A new APIClient instance without credentials set.
    """
    return APIClient()


@pytest.fixture
def tenant():
    """
    Create and return a new Tenant test instance.
    
    Returns:
        tenant (Tenant): A newly created Tenant model instance from TenantFactory.
    """
    return TenantFactory()


@pytest.fixture
def user(tenant):
    """
    Create and return a test user associated with the provided tenant.
    
    Parameters:
        tenant (Tenant): Tenant instance to associate the created user with.
    
    Returns:
        user (User): A newly created test user instance linked to `tenant`.
    """
    return UserFactory(tenant=tenant)


@pytest.fixture
def get_auth_headers():
    """
    Return a callable that produces HTTP Authorization headers containing a JWT access token for a given user.
    
    The returned function accepts a user instance and builds a refresh token for that user, then returns a headers dictionary suitable for use with Django's test client credentials.
    
    Returns:
        callable: A function that accepts a user object and returns a dict `{'HTTP_AUTHORIZATION': 'Bearer <access_token>'}`.
    """
    def _get_headers(user):
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

    return _get_headers


@pytest.fixture
def authenticated_client(user, get_auth_headers):
    """
    Create an APIClient preconfigured with JWT authorization for the given user.
    
    Parameters:
        user: The user instance to authenticate as.
        get_auth_headers: Callable that accepts `user` and returns a headers dict (e.g. {"HTTP_AUTHORIZATION": "Bearer <token>"}).
    
    Returns:
        APIClient: A Django REST Framework test client with the returned authorization headers applied.
    """
    client = APIClient()
    client.credentials(**get_auth_headers(user))
    return client


@pytest.fixture
def admin_user(tenant):
    """
    Create a user associated with the given tenant and assign it the admin role.
    
    Parameters:
        tenant: Tenant instance to associate the created user with.
    
    Returns:
        user: Newly created user belonging to `tenant` with the `Roles.ADMIN` role.
    """
    return UserFactory(tenant=tenant, role=Roles.ADMIN)


@pytest.fixture
def admin_client(admin_user, get_auth_headers):
    """
    Create an API client authenticated as the provided admin user.
    
    Parameters:
        admin_user (User): Admin user instance used to generate authentication headers.
        get_auth_headers (callable): Function that accepts a user and returns a dict of HTTP auth headers.
    
    Returns:
        client (APIClient): DRF APIClient with credentials set for the admin user.
    """
    client = APIClient()
    client.credentials(**get_auth_headers(admin_user))
    return client


@pytest.fixture
def superadmin_user(tenant):
    """
    Create and return a super admin user associated with the given tenant.
    
    Parameters:
        tenant (Tenant): Tenant instance to associate with the created user.
    
    Returns:
        User: The created user with role set to Roles.SUPER_ADMIN.
    """
    return UserFactory(tenant=tenant, role=Roles.SUPER_ADMIN)


@pytest.fixture
def superadmin_client(superadmin_user, get_auth_headers):
    """
    Create an APIClient authenticated as the provided superadmin user.
    
    Parameters:
        superadmin_user (User): A user instance with the SUPER_ADMIN role.
        get_auth_headers (Callable): Callable that accepts a user and returns a dict of HTTP auth headers.
    
    Returns:
        APIClient: A Django REST Framework APIClient with credentials set for the superadmin user.
    """
    client = APIClient()
    client.credentials(**get_auth_headers(superadmin_user))
    return client
