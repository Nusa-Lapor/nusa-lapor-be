from django.urls import path
from .views import (
    get_articles,
    get_featured_articles,
    get_article_categories,
    get_articles_by_category,
    get_article,
    create_article,
    update_article,
    delete_article,
    create_comment,
    get_comments_by_article,
    approve_comment,
    delete_comment,
    get_tags,
    get_articles_by_tag,
    create_tag,
    delete_tag,
)


app_name = "api_article"

urlpatterns = [
    # Artikel URLs
    path('artikel/', get_articles, name='artikel-list'),
    path('artikel/featured/', get_featured_articles, name='artikel-featured'),
    path('artikel/categories/', get_article_categories,
         name='artikel-categories'),
    path('artikel/category/<str:kategori>/',
         get_articles_by_category, name='artikel-by-category'),
    path('artikel/<slug:slug>/', get_article, name='artikel-detail'),
    path('artikel/create/', create_article, name='artikel-create'),
    path('artikel/<slug:slug>/update/',
         update_article, name='artikel-update'),
    path('artikel/<slug:slug>/delete/',
         delete_article, name='artikel-delete'),

    # Komentar URLs
    path('komentar/create/', create_comment, name='komentar-create'),
    path('komentar/article/<uuid:article_id>/',
         get_comments_by_article, name='komentar-by-article'),
    path('komentar/<uuid:comment_id>/approve/',
         approve_comment, name='komentar-approve'),
    path('komentar/<uuid:comment_id>/delete/',
         delete_comment, name='komentar-delete'),

    # Tag URLs
    path('tag/', get_tags, name='tag-list'),
    path('tag/<slug:slug>/articles/',
         get_articles_by_tag, name='articles-by-tag'),
    path('tag/create/', create_tag, name='tag-create'),
    path('tag/<slug:slug>/delete/', delete_tag, name='tag-delete'),
]
