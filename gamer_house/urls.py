from django.contrib import admin
from django.urls import include, path

from core.views import HealthCheckView
from payments.views.views_ui import payment_callback
from users.views import ResetPasswordPageView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("admin/", admin.site.urls),
    path(
        "reset-password/", ResetPasswordPageView.as_view(), name="reset-password-page"
    ),
    path("payments/callback/", payment_callback),
    path("api/v1/", include("users.urls")),
    path("api/v1/", include("catalog.urls")),
    path("api/v1/", include("user_games.urls")),
    path("api/v1/", include("tenants.urls")),
    path("api/v1/", include("tenant_games.urls")),
    path("api/v1/", include("payments.urls")),
]
