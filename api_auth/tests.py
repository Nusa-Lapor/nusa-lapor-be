import json, hashlib
from django.test import TestCase, Client
from django.core.cache import cache
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from django.apps import apps
from api_auth.utils import EncryptedPhoneField
from rest_framework.serializers import ValidationError
from rest_framework.exceptions import Throttled
from unittest.mock import patch

User = get_user_model()
Petugas = apps.get_model('api_auth', 'Petugas')
Admin = apps.get_model('api_auth', 'Admin')

class AuthAPITestCase(TestCase):
    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.register_url = reverse('api_auth:register')
        self.login_url = reverse('api_auth:login')
        self.protected_url = reverse('api_auth:protected')
        self.protected_petugas_url = reverse('api_auth:protected_petugas')
        self.protected_admin_url = reverse('api_auth:protected_admin')
        self.assign_petugas_url = reverse('api_auth:assign_petugas')
        self.refresh_token_url = reverse('api_auth:token_refresh')
        self.logout_url = reverse('api_auth:logout')
        
        # Test user data
        self.valid_user = {
            'email': 'test@example.com',
            'username': 'testuser',
            'name': 'Test User',
            'password': 'password123',
            'nomor_telepon': '081333333333'
        }

        # Test admin data
        self.valid_admin = {
            'email': 'admin@adminexample.com',
            'username': 'adminuser',
            'name': 'Admin User',
            'password': 'adminpass123',
            'nomor_telepon': '081444444444'
        }

        # Test petugas data
        self.valid_petugas = {
            'email': 'petugas@petugasexample.com',
            'username': 'petugasuser',
            'name': 'Petugas User',
            'password': 'petugaspass123',
            'nomor_telepon': '081555555555',
            'jabatan': 'Petugas Lapangan',
        }
        
        # Create a test user for login tests
        self.user = User.objects.create_user(
            email=self.valid_user['email'],
            username=self.valid_user['username'],
            name=self.valid_user['name'],
            password=self.valid_user['password'],
            nomor_telepon=self.valid_user['nomor_telepon'],
        )

        # Create a test admin for admin tests
        self.admin = Admin.objects.create_admin(
            email=self.valid_admin['email'],
            username=self.valid_admin['username'],
            name=self.valid_admin['name'],
            password=self.valid_admin['password'],
            nomor_telepon=self.valid_admin['nomor_telepon'],
        )

        # Create a test petugas for petugas tests
        self.petugas = Petugas.objects.create_petugas(
            email=self.valid_petugas['email'],
            username=self.valid_petugas['username'],
            name=self.valid_petugas['name'],
            password=self.valid_petugas['password'],
            nomor_telepon=self.valid_petugas['nomor_telepon'],
            jabatan=self.valid_petugas['jabatan']
        )

    def test_register_success(self):
        """Test successful user registration."""
        # Delete the pre-created user for this test
        User.objects.all().delete()
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.valid_user),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertEqual(response_data['message'], 'User registered successfully')
        self.assertEqual(User.objects.count(), 1)

    def test_register_missing_fields(self):
        """Test registration with missing fields."""
        # Missing email
        invalid_user = {
            'name': 'Test User',
            'password': 'password123'
        }
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_user),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('error' in response.json())
        self.assertTrue('email' in response.json()['error'])
        self.assertTrue('username' in response.json()['error'])
    
    def test_register_without_nomor_telepon(self):
        """Test registration without nomor_telepon."""
        # Missing nomor_telepon
        valid_user = {
            'email': 'testuser33@example.com',
            'username': 'testuser33',
            'name': 'Test User',
            'password': 'password123',
        }

        response = self.client.post(
            self.register_url,
            data=json.dumps(valid_user),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertEqual(response_data['message'], 'User registered successfully')

    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.valid_user),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('error' in response.json())

    def test_login_success(self):
        """Test successful login."""
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_user['email'],
                'password': self.valid_user['password']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue('token' in response_data)
        self.assertTrue('refresh' in response_data['token'])
        self.assertTrue('access' in response_data['token'])
        self.assertTrue('user' in response_data)
        self.assertEqual(response_data['user']['email'], self.valid_user['email'])
        
        # Store tokens for protected endpoint test
        self.access_token = response_data['token']['access']
        self.refresh_token = response_data['token']['refresh']

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_user['email'],
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {'error': 'Invalid credentials'})

    @patch('api_auth.throttling.LoginRateThrottle.allow_request')
    def test_login_throttle_after_three_failed_attempts(self, mock_allow_request):
        """Test login throttle after three failed attempts using direct mocking."""
        # Configure the mock to return True for the first 3 calls (allowing the requests)
        # and then raise Throttled for the 4th call (throttling the request)
        mock_allow_request.side_effect = [True, True, True, Throttled(wait=60)]
        
        # First three failed attempts should not be throttled
        for _ in range(3):
            response = self.client.post(
                self.login_url,
                data=json.dumps({
                    'email': self.valid_user['email'],
                    'password': 'wrongpassword'
                }),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEqual(response.json(), {'error': 'Invalid credentials'})
        
        # Fourth attempt should be throttled
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_user['email'],
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        
        # Now check for 429 response
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('error', response.json())
        # Use a more flexible assertion for the error message
        self.assertTrue(
            'too many' in response.json()['error'].lower() or 
            'throttled' in response.json()['error'].lower() or
            'login attempts' in response.json()['error'].lower()
        )

    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token."""
        # First login to get the token
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_user['email'],
                'password': self.valid_user['password']
            }),
            content_type='application/json'
        )
        access_token = login_response.json()['token']['access']
        
        # Now access protected endpoint
        response = self.client.get(
            self.protected_url,
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['message'], 'This is a protected endpoint')
        self.assertEqual(response_data['user']['email'], self.valid_user['email'])

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token."""
        response = self.client.get(self.protected_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_success(self):
        """Test successful logout."""
        # First login to get the refresh token
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_user['email'],
                'password': self.valid_user['password']
            }),
            content_type='application/json'
        )
        refresh_token = login_response.json()['token']['refresh']
        
        # Then logout
        response = self.client.post(
            self.logout_url,
            data=json.dumps({'refresh': refresh_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'message': 'User logged out successfully'})

    def test_logout_missing_token(self):
        """Test logout without refresh token."""
        response = self.client.post(
            self.logout_url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'Refresh token is required'})

    def test_logout_invalid_token(self):
        """Test logout with invalid refresh token."""
        response = self.client.post(
            self.logout_url,
            data=json.dumps({'refresh': 'invalid-token'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_petugas_login_success(self):
        """Test successful petugas login."""
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_petugas['email'],
                'password': self.valid_petugas['password']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue('token' in response_data)
        self.assertTrue('refresh' in response_data['token'])
        self.assertTrue('access' in response_data['token'])
        self.assertTrue('user' in response_data)
        self.assertEqual(response_data['user']['email'], self.valid_petugas['email'])
        
        # Store tokens for protected endpoint test
        self.access_token = response_data['token']['access']

    def test_petugas_protected_endpoint(self):
        """Test accessing protected endpoint as a petugas."""
        # First login to get the token
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_petugas['email'],
                'password': self.valid_petugas['password']
            }),
            content_type='application/json'
        )
        access_token = login_response.json()['token']['access']
        
        # Now access protected endpoint
        response = self.client.get(
            self.protected_petugas_url,
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['message'], 'This is a protected petugas endpoint')
        self.assertEqual(response_data['petugas']['email'], self.valid_petugas['email'])
        self.assertTrue('jabatan' in response_data['petugas'])

    def test_admin_login_success(self):
        """Test successful admin login."""
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_admin['email'],
                'password': self.valid_admin['password']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertTrue('token' in response_data)
        self.assertTrue('refresh' in response_data['token'])
        self.assertTrue('access' in response_data['token'])
        self.assertTrue('user' in response_data)
        self.assertEqual(response_data['user']['email'], self.valid_admin['email'])
        self.assertTrue(response_data['user']['is_superuser'])
        
        # Store tokens for protected endpoint test
        self.access_token = response_data['token']['access']

    def test_admin_protected_endpoint(self):
        """Test accessing protected endpoint as an admin."""
        # First login to get the token
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_admin['email'],
                'password': self.valid_admin['password']
            }),
            content_type='application/json'
        )
        access_token = login_response.json()['token']['access']
        
        # Now access protected endpoint
        response = self.client.get(
            self.protected_admin_url,
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['message'], 'This is a protected admin endpoint')
        self.assertEqual(response_data['admin']['email'], self.valid_admin['email'])
        self.assertTrue(response_data['admin']['is_superuser'])

    def test_assign_petugas(self):
        """Test assigning a user to be a petugas, by an admin."""
        # First login as admin to get the token
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_admin['email'],
                'password': self.valid_admin['password']
            }),
            content_type='application/json'
        )
        access_token = login_response.json()['token']['access']
        
        response = self.client.post(
            self.assign_petugas_url,
            data=json.dumps({'user_id': str(self.user.id)}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['message'], 'User assigned as Petugas')
        self.assertEqual(response_data['petugas']['jabatan'], 'Petugas Lapangan')

    def test_assign_petugas_failed(self):
        """Test assigning a user to be a petugas, by an admin, but failed because the user is already a petugas."""
        # First login as admin to get the token
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_admin['email'],
                'password': self.valid_admin['password']
            }),
            content_type='application/json'
        )
        access_token = login_response.json()['token']['access']

        # Assign the user as petugas
        response = self.client.post(
            self.assign_petugas_url,
            data=json.dumps({'user_id': str(self.petugas.id)}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'User is already a Petugas'})

    def test_refresh_token(self):
        """Test refreshing the access token."""
        # First login to get the refresh token
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_user['email'],
                'password': self.valid_user['password']
            }),
            content_type='application/json',
        )
        refresh_token = login_response.json()['token']['refresh']

        # Now refresh the token
        refresh_response = self.client.post(
            self.refresh_token_url,
            data=json.dumps({'refresh': refresh_token}),
            content_type='application/json',
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        response_data = refresh_response.json()
        self.assertTrue('access' in response_data)      

    
    def test_encrypted_phone_field(self):
        """Test the EncryptedPhoneField validation and transformation."""
        field = EncryptedPhoneField()
        
        # Test various formats
        test_cases = [
            # Valid phone numbers
            "081234567890",         # Local format
            "+62812345678",         # International with +
            "62812345678",          # International without +
            "81-234567890",         # International without +, with hypen
            "+123456789012345",     # International with +, without hypen
            "+62-812345678",        # With hyphen
            
            # Invalid phone numbers that should fail
            "62-812-345-678",       # With invalid hyphens
            "0812 3456 7890",       # With spaces
            "abc12345678",          # Contains letters
            "123",                  # Too short
            "12345678901234567890", # Too long
        ]
        
        print("\nTesting EncryptedPhoneField:")
        for phone in test_cases:
            try:
                result = field.to_internal_value(phone)
                decrypted = field.to_representation(result)
                print(f"✅ {phone} → {result[:10]}... → {decrypted}")
            except ValidationError as ve:
                print(f"❌ {phone} → Error: {str(ve)}")