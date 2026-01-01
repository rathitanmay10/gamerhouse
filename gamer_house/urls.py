from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("users.urls")),
    # path("api/v1/games/", include("games.urls")),
    # path("api/v1/genres/", include("genres.urls")),
    # path("api/v1/platforms/", include("platforms.urls")),
]
