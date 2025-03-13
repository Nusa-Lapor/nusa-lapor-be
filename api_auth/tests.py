import json
import hashlib
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()

class AuthAPITestCase(TestCase):
    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.register_url = reverse('api_auth:register')
        self.login_url = reverse('api_auth:login')
        self.protected_url = reverse('api_auth:protected')
        self.logout_url = reverse('api_auth:logout')
        
        # Test user data
        self.valid_user = {
            'email': 'test@example.com',
            'username': 'testuser',
            'name': 'Test User',
            'password': 'password123'
        }
        
        # Create a test user for login tests
        hashed_password = hashlib.sha256(self.valid_user['password'].encode()).hexdigest()
        self.user = User.objects.create(
            email=self.valid_user['email'],
            username=self.valid_user['username'],
            name=self.valid_user['name'],
            password=hashed_password
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
        self.assertEqual(response.json(), {'message': 'User registered successfully'})
        self.assertEqual(User.objects.count(), 1)

    def test_register_missing_fields(self):
        """Test registration with missing fields."""
        # Missing email
        invalid_user = {
            'username': 'testuser',
            'name': 'Test User',
            'password': 'password123'
        }
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_user),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'Email, username, and password are required'})

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
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'error': 'Invalid credentials'})

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