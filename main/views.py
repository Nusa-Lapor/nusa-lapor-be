from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from api_auth.models import User
from asgiref.sync import sync_to_async
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncMonth
import random

async def index(request):
    users = await sync_to_async(list)(User.objects.all())
    users_data = [{'id': user.id, 'email': user.email, 'username': user.username, 'name': user.name, 'nomor_telepon': user.nomor_telepon,} for user in users]
    return JsonResponse(users_data, safe=False)

@api_view(['GET'])
def get_statistics(request):
    # Dapatkan data 6 bulan terakhir
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 bulan

    # Generate data dummy yang lebih realistis
    months = []
    current = start_date
    data = []

    # Data dummy dengan tren meningkat
    base_value = 10  # Nilai dasar
    trend_increase = 5  # Peningkatan per bulan
    variation = 3  # Variasi random

    while current <= end_date:
        months.append(current.strftime('%b'))  # Format bulan (Jan, Feb, etc.)
        
        # Hitung nilai dengan tren meningkat dan sedikit variasi random
        month_index = len(data)
        value = base_value + (month_index * trend_increase)
        random_variation = random.randint(-variation, variation)
        final_value = max(0, value + random_variation)  # Pastikan tidak negatif
        
        data.append(final_value)
        current += timedelta(days=30)

    # Batasi hanya 6 bulan
    months = months[:6]
    data = data[:6]

    statistics_data = {
        'labels': months,
        'datasets': [
            {
                'label': 'Jumlah Laporan',
                'data': data,
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            }
        ]
    }

    return Response(statistics_data)
