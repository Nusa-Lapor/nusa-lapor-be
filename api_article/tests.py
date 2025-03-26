import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.text import slugify
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Artikel, Komentar, Tag
from .serializers import (
    ArtikelListSerializer,
    ArtikelDetailSerializer,
    KomentarSerializer,
    TagSerializer
)

User = get_user_model()


class ArtikelModelTests(TestCase):
    """Test untuk model Artikel"""

    def setUp(self):
        """Set up data untuk pengujian"""
        self.artikel = Artikel.objects.create(
            judul="Artikel Test",
            konten="Ini adalah konten artikel test yang cukup panjang untuk memenuhi validasi panjang minimal.",
            penulis="Admin Test",
            kategori="berita"
        )

    def test_artikel_creation(self):
        """Test pembuatan artikel"""
        self.assertEqual(self.artikel.judul, "Artikel Test")
        self.assertEqual(self.artikel.penulis, "Admin Test")
        self.assertEqual(self.artikel.kategori, "berita")
        self.assertEqual(self.artikel.status, "draft")  # Default status
        self.assertEqual(self.artikel.tampilan, 0)  # Default views
        self.assertFalse(self.artikel.featured)  # Default not featured

    def test_artikel_slug(self):
        """Test slug artikel dibuat dengan benar"""
        self.assertEqual(self.artikel.slug, slugify(self.artikel.judul))

    def test_get_preview(self):
        """Test preview konten artikel"""
        preview = self.artikel.get_preview(20)
        self.assertTrue(len(preview) <= 20)
        self.assertTrue(preview.endswith('...'))

    def test_status_methods(self):
        """Test metode status artikel"""
        self.artikel.publish()
        self.assertEqual(self.artikel.status, "published")

        self.artikel.archive()
        self.assertEqual(self.artikel.status, "archived")

    def test_increment_view(self):
        """Test increment jumlah tampilan"""
        initial_views = self.artikel.tampilan
        self.artikel.increment_view()
        self.assertEqual(self.artikel.tampilan, initial_views + 1)


class KomentarModelTests(TestCase):
    """Test untuk model Komentar"""

    def setUp(self):
        """Set up data untuk pengujian"""
        self.artikel = Artikel.objects.create(
            judul="Artikel dengan Komentar",
            konten="Ini adalah konten artikel test yang cukup panjang untuk memenuhi validasi panjang minimal.",
            penulis="Admin Test",
            kategori="berita"
        )

        self.komentar = Komentar.objects.create(
            artikel=self.artikel,
            nama="Pengguna Test",
            email="pengguna@test.com",
            isi="Komentar uji coba"
        )

    def test_komentar_creation(self):
        """Test pembuatan komentar"""
        self.assertEqual(self.komentar.nama, "Pengguna Test")
        self.assertEqual(self.komentar.email, "pengguna@test.com")
        self.assertEqual(self.komentar.isi, "Komentar uji coba")
        self.assertFalse(self.komentar.disetujui)  # Default not approved

    def test_komentar_approve(self):
        """Test persetujuan komentar"""
        self.assertFalse(self.komentar.disetujui)
        self.komentar.approve()
        self.assertTrue(self.komentar.disetujui)


class TagModelTests(TestCase):
    """Test untuk model Tag"""

    def setUp(self):
        """Set up data untuk pengujian"""
        self.tag = Tag.objects.create(
            nama="Tag Test"
        )

        self.artikel = Artikel.objects.create(
            judul="Artikel dengan Tag",
            konten="Ini adalah konten artikel test yang cukup panjang untuk memenuhi validasi panjang minimal.",
            penulis="Admin Test",
            kategori="berita"
        )

        self.artikel.tags.add(self.tag)

    def test_tag_creation(self):
        """Test pembuatan tag"""
        self.assertEqual(self.tag.nama, "Tag Test")
        self.assertEqual(self.tag.slug, slugify(self.tag.nama))

    def test_tag_artikel_relation(self):
        """Test relasi tag dan artikel"""
        self.assertEqual(self.tag.artikel.count(), 1)
        self.assertEqual(self.artikel.tags.count(), 1)
        self.assertEqual(self.artikel.tags.first(), self.tag)


class ArtikelViewTests(TestCase):
    """Test untuk API artikel"""

    def setUp(self):
        """Set up data dan client untuk pengujian"""
        self.client = APIClient()

        # Buat user admin
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpassword'
        )

        # Buat beberapa artikel untuk testing
        self.artikel1 = Artikel.objects.create(
            judul="Artikel Berita 1",
            konten="Ini adalah konten artikel berita yang cukup panjang untuk memenuhi validasi panjang minimal.",
            penulis="Admin Test",
            kategori="berita",
            status="published"
        )

        self.artikel2 = Artikel.objects.create(
            judul="Artikel Tips 1",
            konten="Ini adalah konten artikel tips yang cukup panjang untuk memenuhi validasi panjang minimal.",
            penulis="Admin Test",
            kategori="tips",
            status="published"
        )

        self.artikel3 = Artikel.objects.create(
            judul="Artikel Featured",
            konten="Ini adalah konten artikel featured yang cukup panjang untuk memenuhi validasi panjang minimal.",
            penulis="Admin Test",
            kategori="berita",
            status="published",
            featured=True
        )

        self.artikel_draft = Artikel.objects.create(
            judul="Artikel Draft",
            konten="Ini adalah konten artikel draft yang cukup panjang untuk memenuhi validasi panjang minimal.",
            penulis="Admin Test",
            kategori="berita",
            status="draft"
        )

    def test_get_articles(self):
        """Test mendapatkan daftar artikel"""
        response = self.client.get('/api/artikel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Hanya artikel yang published yang ditampilkan
        data = json.loads(response.content)
        self.assertEqual(len(data), 3)

    def test_get_articles_by_category(self):
        """Test mendapatkan artikel berdasarkan kategori"""
        response = self.client.get('/api/artikel/category/berita/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content)
        self.assertEqual(len(data), 2)  # 2 artikel berita yang published

    def test_get_featured_articles(self):
        """Test mendapatkan artikel featured"""
        response = self.client.get('/api/artikel/featured/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content)
        self.assertEqual(len(data), 1)  # 1 artikel featured
        self.assertEqual(data[0]['judul'], self.artikel3.judul)

    def test_get_article_detail(self):
        """Test mendapatkan detail artikel"""
        response = self.client.get(f'/api/artikel/{self.artikel1.slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content)
        self.assertEqual(data['judul'], self.artikel1.judul)

        # Test view increment
        self.artikel1.refresh_from_db()
        self.assertEqual(self.artikel1.tampilan, 1)

    def test_get_draft_article_detail(self):
        """Test mendapatkan artikel draft (seharusnya 404)"""
        response = self.client.get(f'/api/artikel/{self.artikel_draft.slug}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_article_unauthorized(self):
        """Test membuat artikel tanpa login (seharusnya ditolak)"""
        data = {
            'judul': 'Artikel Baru',
            'konten': 'Ini adalah konten artikel baru yang cukup panjang untuk memenuhi validasi panjang minimal.',
            'kategori': 'berita'
        }
        response = self.client.post(
            '/api/artikel/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_article_authorized(self):
        """Test membuat artikel sebagai admin"""
        # Login sebagai admin
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'judul': 'Artikel Baru',
            'konten': 'Ini adalah konten artikel baru yang cukup panjang untuk memenuhi validasi panjang minimal.',
            'kategori': 'berita',
            'penulis': 'Admin'
        }
        response = self.client.post(
            '/api/artikel/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Cek apakah artikel berhasil dibuat
        self.assertTrue(Artikel.objects.filter(judul='Artikel Baru').exists())

    def test_update_article(self):
        """Test update artikel sebagai admin"""
        # Login sebagai admin
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'judul': 'Artikel Berita 1 Updated',
            'konten': self.artikel1.konten
        }
        response = self.client.patch(
            f'/api/artikel/{self.artikel1.slug}/update/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Cek apakah artikel berhasil diupdate
        self.artikel1.refresh_from_db()
        self.assertEqual(self.artikel1.judul, 'Artikel Berita 1 Updated')

    def test_delete_article(self):
        """Test menghapus artikel sebagai admin"""
        # Login sebagai admin
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(
            f'/api/artikel/{self.artikel1.slug}/delete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Cek apakah artikel berhasil dihapus
        self.assertFalse(Artikel.objects.filter(
            id_artikel=self.artikel1.id_artikel).exists())


class KomentarViewTests(TestCase):
    """Test untuk API komentar"""

    def setUp(self):
        """Set up data dan client untuk pengujian"""
        self.client = APIClient()

        # Buat user admin
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpassword'
        )

        # Buat artikel untuk komentar
        self.artikel = Artikel.objects.create(
            judul="Artikel Komentar",
            konten="Ini adalah konten artikel untuk pengujian komentar.",
            penulis="Admin Test",
            kategori="berita",
            status="published"
        )

        # Buat komentar
        self.komentar = Komentar.objects.create(
            artikel=self.artikel,
            nama="Pengguna Test",
            email="pengguna@test.com",
            isi="Komentar uji coba",
            disetujui=True
        )

        self.komentar_pending = Komentar.objects.create(
            artikel=self.artikel,
            nama="Pengguna Lain",
            email="lain@test.com",
            isi="Komentar belum disetujui"
        )

    def test_create_comment(self):
        """Test membuat komentar"""
        data = {
            'artikel': str(self.artikel.id_artikel),
            'nama': 'Pengguna Baru',
            'email': 'baru@test.com',
            'isi': 'Komentar baru'
        }
        response = self.client.post(
            '/api/komentar/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Cek apakah komentar berhasil dibuat
        self.assertTrue(Komentar.objects.filter(
            email='baru@test.com').exists())

    def test_get_comments_by_article(self):
        """Test mendapatkan komentar berdasarkan artikel"""
        response = self.client.get(
            f'/api/komentar/article/{self.artikel.id_artikel}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content)
        self.assertEqual(len(data), 1)  # Hanya komentar yang disetujui

    def test_approve_comment(self):
        """Test menyetujui komentar sebagai admin"""
        # Login sebagai admin
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            f'/api/komentar/{self.komentar_pending.id_komentar}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Cek apakah komentar berhasil disetujui
        self.komentar_pending.refresh_from_db()
        self.assertTrue(self.komentar_pending.disetujui)


class TagViewTests(TestCase):
    """Test untuk API tag"""

    def setUp(self):
        """Set up data dan client untuk pengujian"""
        self.client = APIClient()

        # Buat user admin
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpassword'
        )

        # Buat tag
        self.tag = Tag.objects.create(
            nama="Tag Test"
        )

        # Buat artikel dengan tag
        self.artikel = Artikel.objects.create(
            judul="Artikel dengan Tag",
            konten="Ini adalah konten artikel dengan tag untuk pengujian.",
            penulis="Admin Test",
            kategori="berita",
            status="published"
        )

        self.artikel.tags.add(self.tag)

    def test_get_tags(self):
        """Test mendapatkan daftar tag"""
        response = self.client.get('/api/tag/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content)
        self.assertEqual(len(data), 1)

    def test_get_articles_by_tag(self):
        """Test mendapatkan artikel berdasarkan tag"""
        response = self.client.get(f'/api/tag/{self.tag.slug}/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['judul'], self.artikel.judul)

    def test_create_tag(self):
        """Test membuat tag sebagai admin"""
        # Login sebagai admin
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'nama': 'Tag Baru'
        }
        response = self.client.post('/api/tag/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Cek apakah tag berhasil dibuat
        self.assertTrue(Tag.objects.filter(nama='Tag Baru').exists())
