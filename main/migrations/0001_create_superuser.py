# Generated by Django 5.1.6 on 2025-03-17 03:57

import os
from django.db import migrations
from django.contrib.auth import get_user_model

def create_superuser(apps, schema_editor):
    User = get_user_model()
    
    # Check if the superuser already exists
    if not User.objects.filter(username=os.environ.get('SUPERUSER_USERNAME')).exists():
        User.objects.create_superuser(
            username=os.environ.get('SUPERUSER_USERNAME'),
            email=os.environ.get('SUPERUSER_EMAIL'),
            password=os.environ.get('SUPERUSER_PASSWORD'),
        )
        print('Superuser created successfully')
    else:
        print('Superuser already exists, skipping creation')

def delete_superuser(apps, schema_editor):
    User = get_user_model()
    try:
        User.objects.get(username=os.environ.get('SUPERUSER_USERNAME')).delete()
        print('Superuser deleted successfully')
    except:
        print('Superuser not found, skipping deletion')

class Migration(migrations.Migration):

    dependencies = [

    ]

    operations = [
        migrations.RunPython(create_superuser, delete_superuser),
    ]
