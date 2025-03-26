from django.contrib import admin
from .models import Artikel, Komentar, Tag


class KomentarInline(admin.TabularInline):
    model = Komentar
    extra = 0
    readonly_fields = ['tanggal']
    fields = ['nama', 'email', 'isi', 'disetujui', 'tanggal']


@admin.register(Artikel)
class ArtikelAdmin(admin.ModelAdmin):
    list_display = ['judul', 'penulis', 'kategori', 'status',
                    'tanggal_publikasi', 'tampilan', 'featured']
    list_filter = ['status', 'kategori', 'featured', 'tanggal_publikasi']
    search_fields = ['judul', 'konten', 'penulis']
    prepopulated_fields = {'slug': ('judul',)}
    readonly_fields = ['id_artikel', 'tampilan',
                       'tanggal_publikasi', 'tanggal_update']
    fieldsets = (
        ('Informasi Artikel', {
            'fields': ('judul', 'slug', 'konten', 'penulis', 'gambar')
        }),
        ('Kategori dan Tag', {
            'fields': ('kategori', 'tags')
        }),
        ('Status dan Pengaturan', {
            'fields': ('status', 'featured')
        }),
        ('Info Sistem', {
            'fields': ('id_artikel', 'tampilan', 'tanggal_publikasi', 'tanggal_update'),
            'classes': ('collapse',)
        }),
    )
    inlines = [KomentarInline]

    def save_model(self, request, obj, form, change):
        # Jika artikel baru dan tidak ada penulis
        if not obj.pk and not obj.penulis:
            obj.penulis = request.user.username
        super().save_model(request, obj, form, change)


@admin.register(Komentar)
class KomentarAdmin(admin.ModelAdmin):
    list_display = ['nama', 'email',
                    'get_artikel_judul', 'tanggal', 'disetujui']
    list_filter = ['disetujui', 'tanggal']
    search_fields = ['nama', 'email', 'isi']
    readonly_fields = ['id_komentar', 'tanggal']
    actions = ['approve_comments']

    def get_artikel_judul(self, obj):
        return obj.artikel.judul
    get_artikel_judul.short_description = 'Artikel'

    def approve_comments(self, request, queryset):
        updated = queryset.update(disetujui=True)
        self.message_user(request, f'{updated} komentar telah disetujui.')
    approve_comments.short_description = "Setujui komentar yang dipilih"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['nama', 'slug', 'get_artikel_count']
    search_fields = ['nama']
    prepopulated_fields = {'slug': ('nama',)}
    readonly_fields = ['id_tag']

    def get_artikel_count(self, obj):
        return obj.artikel.count()
    get_artikel_count.short_description = 'Jumlah Artikel'
