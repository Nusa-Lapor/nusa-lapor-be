import hashlib, base64
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.request import Request
from django.views.decorators.csrf import csrf_exempt
import json
from .serializers import UserSerializer
from .permissions import IsPetugas, IsAdmin
from .models import User

@csrf_exempt
@api_view(['POST'])
def register(request: Request):
    if request.method == 'POST':
        # Use the serializer to handle data validation and phone encryption
        serializer = UserSerializer(data=request.data)
        
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)
        
        # Extract validated data
        validated_data = serializer.validated_data
        email = validated_data.get('email')
        username = validated_data.get('username')
        name = validated_data.get('name')
        password = validated_data.get('password')
        nomor_telepon = validated_data.get('nomor_telepon', None)
        
        if not email or not username or not password:
            return JsonResponse({'error': 'Email, username, and password are required'}, status=400)

        try:
            # Create the user with the encrypted phone number
            user = User.objects.register(
                email=email,
                username=username,
                name=name,
                password=password,
                nomor_telepon=nomor_telepon,  # Already encrypted by the serializer
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
        user = User.objects.login(email, password)

        if not user:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Add user info to response
        user_data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'name': user.name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        
        # Set session data for Django's session-based auth
        request.session['_auth_user_id'] = str(user.pk)
        request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        request.session.save()
        
        response = JsonResponse({
            'token': {
                'refresh': str(refresh),
                'access': access_token,
            },
            'user': user_data
        })
        
        # Set cookie with the JWT
        response.set_cookie(
            key='jwt',
            value=access_token,
            httponly=True,  # Makes the cookie inaccessible to JavaScript
            samesite='Lax',  # Restricts the cookie from being sent in cross-site requests
            secure=False,  # Set to True in production with HTTPS
        )
        
        return response
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected(request: Request):
    # Get user info from the authenticated request
    user = request.user
    return JsonResponse({
        'message': 'This is a protected endpoint',
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'name': user.name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
    }, status=200)

@api_view(['GET'])
@permission_classes([IsPetugas])
def protected_petugas(request: Request):
    """
    Protected endpoint that only Petugas users can access.
    """
    petugas = request.user.petugas
    return JsonResponse({
        'message': 'This is a protected petugas endpoint',
        'petugas': {
            'id': str(petugas.id),
            'email': petugas.email,
            'username': petugas.username,
            'name': petugas.name,
            'jabatan': petugas.jabatan,
            'is_staff': petugas.is_staff,
            'is_superuser': petugas.is_superuser,
        }
    }, status=200)

@api_view(['GET'])
@permission_classes([IsAdmin])
def protected_admin(request: Request):
    """
    Protected endpoint that only admin users (superusers) can access.
    """
    user = request.user
    
    # Get all users in the system (as an example of admin functionality)
    all_users_count = User.objects.count()
    all_petugas_count = getattr(getattr(User, 'petugas', None), 'objects', None)
    petugas_count = all_petugas_count.count() if all_petugas_count else 0
    
    return JsonResponse({
        'message': 'This is a protected admin endpoint',
        'admin': {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'name': user.name,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff
        },
        'system_stats': {
            'total_users': all_users_count,
            'total_petugas': petugas_count,
        }
    }, status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request: Request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return JsonResponse({'error': 'Refresh token is required'}, status=400)
        
        # Use OutstandingToken if blacklist isn't available
        token = RefreshToken(refresh_token)
        
        # Try to blacklist the token
        try:
            token.blacklist()
        except AttributeError:
            # If blacklisting isn't available, just log it
            print("Token blacklisting is not enabled. Please configure your settings.")
        
        # Clear the session regardless
        request.session.flush()
        
        response = JsonResponse({'message': 'User logged out successfully'}, status=200)
        
        # Remove JWT cookie if it was set during login
        if 'jwt' in request.COOKIES:
            response.delete_cookie('jwt')
            
        return response
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)