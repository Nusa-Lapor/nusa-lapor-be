# Generated by Django 5.1.6 on 2025-03-23 15:27

import os
from django.db import migrations
from django.contrib.auth import get_user_model
from api_auth.models import Admin
from api_auth.serializers import AdminSerializer

User = get_user_model()


def create_superuser(apps, schema_editor):
    
    # Check if the superuser already exists
    if not User.objects.filter(username=os.environ.get('SUPERUSER_USERNAME')).exists():
        # Serialize the superuser data
        serializer = AdminSerializer(data={
            'username': os.environ.get('SUPERUSER_USERNAME'),
            'email': os.environ.get('SUPERUSER_EMAIL'),
            'password': os.environ.get('SUPERUSER_PASSWORD'),
            'name': os.environ.get('SUPERUSER_NAME'),
            'nomor_telepon': os.environ.get('SUPERUSER_TELEPON')
        })

        # Validate the superuser data
        if not serializer.is_valid():
            raise Exception(f'Invalid superuser data: {serializer.errors}')
        
        # Extract validated data
        validated_data = serializer.validated_data

        # Create the superuser
        Admin.objects.create_admin(
            email=validated_data.get('email'),
            username=validated_data.get('username'),
            password=validated_data.get('password'),
            name=validated_data.get('name'),
            nomor_telepon=validated_data.get('nomor_telepon')
        )
        print('Superuser created successfully')
    else:
        print('Superuser already exists, skipping creation')

def delete_superuser(apps, schema_editor):
    try:
        User.objects.get(username=os.environ.get('SUPERUSER_USERNAME')).delete()
        print('Superuser deleted successfully')
    except:
        print('Superuser not found, skipping deletion')

class Migration(migrations.Migration):

    initial = True
    
    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_superuser, delete_superuser),
    ]