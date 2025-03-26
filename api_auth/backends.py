import hashlib
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class SHA256SaltedAuthBackend(ModelBackend):
    """
    Custom authentication backend for salted SHA-256 passwords.
    
    This backend allows Django admin to authenticate users whose passwords
    are stored as SHA-256 hashes with salt.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
            
        try:
            # Try to find the user by username or email
            if '@' in username:
                user = User.objects.get(email=username)
            else:
                user = User.objects.get(username=username)
                
            # Get the salt
            if not hasattr(user, 'password_salt') or not user.password_salt:
                return None
                
            # Hash the provided password with the stored salt
            hashed_password = hashlib.pbkdf2_hmac(
                'sha256', 
                password.encode(), 
                user.password_salt.encode(), 
                100000  # Use the same iteration count as in your create_user method
            ).hex()
            
            # Compare with stored password
            if user.password == hashed_password:
                return user
                
        except User.DoesNotExist:
            # Run this to mitigate timing attacks
            # This ensures the time taken for failed logins is similar to successful ones
            salt = "dummy-salt-for-timing-attack-mitigation"
            hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            
        return None