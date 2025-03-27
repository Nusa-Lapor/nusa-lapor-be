from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    register,
    login, 
    protected,
    protected_petugas,
    protected_admin,
    assign_petugas,
    logout,
    request_access_token,
)

app_name = "api_auth"

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("protected/", protected, name="protected"),
    path("protected/petugas/", protected_petugas, name="protected_petugas"),
    path("protected/admin/", protected_admin, name="protected_admin"),
    path("assign/petugas/", assign_petugas, name="assign_petugas"),
    path("logout/", logout, name="logout"),
    path("token/refresh/", request_access_token, name="token_refresh"),
]