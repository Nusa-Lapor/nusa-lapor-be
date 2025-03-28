# Generated by Django 5.1.6 on 2025-03-26 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Artikel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('judul', models.CharField(max_length=255)),
                ('konten', models.TextField()),
                ('tanggal_publikasi', models.DateTimeField(auto_now_add=True)),
                ('penulis', models.CharField(max_length=100)),
                ('gambar', models.ImageField(blank=True, null=True, upload_to='artikel/')),
            ],
            options={
                'verbose_name': 'Artikel',
                'verbose_name_plural': 'Artikel',
            },
        ),
    ]
