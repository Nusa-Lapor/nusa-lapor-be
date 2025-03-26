from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F
from .models import Artikel, Komentar, Tag
from .serializers import (
    ArtikelListSerializer,
    ArtikelDetailSerializer,
    ArtikelCreateUpdateSerializer,
    KomentarSerializer,
    KomentarCreateSerializer,
    TagSerializer
)

# Create your views here.


class ArtikelViewSet(viewsets.ModelViewSet):
    """
    API endpoint untuk artikel.
    """
    queryset = Artikel.objects.filter(
        status='published').order_by('-tanggal_publikasi')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['judul', 'konten', 'penulis', 'kategori']
    ordering_fields = ['tanggal_publikasi', 'tampilan', 'penulis']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return ArtikelListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ArtikelCreateUpdateSerializer
        return ArtikelDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser]
        else:
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.tampilan = F('tampilan') + 1
        instance.save(update_fields=['tampilan'])
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False)
    def featured(self, request):
        """
        Menampilkan artikel yang difeature
        """
        featured = Artikel.objects.filter(
            featured=True, status='published')[:5]
        serializer = ArtikelListSerializer(featured, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def categories(self, request):
        """
        Menampilkan daftar kategori
        """
        categories = [{'id': id, 'name': name}
                      for id, name in Artikel.kategori_choices]
        return Response(categories)

    @action(detail=False, url_path='category/(?P<kategori>[^/.]+)')
    def by_category(self, request, kategori=None):
        """
        Menampilkan artikel berdasarkan kategori
        """
        valid_categories = dict(Artikel.kategori_choices).keys()
        if kategori not in valid_categories:
            return Response(
                {"error": f"Kategori tidak valid. Pilih dari: {', '.join(valid_categories)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        articles = Artikel.objects.filter(
            kategori=kategori, status='published')
        serializer = ArtikelListSerializer(articles, many=True)
        return Response(serializer.data)


class KomentarViewSet(viewsets.ModelViewSet):
    """
    API endpoint untuk komentar.
    """
    queryset = Komentar.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return KomentarCreateSerializer
        return KomentarSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'list', 'approve']:
            self.permission_classes = [permissions.IsAdminUser]
        else:
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """
        Menyetujui komentar
        """
        komentar = self.get_object()
        komentar.approve()
        return Response({'status': 'Komentar disetujui'})

    @action(detail=False)
    def by_article(self, request):
        """
        Menampilkan komentar berdasarkan artikel
        """
        article_id = request.query_params.get('article_id', None)
        if not article_id:
            return Response(
                {"error": "Parameter article_id diperlukan"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            article = Artikel.objects.get(id_artikel=article_id)
        except Artikel.DoesNotExist:
            return Response(
                {"error": "Artikel tidak ditemukan"},
                status=status.HTTP_404_NOT_FOUND
            )

        comments = Komentar.objects.filter(artikel=article, disetujui=True)
        serializer = KomentarSerializer(comments, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    """
    API endpoint untuk tag.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser]
        else:
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()

    @action(detail=True)
    def articles(self, request, slug=None):
        """
        Menampilkan artikel berdasarkan tag
        """
        tag = self.get_object()
        articles = tag.artikel.filter(status='published')
        serializer = ArtikelListSerializer(articles, many=True)
        return Response(serializer.data)
