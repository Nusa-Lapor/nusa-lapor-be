# Generated by Django 5.1.6 on 2025-03-26 12:35

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id_report', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('evidance', models.FileField(upload_to='')),
                ('description', models.TextField()),
                ('category', models.TextField(choices=[('crime', 'Crime'), ('corruption', 'Corruption'), ('infrastructure', 'Infrastructure'), ('health', 'Health'), ('education', 'Education'), ('environment', 'Environment'), ('other', 'Other')], default='other')),
                ('location', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id_status', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('keterangan', models.CharField(choices=[('new', 'New'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('rejected', 'Rejected')], default='new', max_length=100)),
                ('detail_status', models.TextField(blank=True, null=True)),
                ('waktu_update', models.DateTimeField(auto_now=True)),
                ('id_laporan', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='status', to='api_report.report')),
            ],
        ),
    ]
