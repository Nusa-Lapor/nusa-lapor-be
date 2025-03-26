from django.contrib import admin
from .models import Artikel

@admin.register(Artikel)
class ArtikelAdmin(admin.ModelAdmin):
    list_display = ('judul', 'penulis', 'tanggal_publikasi')
    search_fields = ('judul', 'konten', 'penulis')
    list_filter = ('tanggal_publikasi',)
    readonly_fields = ('tanggal_publikasi',)
