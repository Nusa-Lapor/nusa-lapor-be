# In admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Petugas

class Admin(UserAdmin):
    list_display = ('email', 'username', 'name', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('name', 'nomor_telepon')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    # Only allow superusers to grant superuser status
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            readonly_fields = readonly_fields + ('is_superuser',)
        return readonly_fields

admin.site.register(User, Admin)