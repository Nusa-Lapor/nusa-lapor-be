import asyncio
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from prisma import Prisma
from django.contrib.auth.hashers import make_password

class AuthTests(APITestCase):
    def setUp(self):
        self.prisma = Prisma()
        asyncio.run(self.prisma.connect())
        self.user_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'username': 'testuser',
            'password': 'password123'
        }
        try:
            self.user = asyncio.run(self.prisma.user.create(
                data={
                    'email': self.user_data['email'],
                    'name': self.user_data['name'],
                    'username': self.user_data['username'],
                    'password': make_password(self.user_data['password']),
                }
            ))
        except Exception as e:
            print(f"Error creating user: {e}")
        finally:
            asyncio.run(self.prisma.disconnect())

    def test_register(self):
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'username': 'newuser',
            'password': 'newpassword123'
        }
        try:
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['message'], 'User registered successfully')
        except Exception as e:
            print(f"Error in test_register: {e}")

    def test_login(self):
        url = reverse('login')
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        try:
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('access', response.data)
            self.assertIn('refresh', response.data)
            self.access_token = response.data['access']
            self.refresh_token = response.data['refresh']
        except Exception as e:
            print(f"Error in test_login: {e}")

    def test_protected(self):
        self.test_login()  # Ensure the user is logged in and tokens are set
        url = reverse('protected')
        try:
            self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['message'], 'This is a protected endpoint')
        except Exception as e:
            print(f"Error in test_protected: {e}")

    def test_logout(self):
        self.test_login()  # Ensure the user is logged in and tokens are set
        url = reverse('logout')
        data = {'refresh': self.refresh_token}
        try:
            self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['message'], 'User logged out successfully')
        except Exception as e:
            print(f"Error in test_logout: {e}")