from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

app_name = "main"

urlpatterns = [
    path('', include(router.urls)),
    path('statistics/', views.get_statistics, name='statistics'),
]