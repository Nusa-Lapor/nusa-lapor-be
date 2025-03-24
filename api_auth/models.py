import uuid, hashlib, os, base64, re
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError

class UserManager(BaseUserManager):
    """
    Custom user manager for handling user creation and authentication in the system.
    This manager extends Django's BaseUserManager to provide custom methods for creating
    users and superusers with email as the primary identifier. It implements secure 
    password hashing using PBKDF2 with SHA-256 and a unique salt for each user.
    **Methods:**
        create_user(email, username, password=None, **extra_fields):
            Creates and saves a User with the given email, username and password.
        create_superuser(email, username, password=None, **extra_fields):
            Creates and saves a superuser with the given email, username and password.
        check_password(raw_password):
            Verifies if the provided raw password matches the stored hashed password.
            Handles both Django's native format and custom SHA-256 format with salt.
    Raises:
        ValueError: If email or password is not provided during user creation.
    """
    def create_user(self, email, username, password=None, **extra_fields):
        """
        Create and save a User with the given email, username and password.
        """
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
        """
        Create and save a superuser with the given email, username and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, username, password, **extra_fields)
    
    def register(self, email, username, name, password, nomor_telepon=None, **extra_fields):
        """
        Register a new user with validation checks.
        
        Args:
            email: User's email address
            username: Unique username
            name: User's full name
            password: User's password
            nomor_telepon: User's phone number (optional)
            **extra_fields: Additional fields
            
        Returns:
            The created user if successful
            
        Raises:
            ValidationError: If input data doesn't meet requirements
        """
        # Email validation
        if not email:
            raise ValidationError('Email is required')
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValidationError('Enter a valid email address')
        if self.model.objects.filter(email=email).exists():
            raise ValidationError('Email already in use')
            
        # Username validation
        if not username:
            raise ValidationError('Username is required')
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters')
        if self.model.objects.filter(username=username).exists():
            raise ValidationError('Username already in use')
            
        # Password validation
        if not password:
            raise ValidationError('Password is required')
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters')
            
        # Name validation
        if not name:
            raise ValidationError('Name is required')
            
        # Create the user
        return self.create_user(
            email=email,
            username=username,
            password=password,
            name=name,
            nomor_telepon=nomor_telepon,
            **extra_fields
        )
    
    def login(self, email, password):
        """
        Authenticate a user by email and password.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        if not email or not password:
            return None
            
        try:
            # Get the user by email
            user = self.model.objects.get(email=email)
            
            # Check if account is active
            if not user.is_active:
                return None
                
            # Check password
            if user.check_password(password):
                return user
                
        except self.model.DoesNotExist:
            # Run the hash function anyway to prevent timing attacks
            hashlib.pbkdf2_hmac('sha256', password.encode(), b'dummy-salt', 100000)
            
        return None
    
    def check_password(self, user, raw_password):
        """
        Check if the raw password matches the one stored in the database.
        
        Args:
            user: User object
            raw_password: Password to check
            
        Returns:
            True if password matches, False otherwise
        """
        if not user.password or not raw_password:
            return False
            
        # Get salt and create hash
        salt = user.password_salt
        hashed_password = hashlib.pbkdf2_hmac(
            'sha256', 
            raw_password.encode(), 
            salt.encode(), 
            100000
        ).hex()
        
        # Compare with stored password
        return user.password == hashed_password

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that extends Django's AbstractBaseUser.
    This model uses email as the primary identifier for authentication.
    
    **Fields:**
        - id: UUIDField, primary key
        - email: EmailField, unique
        - username: CharField, unique
        - name: CharField, optional
        - nomor_telepon: CharField, optional
        - password: CharField, hashed password
        - password_salt: CharField, unique salt for password hashing
        - is_active: BooleanField, default=True
        - is_staff: BooleanField, default=False
        - is_superuser: BooleanField, default=False
    
    **Methods:**
        __str__():
            Returns the email of the user.
        has_module_perms(app_label):
            Does the user have permissions to view the app `app_label`?
        save(*args, **kwargs):
            Override the save method to generate a UUID for the user.
        check_password(raw_password):
            Returns a boolean of whether the raw_password was
            correct. This method is needed for Django admin compatibility.
    """
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
    
    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct.
        This method is needed for Django admin compatibility.
        """
        if not self.password or not raw_password:
            return False
            
        # Get salt and create hash
        salt = self.password_salt
        hashed_password = hashlib.pbkdf2_hmac(
            'sha256', 
            raw_password.encode(), 
            salt.encode(), 
            100000
        ).hex()
        
        # Compare with stored password
        return self.password == hashed_password

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
    
class AdminManager(models.Manager):
    """Manager for Admin model."""
    def create_admin(self, email, username, password=None, name=None, nomor_telepon=None, **extra_fields):
        """
        Create and save an Admin with the given email, username, and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        
        if not username:
            raise ValueError('The Username field must be set')
        
        if not name:
            # Use username as name if not provided
            name = username

        # Create the superuser part
        user = User.objects.create_superuser(
            email=email,
            username=username,
            password=password,
            name=name,
            nomor_telepon=nomor_telepon,
            **extra_fields
        )

        # Create the Admin part that extends User
        admin = self.model(
            user_ptr=user
        )

        # This is required because we're using multi-table inheritance
        admin.__dict__.update(user.__dict__)
        admin.save(using=self._db)

        return admin

    def get_queryset(self):
        """Filter queryset to only include superusers."""
        return super().get_queryset().filter(is_superuser=True)
    
class Admin(User):
    """
    Admin model that inherits from User.
    """
    objects = AdminManager()
    
    def __str__(self):
        return f"{self.name} - Admin"