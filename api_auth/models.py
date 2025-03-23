import uuid, hashlib, os, base64
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        
        if password:
            user.password_salt = base64.b64encode(os.urandom(32)).decode('utf-8')
            # Use HMAC for more secure password and salt combination
            hashed_password = hashlib.pbkdf2_hmac('sha256', 
                                                password.encode(), 
                                                user.password_salt.encode(), 
                                                100000).hex()
            user.password = hashed_password
        else:
            raise ValueError('The Password field must be set')
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=25, unique=True)
    name = models.CharField(max_length=100, blank=True)
    nomor_telepon = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255)
    password_salt = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        # Simplest possible answer: Yes, always
        return True if self.is_staff else False
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4()
        super().save(*args, **kwargs)

class PetugasManager(models.Manager):
    def create_petugas(self, email, username, password=None, name=None, jabatan=None, nomor_telepon=None, **extra_fields):
        """
        Create and save a Petugas with the given email, username, and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
            
        if not username:
            raise ValueError('The Username field must be set')
            
        if not name:
            # Use username as nama if not provided
            name = username
            
        if not jabatan:
            raise ValueError('The Jabatan field must be set')
        
        # Set Petugas-specific flags
        extra_fields.setdefault('is_staff', True)  # Petugas are staff by default
        
        # Create the User part
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            name=name,
            nomor_telepon=nomor_telepon,
            **extra_fields
        )
        
        # Create the Petugas part that extends User
        petugas = self.model(
            user_ptr=user,
            jabatan=jabatan
        )
        
        # This is required because we're using multi-table inheritance
        petugas.__dict__.update(user.__dict__)
        petugas.save(using=self._db)
        
        return petugas

class Petugas(User):
    """
    Petugas model that inherits from User.
    Adds jabatan (role/position) field.
    """
    jabatan = models.CharField(max_length=100)
    
    objects = PetugasManager()
    
    def __str__(self):
        return f"{self.name} - {self.jabatan}"