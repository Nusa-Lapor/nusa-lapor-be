from django.db import models

# Create your models here.

class Artikel(models.Model):
    judul = models.CharField(max_length=255)
    konten = models.TextField()
    tanggal_publikasi = models.DateTimeField(auto_now_add=True)
    penulis = models.CharField(max_length=100)
    gambar = models.ImageField(upload_to='artikel/', null=True, blank=True)
    
    def __str__(self):
        return self.judul

    def publikasi_artikel(self):
        return True

    class Meta:
        verbose_name = 'Artikel'
        verbose_name_plural = 'Artikel'
