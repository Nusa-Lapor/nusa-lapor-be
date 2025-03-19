import json
import hashlib
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from django.apps import apps

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
            'password': 'password123',
            'nomor_telepon': '081333333333'
        }
        
        # Create a test user for login tests
        hashed_password = hashlib.sha256(self.valid_user['password'].encode()).hexdigest()
        self.user = User.objects.create(
            email=self.valid_user['email'],
            username=self.valid_user['username'],
            name=self.valid_user['name'],
            password=hashed_password,
            nomor_telepon=self.valid_user['nomor_telepon'],
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
        self.assertEqual(response.json(), {
            "error": {
                "email": [
                    "This field is required."
                ],
                "username": [
                    "user with this username already exists."
                ]
            }
        })

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

    def test_admin_protected_endpoint_authorized(self):
        """Test accessing admin protected endpoint with admin token."""
        # Create an admin user
        admin_data = {
            'email': 'admin@example.com',
            'username': 'adminuser',
            'name': 'Admin User',
            'password': 'adminpass123',
            'nomor_telepon': '081444444444'
        }
        
        # Hash the password
        hashed_password = hashlib.sha256(admin_data['password'].encode()).hexdigest()
        
        # Create admin user
        admin = User.objects.create(
            email=admin_data['email'],
            username=admin_data['username'],
            name=admin_data['name'],
            password=hashed_password,
            nomor_telepon=admin_data['nomor_telepon'],
            is_superuser=True,
            is_staff=True
        )
        
        # Login as admin
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': admin_data['email'],
                'password': admin_data['password']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        admin_token = login_response.json()['token']['access']
        
        # Access admin protected endpoint
        admin_url = reverse('api_auth:protected_admin')
        response = self.client.get(
            admin_url,
            HTTP_AUTHORIZATION=f'Bearer {admin_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.json())
        self.assertIn('admin', response.json())
        self.assertEqual(response.json()['admin']['email'], admin_data['email'])

    def test_admin_protected_endpoint_unauthorized(self):
        """Test accessing admin protected endpoint with non-admin token."""
        # Login with regular user
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_user['email'],
                'password': self.valid_user['password']
            }),
            content_type='application/json'
        )
        
        user_token = login_response.json()['token']['access']
        
        # Try to access admin endpoint
        admin_url = reverse('api_auth:protected_admin')
        response = self.client.get(
            admin_url,
            HTTP_AUTHORIZATION=f'Bearer {user_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_petugas_protected_endpoint_authorized(self):
        """Test accessing petugas protected endpoint with petugas token."""
        # Define petugas data
        petugas_data = {
            'email': 'petugas@example.com',
            'username': 'petugasuser',
            'name': 'Petugas User',
            'password': 'petugaspass123',
            'nomor_telepon': '081555555555',
            'jabatan': 'Field Officer'
        }
        
        # Hash the password
        hashed_password = hashlib.sha256(petugas_data['password'].encode()).hexdigest()
        
        # Get the Petugas model
        Petugas = apps.get_model('api_auth', 'Petugas')
        
        # Create petugas user (two steps due to inheritance)
        # First create the User part
        user = User.objects.create(
            email=petugas_data['email'],
            username=petugas_data['username'],
            name=petugas_data['name'],
            password=hashed_password,
            nomor_telepon=petugas_data['nomor_telepon'],
            is_staff=True
        )
        
        # Then create the Petugas part with the same ID
        # This is needed for multi-table inheritance
        petugas = Petugas(
            user_ptr_id=user.id,
            jabatan=petugas_data['jabatan']
        )
        petugas.save_base(raw=True)  # Special save for multi-table inheritance
        
        # Login as petugas
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': petugas_data['email'],
                'password': petugas_data['password']
            }),
            content_type='application/json'
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        petugas_token = login_response.json()['token']['access']
        
        # Access petugas protected endpoint
        petugas_url = reverse('api_auth:protected_petugas')
        response = self.client.get(
            petugas_url,
            HTTP_AUTHORIZATION=f'Bearer {petugas_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.json())
        self.assertIn('petugas', response.json())
        self.assertEqual(response.json()['petugas']['email'], petugas_data['email'])
        self.assertEqual(response.json()['petugas']['jabatan'], petugas_data['jabatan'])

    def test_petugas_protected_endpoint_unauthorized(self):
        """Test accessing petugas protected endpoint with non-petugas token."""
        # Login with regular user
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.valid_user['email'],
                'password': self.valid_user['password']
            }),
            content_type='application/json'
        )
        
        user_token = login_response.json()['token']['access']
        
        # Try to access petugas endpoint
        petugas_url = reverse('api_auth:protected_petugas')
        response = self.client.get(
            petugas_url,
            HTTP_AUTHORIZATION=f'Bearer {user_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_petugas_endpoint_access(self):
        """Test if admin can access petugas endpoint."""
        # Create an admin user
        admin_data = {
            'email': 'admin2@example.com',
            'username': 'adminuser2',
            'name': 'Admin User 2',
            'password': 'adminpass123',
            'nomor_telepon': '081666666666'
        }
        
        # Hash the password
        hashed_password = hashlib.sha256(admin_data['password'].encode()).hexdigest()
        
        # Create admin user
        admin = User.objects.create(
            email=admin_data['email'],
            username=admin_data['username'],
            name=admin_data['name'],
            password=hashed_password,
            nomor_telepon=admin_data['nomor_telepon'],
            is_superuser=True,
            is_staff=True
        )
        
        # Login as admin
        login_response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': admin_data['email'],
                'password': admin_data['password']
            }),
            content_type='application/json'
        )
        
        admin_token = login_response.json()['token']['access']
        
        # Try to access petugas endpoint as admin
        petugas_url = reverse('api_auth:protected_petugas')
        response = self.client.get(
            petugas_url,
            HTTP_AUTHORIZATION=f'Bearer {admin_token}'
        )
        
        # This checks if your implementation allows admins to access petugas endpoints
        # You might want to adjust based on your intended behavior
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # If admins should have access, change to:
        # self.assertEqual(response.status_code, status.HTTP_200_OK)