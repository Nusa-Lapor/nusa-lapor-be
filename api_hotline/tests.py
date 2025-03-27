from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Hotline
from .serializers import HotlineSerializer

class HotlineModelTests(TestCase):
    def setUp(self):
        """
        Set up data untuk pengujian
        """
        self.hotline_data = {
            'nama': 'Polisi',
            'nomor_telepon': '110',
            'alamat': 'Jl. Trunojoyo No. 3, Jakarta Selatan',
            'website': 'https://www.polri.go.id',
            'layanan': 'Layanan darurat kepolisian 24 jam'
        }
        self.hotline = Hotline.objects.create(**self.hotline_data)

    def test_hotline_creation(self):
        """
        Test pembuatan instance Hotline
        """
        self.assertTrue(isinstance(self.hotline, Hotline))
        self.assertEqual(str(self.hotline), f"{self.hotline.nama} - {self.hotline.nomor_telepon}")

    def test_nama_validation(self):
        """
        Test validasi nama hotline
        """
        # Test nama terlalu pendek
        with self.assertRaises(Exception):
            hotline = Hotline(
                nama='Po',
                nomor_telepon='112',
                alamat='Jl. Test',
                layanan='Test layanan'
            )
            hotline.full_clean()

    def test_nomor_telepon_validation(self):
        """
        Test validasi nomor telepon
        """
        # Test nomor telepon dengan karakter non-digit
        with self.assertRaises(Exception):
            hotline = Hotline(
                nama='Test Hotline',
                nomor_telepon='abc123',
                alamat='Jl. Test',
                layanan='Test layanan'
            )
            hotline.full_clean()

class HotlineSerializerTests(TestCase):
    def setUp(self):
        """
        Set up data untuk pengujian
        """
        self.hotline_data = {
            'nama': 'Ambulans',
            'nomor_telepon': '118',
            'alamat': 'Jl. Kesehatan No. 1, Jakarta Pusat',
            'website': 'www.ambulans.go.id',
            'layanan': 'Layanan ambulans darurat 24 jam'
        }
        self.hotline = Hotline.objects.create(**self.hotline_data)
        self.serializer = HotlineSerializer(instance=self.hotline)

    def test_contains_expected_fields(self):
        """
        Test bahwa serializer memiliki field yang diharapkan
        """
        data = self.serializer.data
        expected_fields = {
            'id_hotline', 'nama', 'nomor_telepon', 'alamat', 'website', 
            'layanan', 'created_at', 'updated_at', 
            'formatted_created_at', 'formatted_updated_at'
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_website_validation(self):
        """
        Test validasi website
        """
        # Test penambahan https:// otomatis
        serializer = HotlineSerializer(data=self.hotline_data)
        self.assertTrue(serializer.is_valid())
        self.assertTrue(serializer.validated_data['website'].startswith('https://'))

class HotlineViewTests(APITestCase):
    def setUp(self):
        """
        Set up data untuk pengujian
        """
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.hotline_data = {
            'nama': 'Pemadam Kebakaran',
            'nomor_telepon': '113',
            'alamat': 'Jl. Api No. 1, Jakarta Timur',
            'website': 'https://www.damkar.go.id',
            'layanan': 'Layanan pemadam kebakaran 24 jam'
        }
        self.hotline = Hotline.objects.create(**self.hotline_data)
        self.list_url = reverse('api_hotline:hotline-list')
        self.detail_url = reverse('api_hotline:hotline-detail', args=[self.hotline.id_hotline])

    def test_get_hotlines_list(self):
        """
        Test mendapatkan daftar hotline
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_hotline_detail(self):
        """
        Test mendapatkan detail hotline
        """
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nama'], self.hotline_data['nama'])

    def test_create_hotline(self):
        """
        Test membuat hotline baru (memerlukan autentikasi admin)
        """
        self.client.force_login(self.admin_user)
        new_hotline = {
            'nama': 'SAR',
            'nomor_telepon': '115',
            'alamat': 'Jl. Penyelamat No. 1, Jakarta Utara',
            'website': 'https://www.sar.go.id',
            'layanan': 'Layanan pencarian dan penyelamatan 24 jam'
        }
        response = self.client.post(
            reverse('api_hotline:hotline-create'),
            new_hotline,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_hotline(self):
        """
        Test mengupdate hotline (memerlukan autentikasi admin)
        """
        self.client.force_login(self.admin_user)
        updated_data = {
            'nama': 'Pemadam Kebakaran Jakarta',
            'layanan': 'Layanan pemadam kebakaran dan penyelamatan 24 jam'
        }
        response = self.client.patch(
            reverse('api_hotline:hotline-update', args=[self.hotline.id_hotline]),
            updated_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['nama'], updated_data['nama'])

    def test_delete_hotline(self):
        """
        Test menghapus hotline (memerlukan autentikasi admin)
        """
        self.client.force_login(self.admin_user)
        response = self.client.delete(
            reverse('api_hotline:hotline-delete', args=[self.hotline.id_hotline])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Hotline.objects.count(), 0)

    def test_call_hotline(self):
        """
        Test endpoint untuk menelepon hotline
        """
        response = self.client.get(
            reverse('api_hotline:hotline-call', args=[self.hotline.id_hotline])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('tel_link' in response.data)
        self.assertEqual(
            response.data['tel_link'],
            f"tel:{self.hotline_data['nomor_telepon']}"
        )
