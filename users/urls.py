from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import (
    ChangePasswordAPIView,
    ForgotPasswordAPIView,
    LoginVerifyAPIView,
    LoginView,
    LogoutAPIView,
    MeAPIView,
    RegisterAPIView,
    ResendVerificationAPIView,
    ResetPasswordAPIView,
    TenantTokenRefreshView,
    UserViewSet,
    VerifyEmailAPIView,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/verify-login/", LoginVerifyAPIView.as_view(), name="login_verify"),
    path("auth/refresh/", TenantTokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutAPIView.as_view(), name="logout"),
    path(
        "auth/forgot-password/", ForgotPasswordAPIView.as_view(), name="forgot-password"
    ),
    path("auth/reset-password/", ResetPasswordAPIView.as_view(), name="reset-password"),
    path("auth/verify-email/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path(
        "auth/resend-verification/",
        ResendVerificationAPIView.as_view(),
        name="resend-verification",
    ),
    path(
        "auth/register/",
        RegisterAPIView.as_view(),
        name="tenant-register",
    ),
    path("users/me/", MeAPIView.as_view(), name="me"),
    path(
        "users/me/change-password/",
        ChangePasswordAPIView.as_view(),
        name="change-password",
    ),
    path("", include(router.urls)),
]
