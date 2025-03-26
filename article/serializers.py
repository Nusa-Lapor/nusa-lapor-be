from rest_framework import serializers
from .models import Artikel

class ArtikelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artikel
        fields = ['id', 'judul', 'konten', 'tanggal_publikasi', 'penulis', 'gambar']
        read_only_fields = ['tanggal_publikasi'] 