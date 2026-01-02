from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from users.views.auth import RegisterAPIView, LoginView, LogoutAPIView
from users.views.admin import AdminUserViewSet
from users.views.self import MeAPIView, ChangePasswordAPIView

router = DefaultRouter()
router.register("users", AdminUserViewSet, basename="users")

urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/logout/", LogoutAPIView.as_view()),
    path("users/me/", MeAPIView.as_view()),
    path("users/me/change-password/", ChangePasswordAPIView.as_view()),
    path("", include(router.urls)),
]
