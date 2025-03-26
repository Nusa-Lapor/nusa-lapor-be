from django.urls import path, include
from . import views

app_name = "api_article"

urlpatterns = [
    # Artikel URLs
    path('artikel/', views.get_articles, name='artikel-list'),
    path('artikel/featured/', views.get_featured_articles, name='artikel-featured'),
    path('artikel/categories/', views.get_article_categories,
         name='artikel-categories'),
    path('artikel/category/<str:kategori>/',
         views.get_articles_by_category, name='artikel-by-category'),
    path('artikel/<slug:slug>/', views.get_article, name='artikel-detail'),
    path('artikel/create/', views.create_article, name='artikel-create'),
    path('artikel/<slug:slug>/update/',
         views.update_article, name='artikel-update'),
    path('artikel/<slug:slug>/delete/',
         views.delete_article, name='artikel-delete'),

    # Komentar URLs
    path('komentar/create/', views.create_comment, name='komentar-create'),
    path('komentar/article/<uuid:article_id>/',
         views.get_comments_by_article, name='komentar-by-article'),
    path('komentar/<uuid:comment_id>/approve/',
         views.approve_comment, name='komentar-approve'),
    path('komentar/<uuid:comment_id>/delete/',
         views.delete_comment, name='komentar-delete'),

    # Tag URLs
    path('tag/', views.get_tags, name='tag-list'),
    path('tag/<slug:slug>/articles/',
         views.get_articles_by_tag, name='articles-by-tag'),
    path('tag/create/', views.create_tag, name='tag-create'),
    path('tag/<slug:slug>/delete/', views.delete_tag, name='tag-delete'),
]
