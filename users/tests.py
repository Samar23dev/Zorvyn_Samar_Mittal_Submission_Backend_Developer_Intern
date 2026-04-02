from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        
    def test_register_login(self):
        # Register
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        
        # Login
        login_data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_me_view(self):
        me_url = '/api/auth/me/'
        # Unauthenticated
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Authenticated
        admin = User.objects.create_user(username='admintest', password='password', role='ADMIN')
        self.client.force_authenticate(user=admin)
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'admintest')
        self.assertEqual(response.data['role'], 'ADMIN')

class UserManagementTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='password', role='ADMIN')
        self.viewer = User.objects.create_user(username='viewer', password='password', role='VIEWER')
        self.target_user = User.objects.create_user(username='target', password='password', role='VIEWER')
        
    def test_non_admin_cannot_access_users(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_user_deactivation(self):
        self.client.force_authenticate(user=self.admin)
        url = f'/api/auth/users/{self.target_user.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Row preserved, is_active=False
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)
        self.assertEqual(User.objects.count(), 3)  # admin, viewer, target

    def test_admin_can_access_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_admin_can_update_roles(self):
        self.client.force_authenticate(user=self.admin)
        url = f'/api/auth/users/{self.target_user.id}/'
        response = self.client.patch(url, {'role': 'ANALYST'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.role, 'ANALYST')
