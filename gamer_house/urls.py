from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("users.urls")),
    path("api/v1/", include("catalog.urls")),
    path("api/v1/", include("user_games.urls")),
    path("api/v1/", include("tenants.urls")),
    path("api/v1/", include("tenant_games.urls")),
]
