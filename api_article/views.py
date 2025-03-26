import os
import json
from django.forms import ValidationError
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.request import Request
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F, Q
from django.utils.text import slugify
from .models import Artikel, Komentar, Tag
from .serializers import (
    ArtikelListSerializer,
    ArtikelDetailSerializer,
    ArtikelCreateUpdateSerializer,
    KomentarSerializer,
    KomentarCreateSerializer,
    TagSerializer
)

# ===== Artikel APIs =====


@api_view(['GET'])
def get_articles(request: Request):
    """
    Mendapatkan daftar artikel yang dipublikasikan
    """
    try:
        # Filter artikel
        kategori = request.query_params.get('kategori', None)
        search = request.query_params.get('search', None)
        featured = request.query_params.get('featured', None)

        articles = Artikel.objects.filter(
            status='published').order_by('-tanggal_publikasi')

        if kategori:
            articles = articles.filter(kategori=kategori)

        if search:
            articles = articles.filter(
                Q(judul__icontains=search) |
                Q(konten__icontains=search) |
                Q(penulis__icontains=search)
            )

        if featured and featured.lower() == 'true':
            articles = articles.filter(featured=True)

        # Batasi hasil untuk pagination
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        articles = articles[offset:offset+limit]

        serializer = ArtikelListSerializer(articles, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET'])
def get_article(request: Request, slug):
    """
    Mendapatkan detail artikel berdasarkan slug
    """
    try:
        artikel = get_object_or_404(Artikel, slug=slug, status='published')

        # Tambahkan jumlah tampilan
        artikel.tampilan = F('tampilan') + 1
        artikel.save(update_fields=['tampilan'])
        artikel.refresh_from_db()

        serializer = ArtikelDetailSerializer(artikel)
        return JsonResponse(serializer.data, safe=False, status=200)

    except Artikel.DoesNotExist:
        return JsonResponse({'error': 'Artikel tidak ditemukan'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_article(request: Request):
    """
    Membuat artikel baru (hanya admin)
    """
    try:
        serializer = ArtikelCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            artikel = serializer.save()
            return JsonResponse({
                'message': 'Artikel berhasil dibuat',
                'artikel': ArtikelDetailSerializer(artikel).data
            }, status=201)
        return JsonResponse({'error': serializer.errors}, status=400)

    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def update_article(request: Request, slug):
    """
    Memperbarui artikel (hanya admin)
    """
    try:
        artikel = get_object_or_404(Artikel, slug=slug)

        # Partial update jika PATCH
        partial = request.method == 'PATCH'

        serializer = ArtikelCreateUpdateSerializer(
            artikel,
            data=request.data,
            partial=partial
        )

        if serializer.is_valid():
            artikel = serializer.save()
            return JsonResponse({
                'message': 'Artikel berhasil diperbarui',
                'artikel': ArtikelDetailSerializer(artikel).data
            }, status=200)

        return JsonResponse({'error': serializer.errors}, status=400)

    except Artikel.DoesNotExist:
        return JsonResponse({'error': 'Artikel tidak ditemukan'}, status=404)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_article(request: Request, slug):
    """
    Menghapus artikel (hanya admin)
    """
    try:
        artikel = get_object_or_404(Artikel, slug=slug)
        artikel.delete()
        return JsonResponse({'message': 'Artikel berhasil dihapus'}, status=200)

    except Artikel.DoesNotExist:
        return JsonResponse({'error': 'Artikel tidak ditemukan'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET'])
def get_article_categories(request: Request):
    """
    Mendapatkan daftar kategori artikel
    """
    try:
        categories = [{'id': id, 'name': name}
                      for id, name in Artikel.kategori_choices]
        return JsonResponse(categories, safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET'])
def get_articles_by_category(request: Request, kategori):
    """
    Mendapatkan artikel berdasarkan kategori
    """
    try:
        valid_categories = dict(Artikel.kategori_choices).keys()
        if kategori not in valid_categories:
            return JsonResponse(
                {"error": f"Kategori tidak valid. Pilih dari: {', '.join(valid_categories)}"},
                status=400
            )

        articles = Artikel.objects.filter(
            kategori=kategori, status='published')
        serializer = ArtikelListSerializer(articles, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET'])
def get_featured_articles(request: Request):
    """
    Mendapatkan artikel yang difeature
    """
    try:
        featured = Artikel.objects.filter(
            featured=True, status='published').order_by('-tanggal_publikasi')[:5]
        serializer = ArtikelListSerializer(featured, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# ===== Komentar APIs =====


@api_view(['POST'])
def create_comment(request: Request):
    """
    Membuat komentar baru
    """
    try:
        serializer = KomentarCreateSerializer(data=request.data)
        if serializer.is_valid():
            komentar = serializer.save()
            return JsonResponse({
                'message': 'Komentar berhasil dibuat dan menunggu persetujuan',
                'komentar': KomentarSerializer(komentar).data
            }, status=201)
        return JsonResponse({'error': serializer.errors}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET'])
def get_comments_by_article(request: Request, article_id):
    """
    Mendapatkan komentar berdasarkan artikel
    """
    try:
        artikel = get_object_or_404(Artikel, id_artikel=article_id)
        komentar = Komentar.objects.filter(artikel=artikel, disetujui=True)
        serializer = KomentarSerializer(komentar, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)

    except Artikel.DoesNotExist:
        return JsonResponse({'error': 'Artikel tidak ditemukan'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_comment(request: Request, comment_id):
    """
    Menyetujui komentar (hanya admin)
    """
    try:
        komentar = get_object_or_404(Komentar, id_komentar=comment_id)
        komentar.approve()
        return JsonResponse({'message': 'Komentar berhasil disetujui'}, status=200)

    except Komentar.DoesNotExist:
        return JsonResponse({'error': 'Komentar tidak ditemukan'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_comment(request: Request, comment_id):
    """
    Menghapus komentar (hanya admin)
    """
    try:
        komentar = get_object_or_404(Komentar, id_komentar=comment_id)
        komentar.delete()
        return JsonResponse({'message': 'Komentar berhasil dihapus'}, status=200)

    except Komentar.DoesNotExist:
        return JsonResponse({'error': 'Komentar tidak ditemukan'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# ===== Tag APIs =====


@api_view(['GET'])
def get_tags(request: Request):
    """
    Mendapatkan daftar tag
    """
    try:
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET'])
def get_articles_by_tag(request: Request, slug):
    """
    Mendapatkan artikel berdasarkan tag
    """
    try:
        tag = get_object_or_404(Tag, slug=slug)
        articles = tag.artikel.filter(status='published')
        serializer = ArtikelListSerializer(articles, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)

    except Tag.DoesNotExist:
        return JsonResponse({'error': 'Tag tidak ditemukan'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_tag(request: Request):
    """
    Membuat tag baru (hanya admin)
    """
    try:
        serializer = TagSerializer(data=request.data)
        if serializer.is_valid():
            tag = serializer.save()
            return JsonResponse({
                'message': 'Tag berhasil dibuat',
                'tag': TagSerializer(tag).data
            }, status=201)
        return JsonResponse({'error': serializer.errors}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_tag(request: Request, slug):
    """
    Menghapus tag (hanya admin)
    """
    try:
        tag = get_object_or_404(Tag, slug=slug)
        tag.delete()
        return JsonResponse({'message': 'Tag berhasil dihapus'}, status=200)

    except Tag.DoesNotExist:
        return JsonResponse({'error': 'Tag tidak ditemukan'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
