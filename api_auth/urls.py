from django.urls import path
from .views import register, login, protected, logout

app_name = "api_auth"

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("protected/", protected, name="protected"),
    path("logout/", logout, name="logout"),
]