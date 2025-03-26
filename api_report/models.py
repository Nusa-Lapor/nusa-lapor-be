import re
import uuid, hashlib, os, base64
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.core.validators import RegexValidator
from api_auth.models import User


# Create your models here.
class ReportManager(models.Manager):
    def create_report(self, id_user, category, evidance, description, location):
        clean_evidance = self.validate_evidance(evidance)
        clean_description = self.validate_description(description)
        clean_location = self.validate_location(location)
        clean_category = self.validate_category(category)
        report = self.create(id_user=id_user, evidance=clean_evidance, description=clean_description, location=clean_location, category=clean_category)
        return report

    def evidance_upload_path(self, instance, filename):
        return os.path.join('evidance', instance.id_report, filename)
    
    def validate_evidance(self, file):
        if not file:
            raise ValidationError('Evidance is required')
        VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov']
        file = os.path.splitext(file.name)[1].lower()
        if file not in VALID_EXTENSIONS:
            raise ValidationError('Invalid file type {}'.format(file))
        
    def validate_description(self, description):
        if not description:
            raise ValidationError('Description is required')
        if len(description) < 10:
            raise ValidationError('Description is too short')
        
        clean_description = re.sub(r'<[^>]*>', '', description)

        alphanumeric_validator = RegexValidator(
            regex=r'^[a-zA-Z0-9\s.,!?()-]*$',
            message='Description can only contain letters, numbers, and basic punctuation',
            code='invalid_description'
        )
        
        sql_injection_validator = RegexValidator(
            regex=r'(?i)(select|insert|update|delete|drop|union|exec|declare|script|\-\-|\/\*|\*\/|@@|@)',
            message='Description contains invalid characters or patterns',
            code='invalid_description',
            inverse_match=True  
        )
        
        try:
            alphanumeric_validator(clean_description)
            sql_injection_validator(clean_description)
        except ValidationError as e:
            raise ValidationError(f'Validation error: {e.message}')
            
        return clean_description
    
    def validate_location(self, location):
        if not location:
            raise ValidationError('Location is required')
        if len(location) < 5:
            raise ValidationError('Location is too short')
        
        clean_location = re.sub(r'<[^>]*>', '', location)

        alphanumeric_validator = RegexValidator(
            regex=r'^[a-zA-Z0-9\s.,!?()-]*$',
            message='Location can only contain letters, numbers, and basic punctuation',
            code='invalid_location'
        )
        
        sql_injection_validator = RegexValidator(
            regex=r'(?i)(select|insert|update|delete|drop|union|exec|declare|script|\-\-|\/\*|\*\/|@@|@)',
            message='Location contains invalid characters or patterns',
            code='invalid_location',
            inverse_match=True  
        )
        
        try:
            alphanumeric_validator(clean_location)
            sql_injection_validator(clean_location)
        except ValidationError as e:
            raise ValidationError(f'Validation error: {e.message}')
            
        return clean_location
    
    def validate_category(self, category):
        if not category:
            raise ValidationError('Category is required')
        if category not in dict(Report.category_choices):
            raise ValidationError(f'Invalid category. Must be one of: {", ".join(dict(Report.category_choices).values())}')
        return category


class Report(models.Model):
    category_choices = [
        ('crime', 'Crime'),
        ('corruption', 'Corruption'),
        ('infrastructure', 'Infrastructure'),
        ('health', 'Health'),
        ('education', 'Education'),
        ('environment', 'Environment'),
        ('other', 'Other'),
    ]

    id_report = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports', default=None)
    evidance = models.FileField()
    description = models.TextField()
    category = models.TextField(choices=category_choices, default='other')
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ReportManager()

    def to_dict(self):
        """Convert report instance to dictionary for JSON serialization"""
        data = {
            'id': str(self.id_report),
            'description': self.description,
            'category': self.category,
            'location': self.location,
            'created_at': self.created_at.isoformat(),
            # 'evidance': self.evidance,
            'status': {
                'keterangan': self.status.keterangan,
                'detail_status': self.status.detail_status,
                'waktu_update': self.status.waktu_update.isoformat()
            } if hasattr(self, 'status') else None
        }
        return data
    
    def get_status(self):
        return self.status

    def update_status(self, new_status, detail, petugas=None):
        """
        Update report status
        Args:
            new_status (str): New status from status_choices
            detail (str): Detail explanation for status change
            petugas (User): Officer handling the report
        """
        if new_status not in dict(Status.status_choices):
            raise ValidationError(f"Invalid status: {new_status}")
        
        if hasattr(self, 'status'):
            self.status.keterangan = new_status
            self.status.detail_status = detail
            if petugas:
                self.status.id_petugas = petugas
            self.status.save()
        else:
            Status.objects.create(
                id_laporan=self,
                keterangan=new_status,
                detail_status=detail,
                id_petugas=petugas
            )

    def update_status_petugas(self, new_status, detail):
        if not hasattr(self, 'status'):
            raise ValidationError("Report has no status")
        
        if new_status not in dict('in_progress', 'completed'):
            raise ValidationError(f"Invalid status: {new_status}")
        
        self.status.keterangan = new_status
        self.status.detail_status = detail
        self.status.save()

    def is_new(self):
        return self.get_status() == 'new'

    def is_in_progress(self):
        return self.get_status() == 'in_progress'

    def is_completed(self):
        return self.get_status() == 'completed'

    def is_rejected(self):
        return self.get_status() == 'rejected'

    # To be implemented in the future
    def assign_officer(self, petugas):
        if not hasattr(self, 'status'):
            raise ValidationError("Report has no status")
        
        self.status.id_petugas = petugas
        self.update_status('in_progress', f'Laporan ditangani oleh {petugas.username}', petugas)

class Status(models.Model):
    status_choices = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected')
    ]

    id_status = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    keterangan = models.CharField(max_length=100, choices=status_choices, default='new')
    detail_status = models.TextField(blank=True, null=True)
    waktu_update = models.DateTimeField(auto_now=True)
    id_petugas = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_statuses')
    id_laporan = models.OneToOneField('Report', on_delete=models.CASCADE, related_name='status')

    def __str__(self):
        return f"Status {self.keterangan} for Report {self.id_laporan.id_report}"
    
    def validate_keterangan(self, keterangan):
            
        clean_keterangan = re.sub(r'<[^>]*>', '', keterangan)
        
        # Validator for allowed characters
        alphanumeric_validator = RegexValidator(
            regex=r'^[a-zA-Z0-9\s.,!?()-]*$',
            message='Keterangan can only contain letters, numbers, and basic punctuation',
            code='invalid_status_keterangan'
        )
        
        # Validator for SQL/script injection patterns
        sql_injection_validator = RegexValidator(
            regex=r'(?i)(select|insert|update|delete|drop|union|exec|declare|script|\-\-|\/\*|\*\/|@@|@)',
            message='Keterangan contains invalid characters or patterns',
            code='invalid_status_keterangan',
            inverse_match=True
        )
        
        try:
            alphanumeric_validator(clean_keterangan)
            sql_injection_validator(clean_keterangan)
        except ValidationError as e:
            raise ValidationError(f'Validation error: {e.message}')
            
        return clean_keterangan

@receiver(post_save, sender=Report)
def create_report_status(sender, instance, created, **kwargs):
    if created:
        Status.objects.create(
            id_laporan=instance,
            keterangan='new',
            detail_status='Laporan baru dibuat dan menunggu verifikasi'
        )