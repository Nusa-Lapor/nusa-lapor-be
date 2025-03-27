from rest_framework import serializers
from .models import Hotline

class HotlineSerializer(serializers.ModelSerializer):
    formatted_created_at = serializers.SerializerMethodField()
    formatted_updated_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Hotline
        fields = [
            'id_hotline',
            'nama',
            'nomor_telepon',
            'alamat',
            'website',
            'layanan',
            'created_at',
            'updated_at',
            'formatted_created_at',
            'formatted_updated_at'
        ]
        read_only_fields = ['id_hotline', 'created_at', 'updated_at']

    def validate_nama(self, value):
        """
        Validasi untuk nama layanan hotline
        """
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Nama harus memiliki minimal 3 karakter")
        return ' '.join(value.split())  # Membersihkan spasi berlebih

    def validate_nomor_telepon(self, value):
        """
        Validasi untuk nomor telepon
        """
        # Menghapus karakter non-digit
        cleaned_number = ''.join(filter(str.isdigit, value))
        
        if not cleaned_number:
            raise serializers.ValidationError("Nomor telepon harus berisi angka")
        
        if len(cleaned_number) < 3:
            raise serializers.ValidationError("Nomor telepon terlalu pendek (minimal 3 digit)")
        
        if len(cleaned_number) > 15:
            raise serializers.ValidationError("Nomor telepon terlalu panjang (maksimal 15 digit)")
        
        return cleaned_number

    def validate_alamat(self, value):
        """
        Validasi untuk alamat
        """
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Alamat harus memiliki minimal 10 karakter")
        return ' '.join(value.split())  # Membersihkan spasi berlebih

    def validate_website(self, value):
        """
        Validasi untuk website
        """
        if value and not (value.startswith('http://') or value.startswith('https://')):
            value = 'https://' + value
        return value

    def validate_layanan(self, value):
        """
        Validasi untuk deskripsi layanan
        """
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Deskripsi layanan harus memiliki minimal 10 karakter")
        return ' '.join(value.split())  # Membersihkan spasi berlebih

    def get_formatted_created_at(self, obj):
        """
        Format tanggal created_at ke format yang lebih mudah dibaca
        """
        return obj.created_at.strftime("%d %B %Y %H:%M:%S")

    def get_formatted_updated_at(self, obj):
        """
        Format tanggal updated_at ke format yang lebih mudah dibaca
        """
        return obj.updated_at.strftime("%d %B %Y %H:%M:%S") 