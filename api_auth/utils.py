from rest_framework import serializers
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import os

def get_encryption_key():
    """Get or generate a Fernet encryption key."""
    key = getattr(settings, 'CRYPTOGRAPHY_KEY', None)
    
    if key is None:
        # For development only - in production, use a stable key
        key = os.environ.get('CRYPTOGRAPHY_KEY')
        if not key:
            # Generate a key as last resort
            key = Fernet.generate_key()
            # Store in environment for this process
            os.environ['CRYPTOGRAPHY_KEY'] = key.decode()
            print("key", key.decode())
    
    # Convert string key to bytes if needed
    if isinstance(key, str):
        key = key.encode()
    
    return key

def encrypt_phone_number(phone_number):
    """Encrypt a phone number using Fernet symmetric encryption."""
    if not phone_number:
        return None
    
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(str(phone_number).encode())
    return encrypted.decode()

def decrypt_phone_number(encrypted_phone):
    """Decrypt a phone number that was encrypted with Fernet."""
    if not encrypted_phone:
        return None
    
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_phone.encode())
        return decrypted.decode()
    except Exception as e:
        # Log error but don't expose details
        print(f"Decryption error: {type(e).__name__}")
        return None

# Custom field for handling encrypted phone numbers in serializers
class EncryptedPhoneField(serializers.CharField):
    """
    A serializer field that handles encryption/decryption of phone numbers.
    """
    def __init__(self, **kwargs):
        # Extract the actual phone number length limit (separate from storage length)
        self.phone_max_length = kwargs.pop('phone_max_length', 15) 
        
        # Storage length needs to be much longer for the encrypted value
        kwargs.setdefault('max_length', 255)
        
        super().__init__(**kwargs)

    def to_representation(self, value):
        """When serializing, decrypt the phone number if it's encrypted."""
        if value and isinstance(value, str) and value.startswith('gAAA'):
            # Looks like an encrypted value, decrypt it
            return decrypt_phone_number(value)
        return value

    def to_internal_value(self, data):
        """When deserializing, validate length and then encrypt."""
        # Skip validation for empty values
        if not data:
            return data
        
        # Skip length validation if the data is already encrypted
        if isinstance(data, str) and data.startswith('gAAA') and len(decrypt_phone_number(data)) <= self.phone_max_length:
            # It's already encrypted, just return it
            return data
            
        # Validate the raw phone number length before any processing
        if len(str(data)) > self.phone_max_length:
            raise serializers.ValidationError(
                f"Phone number must be {self.phone_max_length} characters or less."
            )
            
        # Now process normally with CharField validation
        value = super().to_internal_value(data)
        
        # Encrypt if not already encrypted
        if value and not (isinstance(value, str) and value.startswith('gAAA')):
            return encrypt_phone_number(value)
            
        return value

# Example serializer that uses the EncryptedPhoneField
class PhoneNumberSerializer(serializers.Serializer):
    """
    A sample serializer demonstrating how to use the EncryptedPhoneField.
    """
    phone = EncryptedPhoneField(allow_blank=True)

# Mixin for model serializers to handle encrypted phone fields
class EncryptedPhoneSerializerMixin:
    """
    A mixin for serializers that automatically encrypts/decrypts phone fields.
    
    Usage:
    class UserSerializer(EncryptedPhoneSerializerMixin, serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ['id', 'username', 'nomor_telepon']
            encrypted_fields = ['nomor_telepon']  # Specify which fields should be encrypted
    """
    def to_representation(self, instance):
        """Decrypt encrypted fields when serializing."""
        representation = super().to_representation(instance)
        
        encrypted_fields = getattr(self.Meta, 'encrypted_fields', [])
        for field_name in encrypted_fields:
            if field_name in representation and representation[field_name]:
                value = representation[field_name]
                if isinstance(value, str) and value.startswith('gAAA'):
                    representation[field_name] = decrypt_phone_number(value)
                
        return representation

    def to_internal_value(self, data):
        """Encrypt specified fields when deserializing."""
        encrypted_fields = getattr(self.Meta, 'encrypted_fields', [])
        
        for field_name in encrypted_fields:
            if field_name in data and data[field_name]:
                value = data[field_name]
                if not (isinstance(value, str) and value.startswith('gAAA')):
                    data[field_name] = encrypt_phone_number(value)
        
        return super().to_internal_value(data)