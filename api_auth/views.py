import hashlib
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.request import Request
from django.views.decorators.csrf import csrf_exempt
import json

User = get_user_model()

@csrf_exempt
@api_view(['POST'])
def register(request: Request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        username = data.get('username')
        name = data.get('name')
        password = data.get('password')

        if not email or not username or not password:
            return JsonResponse({'error': 'Email, username, and password are required'}, status=400)

        # Hash the password with SHA-256
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            user = User.objects.create(
                email=email,
                username=username,
                name=name,
                password=hashed_password
            )
            return JsonResponse({'message': 'User registered successfully'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
@api_view(['POST'])
def login(request: Request):
    data = json.loads(request.body)
    email = data.get('email')
    password = data.get('password')

    try:
        user = User.objects.get(email=email)
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if user.password == hashed_password:
            # Manually set the user in the session
            request.session['_auth_user_id'] = user.pk
            request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid credentials'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected(request: Request):
    return JsonResponse({'message': 'This is a protected endpoint'}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request: Request):
    try:
        refresh_token = request.data['refresh']
        token = RefreshToken(refresh_token)
        token.blacklist()
        request.session.flush()
        return JsonResponse({'message': 'User logged out successfully'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)