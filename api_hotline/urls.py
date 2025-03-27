from django.urls import path
from . import views

app_name = 'api_hotline'

urlpatterns = [
    # Endpoint untuk daftar dan pembuatan hotline
    path('', views.get_hotlines, name='hotline-list'),
    path('create/', views.create_hotline, name='hotline-create'),
    
    # Endpoint untuk detail, update, dan hapus hotline
    path('<uuid:id_hotline>/', views.get_hotline, name='hotline-detail'),
    path('<uuid:id_hotline>/update/', views.update_hotline, name='hotline-update'),
    path('<uuid:id_hotline>/delete/', views.delete_hotline, name='hotline-delete'),
    
    # Endpoint untuk menelepon hotline
    path('<uuid:id_hotline>/call/', views.call_hotline, name='hotline-call'),
] 