from django.urls import path
from .views import register, login, protected, logout

urlpatterns = [
    path("register/", register, name="index"),
    path("login/", login, name="index"),
    path("protected/", protected, name="index"),
    path("logout/", logout, name="index"),
]