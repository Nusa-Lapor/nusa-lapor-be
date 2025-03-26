from rest_framework import serializers
from .models import User, Petugas, Admin
from .utils import EncryptedPhoneSerializerMixin, EncryptedPhoneField
import base64, os, hashlib

class BaseUserModelSerializer(EncryptedPhoneSerializerMixin, serializers.ModelSerializer):
    """
    Base serializer for user-like models with password and phone number handling.
    """
    password = serializers.CharField(write_only=True, required=True)
    nomor_telepon = EncryptedPhoneField(allow_blank=True, required=False, allow_null=True)
    
    # def update(self, instance, validated_data):
    #     """
    #     Only update fields that are explicitly passed in the request data.
    #     Uses the model's check_password and custom password hashing.
    #     """
    #     # Get the actual request data before validation
    #     request_data = getattr(self, 'initial_data', {})
        
    #     # Handle password separately using the model's custom password hashing
    #     if 'password' in validated_data:
    #         password = validated_data.pop('password')
    #         if password:
    #             # Create salt and hash password as done in UserManager.create_user
    #             instance.password_salt = base64.b64encode(os.urandom(32)).decode('utf-8')
    #             hashed_password = hashlib.pbkdf2_hmac(
    #                 'sha256', 
    #                 password.encode(), 
    #                 instance.password_salt.encode(), 
    #                 100000
    #             ).hex()
    #             instance.password = hashed_password
        
    #     # Only update fields explicitly included in the request
    #     for field in self.Meta.fields:
    #         # Skip id and password (already handled)
    #         if field in ('id', 'password', 'password_salt'):
    #             continue
                
    #         # Only update if explicitly included in the request
    #         if field in request_data:
    #             # If field exists in validated_data, use that value
    #             if field in validated_data:
    #                 setattr(instance, field, validated_data[field])
        
    #     # Save the instance
    #     instance.save()
    #     return instance
    
class UserSerializer(BaseUserModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'name', 'nomor_telepon', 'password']
        read_only_fields = ['id', 'password_salt']
        encrypted_fields = ['nomor_telepon']

class PetugasSerializer(BaseUserModelSerializer):
    class Meta:
        model = Petugas
        fields = ['id', 'email', 'username', 'name', 'jabatan', 'nomor_telepon', 'password']
        read_only_fields = ['id', 'password_salt']
        encrypted_fields = ['nomor_telepon']

class AdminSerializer(BaseUserModelSerializer):
    class Meta:
        model = Admin
        fields = ['id', 'email', 'username', 'name', 'nomor_telepon', 'password']
        read_only_fields = ['id', 'password_salt']
        encrypted_fields = ['nomor_telepon']