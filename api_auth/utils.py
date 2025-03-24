from rest_framework import serializers
from django.conf import settings
from django.core.validators import RegexValidator
from cryptography.fernet import Fernet
import base64
import os, re

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
    Validates phone format before encryption and handles the encryption process.
    """
    def __init__(self, **kwargs):
        # Set appropriate defaults for field
        kwargs.setdefault('max_length', 255)  # Encrypted value needs space
        kwargs.setdefault('allow_blank', True)
        kwargs.setdefault('required', False)
        
        # Don't use validators directly - we'll handle validation in to_internal_value
        if 'validators' in kwargs:
            self._extra_validators = kwargs.pop('validators')
        else:
            self._extra_validators = []
            
        # Initialize the field
        super().__init__(**kwargs)

    def to_representation(self, value):
        """When serializing, decrypt the phone number if it's encrypted."""
        if not value:
            return value
            
        # Check if the value is encrypted
        if isinstance(value, str) and value.startswith('gAAA'):
            try:
                # Decrypt the phone number
                return decrypt_phone_number(value)
            except Exception as e:
                # If decryption fails, return a placeholder
                print(f"Error decrypting phone number: {e}")
                return "[Encrypted]"
                
        # If not encrypted, return as is
        return value

    def to_internal_value(self, data):
        """
        Validate and encrypt phone number.
        This is where we handle both validation and encryption.
        """
        # Preliminary validation (CharField's validation)
        validated_data = super().to_internal_value(data)
        
        # Skip empty values
        if not validated_data:
            return None
            
        # Skip already encrypted values
        if isinstance(validated_data, str) and validated_data.startswith('gAAA'):
            return validated_data
            
        # Clean the input value
        phone = validated_data.strip()
        
        # Phone number pattern for Indonesian numbers
        # More permissive pattern that should catch all valid formats
        pattern = r'^(\+?\d{1,3}|0)[-\s]?\d{8,12}$'
        
        # Validate the phone format
        if not re.match(pattern, phone):
            raise serializers.ValidationError(
                "Invalid phone number format. Please use a valid Indonesian phone number. "
                "Example: 081234567890, +62812345678, or 0812-3456-7890"
            )
            
        # Transform the phone number to standard format
        # 1. If starts with 0, replace with 62
        # 2. If starts with +62, replace with 62
        # 3. Remove any spaces or hyphens
        
        # First handle the prefix
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif phone.startswith('+62'):
            phone = '62' + phone[3:]
        elif phone.startswith('+'):
            phone = phone[1:]  # Just remove the plus
            
        # Remove any non-digit characters (spaces, hyphens, etc.)
        phone = re.sub(r'\D', '', phone)
        
        # Final check: ensure the number is not too long after transformation
        if len(phone) > 15:  # Standard max phone number length
            raise serializers.ValidationError("Phone number too long after normalization")
            
        # Encrypt the validated and transformed phone number
        try:
            return encrypt_phone_number(phone)
        except Exception as e:
            # If encryption fails, raise a validation error
            print(f"Error encrypting phone number: {e}")
            raise serializers.ValidationError("Error processing phone number")

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get encrypted fields from Meta
        encrypted_fields = getattr(self.Meta, 'encrypted_fields', [])
        
        # Register EncryptedPhoneField for each encrypted field that doesn't have a custom field
        for field_name in encrypted_fields:
            if field_name in self.fields and not isinstance(self.fields[field_name], EncryptedPhoneField):
                # Only replace CharField fields, not custom fields
                if isinstance(self.fields[field_name], serializers.CharField):
                    # Copy existing field attributes
                    field_kwargs = {
                        'required': self.fields[field_name].required,
                        'allow_blank': getattr(self.fields[field_name], 'allow_blank', True),
                        'label': self.fields[field_name].label,
                        'help_text': self.fields[field_name].help_text,
                    }
                    # Replace with EncryptedPhoneField
                    self.fields[field_name] = EncryptedPhoneField(**field_kwargs)
    
    def to_representation(self, instance):
        """Decrypt encrypted fields when serializing."""
        representation = super().to_representation(instance)
        
        encrypted_fields = getattr(self.Meta, 'encrypted_fields', [])
        for field_name in encrypted_fields:
            if field_name in representation and representation[field_name]:
                value = representation[field_name]
                # Skip if already handled by EncryptedPhoneField
                if not isinstance(self.fields.get(field_name), EncryptedPhoneField):
                    if isinstance(value, str) and value.startswith('gAAA'):
                        representation[field_name] = decrypt_phone_number(value)
                
        return representation
    
    def to_internal_value(self, data):
        """
        No need to handle encryption here anymore - the EncryptedPhoneField
        will handle it automatically. This method is kept for backward compatibility.
        """
        return super().to_internal_value(data)