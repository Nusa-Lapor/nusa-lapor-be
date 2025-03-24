from rest_framework import serializers
from .models import User, Petugas, Admin
from .utils import EncryptedPhoneSerializerMixin, EncryptedPhoneField

class UserSerializer(EncryptedPhoneSerializerMixin, serializers.ModelSerializer):
    """Serializer for the User model with encrypted phone number."""
    password = serializers.CharField(write_only=True, required=True)
    nomor_telepon = EncryptedPhoneField(allow_blank=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'name', 'nomor_telepon', 'password']
        encrypted_fields = ['nomor_telepon']
        
class PetugasSerializer(EncryptedPhoneSerializerMixin, serializers.ModelSerializer):
    """Serializer for the Petugas model with encrypted phone number."""
    password = serializers.CharField(write_only=True, required=True)
    nomor_telepon = EncryptedPhoneField(allow_blank=True, required=False, allow_null=True)

    class Meta:
        model = Petugas
        fields = ['id', 'nama', 'nomor_telepon', 'jabatan', 'password']
        encrypted_fields = ['nomor_telepon']

class AdminSerializer(EncryptedPhoneSerializerMixin, serializers.ModelSerializer):
    """Serializer for the Admin model."""
    password = serializers.CharField(write_only=True, required=True)
    nomor_telepon = EncryptedPhoneField(allow_blank=True, required=False, allow_null=True)

    class Meta:
        model = Admin
        fields = ['id', 'email', 'username', 'name', 'nomor_telepon', 'password']
        encrypted_fields = ['nomor_telepon']