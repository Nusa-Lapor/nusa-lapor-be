from django.contrib import admin
from .models import Hotline

@admin.register(Hotline)
class HotlineAdmin(admin.ModelAdmin):
    list_display = ('nama', 'nomor_telepon', 'website', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('nama', 'nomor_telepon', 'alamat', 'layanan')
    readonly_fields = ('id_hotline', 'created_at', 'updated_at')
    ordering = ('nama',)
    
    fieldsets = (
        ('Informasi Utama', {
            'fields': ('id_hotline', 'nama', 'nomor_telepon')
        }),
        ('Detail Layanan', {
            'fields': ('alamat', 'website', 'layanan')
        }),
        ('Informasi Timestamp', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Menjadikan id_hotline, created_at, dan updated_at readonly
        """
        if obj:  # editing an existing object
            return self.readonly_fields
        return ('created_at', 'updated_at')  # creating a new object
