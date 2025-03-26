import re
import uuid
import hashlib
import os
import base64
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import slugify


class ArticleManager(models.Manager):
    def create_article(self, judul, konten, gambar=None, penulis=None, kategori='umum'):
        clean_judul = self.validate_judul(judul)
        clean_konten = self.validate_konten(konten)
        clean_kategori = self.validate_kategori(kategori)

        if gambar:
            self.validate_gambar(gambar)

        article = self.create(
            judul=clean_judul,
            konten=clean_konten,
            gambar=gambar,
            penulis=penulis,
            kategori=clean_kategori,
            slug=slugify(clean_judul)
        )
        return article

    def gambar_upload_path(self, instance, filename):
        return os.path.join('artikel', str(instance.id_artikel), filename)

    def validate_judul(self, judul):
        if not judul:
            raise ValidationError('Judul artikel wajib diisi')
        if len(judul) < 5:
            raise ValidationError(
                'Judul artikel terlalu pendek (minimal 5 karakter)')
        if len(judul) > 150:
            raise ValidationError(
                'Judul artikel terlalu panjang (maksimal 150 karakter)')

        clean_judul = re.sub(r'<[^>]*>', '', judul)

        alphanumeric_validator = RegexValidator(
            regex=r'^[a-zA-Z0-9\s.,!?()-:]*$',
            message='Judul hanya boleh berisi huruf, angka, dan tanda baca standar',
            code='invalid_judul'
        )

        sql_injection_validator = RegexValidator(
            regex=r'(?i)(select|insert|update|delete|drop|union|exec|declare|script|\-\-|\/\*|\*\/|@@|@)',
            message='Judul mengandung karakter atau pola yang tidak valid',
            code='invalid_judul',
            inverse_match=True
        )

        try:
            alphanumeric_validator(clean_judul)
            sql_injection_validator(clean_judul)
        except ValidationError as e:
            raise ValidationError(f'Validasi error: {e.message}')

        return clean_judul

    def validate_konten(self, konten):
        if not konten:
            raise ValidationError('Konten artikel wajib diisi')
        if len(konten) < 50:
            raise ValidationError(
                'Konten artikel terlalu pendek (minimal 50 karakter)')

        # Membersihkan tag HTML berbahaya namun mempertahankan format dasar
        allowed_tags = ['p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5',
                        'h6', 'ul', 'ol', 'li', 'strong', 'em', 'blockquote']
        pattern = f'<(?!\/?({"".join([f"{tag}|" for tag in allowed_tags])[:-1]})\s*\/?>)[^>]*>'
        clean_konten = re.sub(pattern, '', konten)

        # Cek untuk SQL Injection dan XSS patterns
        sql_injection_validator = RegexValidator(
            regex=r'(?i)(select\s+\*|insert\s+into|update\s+[a-z]+\s+set|delete\s+from|drop\s+table|union\s+select|exec\s+|declare\s+|script>|onload=|onerror=|<\/script>|\-\-|\||\&\&)',
            message='Konten mengandung karakter atau pola yang tidak valid',
            code='invalid_konten',
            inverse_match=True
        )

        try:
            sql_injection_validator(clean_konten)
        except ValidationError as e:
            raise ValidationError(f'Validasi error: {e.message}')

        return clean_konten

    def validate_gambar(self, file):
        if file:
            VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in VALID_EXTENSIONS:
                raise ValidationError(
                    'Format file tidak valid. Format yang diizinkan: JPG, JPEG, PNG, GIF')

            if file.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError(
                    'Ukuran file terlalu besar (maksimal 5MB)')

    def validate_kategori(self, kategori):
        valid_categories = dict(Artikel.kategori_choices)
        if kategori not in valid_categories:
            raise ValidationError(
                f'Kategori tidak valid. Kategori yang diizinkan: {", ".join(valid_categories.keys())}')
        return kategori


class Artikel(models.Model):
    kategori_choices = [
        ('umum', 'Umum'),
        ('berita', 'Berita'),
        ('pengumuman', 'Pengumuman'),
        ('tips', 'Tips & Tricks'),
        ('tutorial', 'Tutorial'),
        ('event', 'Event'),
    ]

    status_choices = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    id_artikel = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    judul = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    konten = models.TextField()
    gambar = models.ImageField(upload_to='artikel/', null=True, blank=True)
    penulis = models.CharField(max_length=100)
    kategori = models.CharField(
        max_length=20, choices=kategori_choices, default='umum')
    status = models.CharField(
        max_length=15, choices=status_choices, default='draft')
    tanggal_publikasi = models.DateTimeField(auto_now_add=True)
    tanggal_update = models.DateTimeField(auto_now=True)
    tampilan = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)

    objects = ArticleManager()

    class Meta:
        verbose_name = 'Artikel'
        verbose_name_plural = 'Artikel'
        ordering = ['-tanggal_publikasi']

    def __str__(self):
        return self.judul

    def increment_view(self):
        self.tampilan += 1
        self.save(update_fields=['tampilan'])

    def publish(self):
        if self.status != 'published':
            self.status = 'published'
            self.save(update_fields=['status'])

    def archive(self):
        if self.status != 'archived':
            self.status = 'archived'
            self.save(update_fields=['status'])

    def get_preview(self, length=150):
        """Return a short preview of the article content"""
        # Remove HTML tags for preview
        plain_text = re.sub(r'<[^>]*>', '', self.konten)
        if len(plain_text) <= length:
            return plain_text
        return plain_text[:length].rsplit(' ', 1)[0] + '...'


class Komentar(models.Model):
    id_komentar = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    artikel = models.ForeignKey(
        Artikel, on_delete=models.CASCADE, related_name='komentar')
    nama = models.CharField(max_length=100)
    email = models.EmailField()
    isi = models.TextField()
    tanggal = models.DateTimeField(auto_now_add=True)
    disetujui = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Komentar'
        verbose_name_plural = 'Komentar'
        ordering = ['-tanggal']

    def __str__(self):
        return f"Komentar dari {self.nama} pada {self.artikel.judul}"

    def approve(self):
        self.disetujui = True
        self.save(update_fields=['disetujui'])

    def validate_isi(self, isi):
        if not isi:
            raise ValidationError('Komentar tidak boleh kosong')
        if len(isi) < 2:
            raise ValidationError('Komentar terlalu pendek')

        clean_isi = re.sub(r'<[^>]*>', '', isi)

        alphanumeric_validator = RegexValidator(
            regex=r'^[a-zA-Z0-9\s.,!?()-:]*$',
            message='Komentar hanya boleh berisi huruf, angka, dan tanda baca standar',
            code='invalid_komentar'
        )

        sql_injection_validator = RegexValidator(
            regex=r'(?i)(select|insert|update|delete|drop|union|exec|declare|script|\-\-|\/\*|\*\/|@@|@)',
            message='Komentar mengandung karakter atau pola yang tidak valid',
            code='invalid_komentar',
            inverse_match=True
        )

        try:
            alphanumeric_validator(clean_isi)
            sql_injection_validator(clean_isi)
        except ValidationError as e:
            raise ValidationError(f'Validasi error: {e.message}')

        return clean_isi


class Tag(models.Model):
    id_tag = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    nama = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    artikel = models.ManyToManyField(Artikel, related_name='tags')

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tag'
        ordering = ['nama']

    def __str__(self):
        return self.nama

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nama)
        return super().save(*args, **kwargs)


@receiver(post_save, sender=Artikel)
def create_article_slug(sender, instance, created, **kwargs):
    if created and not instance.slug:
        instance.slug = slugify(instance.judul)
        # Jika slug sudah ada, tambahkan bagian dari UUID
        if Artikel.objects.filter(slug=instance.slug).exists():
            instance.slug = f"{instance.slug}-{str(instance.id_artikel)[:8]}"
        instance.save(update_fields=['slug'])
