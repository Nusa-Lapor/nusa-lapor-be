import uuid
import re
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class Hotline(models.Model):
    id_hotline = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="ID unik untuk layanan hotline"
    )

    nama = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-]+$',
                message="Nama hanya boleh mengandung huruf, angka, spasi, dan tanda hubung"
            )
        ],
        help_text="Nama layanan hotline"
    )

    nomor_telepon = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\d{3,15}$',
                message="Nomor telepon harus berupa angka (3-15 digit)"
            )
        ],
        help_text="Nomor telepon hotline (contoh: 110, 112, 113, dll)"
    )

    alamat = models.TextField(
        max_length=255,
        help_text="Alamat kantor layanan hotline"
    )

    website = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Website resmi layanan (opsional)"
    )

    layanan = models.TextField(
        help_text="Deskripsi layanan yang disediakan"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hotline"
        verbose_name_plural = "Hotline"
        ordering = ['nama']

    def __str__(self):
        return f"{self.nama} - {self.nomor_telepon}"

    def clean(self):
        # Validasi nama
        if self.nama:
            if len(self.nama.strip()) < 3:
                raise ValidationError({
                    'nama': 'Nama harus memiliki minimal 3 karakter'
                })
            
            # Membersihkan spasi berlebih
            self.nama = ' '.join(self.nama.split())

        # Validasi nomor telepon
        if self.nomor_telepon:
            # Menghapus semua spasi dan tanda hubung
            cleaned_number = re.sub(r'[\s\-]', '', self.nomor_telepon)
            
            # Validasi hanya angka
            if not cleaned_number.isdigit():
                raise ValidationError({
                    'nomor_telepon': 'Nomor telepon hanya boleh berisi angka'
                })

            # Validasi panjang nomor
            if len(cleaned_number) < 3:
                raise ValidationError({
                    'nomor_telepon': 'Nomor telepon terlalu pendek (minimal 3 digit)'
                })
            
            if len(cleaned_number) > 15:
                raise ValidationError({
                    'nomor_telepon': 'Nomor telepon terlalu panjang (maksimal 15 digit)'
                })

            # Simpan nomor yang sudah dibersihkan
            self.nomor_telepon = cleaned_number

        # Validasi alamat
        if self.alamat:
            if len(self.alamat.strip()) < 10:
                raise ValidationError({
                    'alamat': 'Alamat harus memiliki minimal 10 karakter'
                })
            
            # Membersihkan spasi berlebih
            self.alamat = ' '.join(self.alamat.split())

        # Validasi website
        if self.website:
            if not (self.website.startswith('http://') or self.website.startswith('https://')):
                self.website = 'https://' + self.website

        # Validasi layanan
        if self.layanan:
            if len(self.layanan.strip()) < 10:
                raise ValidationError({
                    'layanan': 'Deskripsi layanan harus memiliki minimal 10 karakter'
                })
            
            # Membersihkan spasi berlebih
            self.layanan = ' '.join(self.layanan.split())

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
