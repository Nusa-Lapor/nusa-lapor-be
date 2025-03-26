from rest_framework import serializers
from .models import Artikel, Komentar, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id_tag', 'nama', 'slug']


class KomentarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Komentar
        fields = ['id_komentar', 'nama', 'email',
                  'isi', 'tanggal', 'disetujui']
        read_only_fields = ['id_komentar', 'tanggal', 'disetujui']


class ArtikelListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    preview = serializers.SerializerMethodField()

    class Meta:
        model = Artikel
        fields = ['id_artikel', 'judul', 'slug', 'preview', 'gambar', 'penulis',
                  'kategori', 'tanggal_publikasi', 'tampilan', 'featured', 'tags']
        read_only_fields = ['id_artikel', 'slug',
                            'tanggal_publikasi', 'tampilan']

    def get_preview(self, obj):
        return obj.get_preview(150)


class ArtikelDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    komentar = serializers.SerializerMethodField()

    class Meta:
        model = Artikel
        fields = ['id_artikel', 'judul', 'slug', 'konten', 'gambar', 'penulis',
                  'kategori', 'status', 'tanggal_publikasi', 'tanggal_update',
                  'tampilan', 'featured', 'tags', 'komentar']
        read_only_fields = ['id_artikel', 'slug', 'tanggal_publikasi',
                            'tanggal_update', 'tampilan']

    def get_komentar(self, obj):
        # Hanya menampilkan komentar yang disetujui
        komentar = obj.komentar.filter(disetujui=True)
        return KomentarSerializer(komentar, many=True).data


class ArtikelCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artikel
        fields = ['judul', 'konten', 'gambar',
                  'penulis', 'kategori', 'status', 'featured']

    def validate_judul(self, value):
        return Artikel.objects.validate_judul(Artikel.objects, value)

    def validate_konten(self, value):
        return Artikel.objects.validate_konten(Artikel.objects, value)

    def validate_kategori(self, value):
        return Artikel.objects.validate_kategori(Artikel.objects, value)

    def create(self, validated_data):
        return Artikel.objects.create_article(
            judul=validated_data['judul'],
            konten=validated_data['konten'],
            gambar=validated_data.get('gambar'),
            penulis=validated_data.get('penulis'),
            kategori=validated_data.get('kategori', 'umum')
        )


class KomentarCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Komentar
        fields = ['artikel', 'nama', 'email', 'isi']

    def validate_isi(self, value):
        instance = Komentar()
        return instance.validate_isi(value)
