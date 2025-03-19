from django.shortcuts import render
from django.http import JsonResponse
from api_auth.models import User
from asgiref.sync import sync_to_async

async def index(request):
    users = await sync_to_async(list)(User.objects.all())
    users_data = [{'id': user.id, 'email': user.email, 'username': user.username, 'name': user.name, 'nomor_telepon': user.nomor_telepon,} for user in users]
    return JsonResponse(users_data, safe=False)