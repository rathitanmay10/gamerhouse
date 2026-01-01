from django.urls import path
from users.views.auth import RegisterAPIView, LoginView, LogoutAPIView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/logout/", LogoutAPIView.as_view()),
]
