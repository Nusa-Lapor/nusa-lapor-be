from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'artikel', views.ArtikelViewSet)

app_name = "article"

urlpatterns = [
    path('', include(router.urls)),
] 