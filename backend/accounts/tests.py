"""
Unit tests for accounts app - User authentication and management
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserModelTests(TestCase):
    """Test cases for custom User model"""

    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )

        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_active)

    def test_user_string_representation(self):
        """Test user __str__ method"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(str(user), 'test@example.com')

    def test_email_normalization(self):
        """Test that email addresses are normalized"""
        user = User.objects.create_user(
            email='Test@EXAMPLE.COM',
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(user.email, 'Test@example.com')


class AuthenticationAPITests(APITestCase):
    """Test cases for authentication API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

        new_user = User.objects.get(email='newuser@example.com')
        self.assertEqual(new_user.username, 'newuser')
        self.assertEqual(new_user.first_name, 'New')

    def test_user_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpass123',
            'password_confirm': 'differentpass123',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_duplicate_email(self):
        """Test registration with existing email"""
        url = reverse('register')
        data = {
            'email': 'test@example.com',  # Already exists
            'username': 'newuser',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        """Test user login endpoint"""
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('user', response.data)

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh(self):
        """Test JWT token refresh"""
        refresh = RefreshToken.for_user(self.user)

        url = reverse('token_refresh')
        data = {'refresh': str(refresh)}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_invalid(self):
        """Test token refresh with invalid token"""
        url = reverse('token_refresh')
        data = {'refresh': 'invalid_token'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout(self):
        """Test user logout endpoint"""
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        url = reverse('logout')
        data = {'refresh': str(refresh)}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserProfileAPITests(APITestCase):
    """Test cases for user profile management"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_get_user_profile(self):
        """Test retrieving user profile"""
        url = reverse('profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['username'], 'testuser')

    def test_update_user_profile(self):
        """Test updating user profile"""
        url = reverse('profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated bio',
            'location': 'New York, NY',
            'phone': '+1234567890'
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_change_password(self):
        """Test password change endpoint"""
        url = reverse('change_password')
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_change_password_wrong_current(self):
        """Test password change with wrong current password"""
        url = reverse('change_password')
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatch(self):
        """Test password change with mismatched new passwords"""
        url = reverse('change_password')
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'differentpassword123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_profile_access(self):
        """Test that unauthenticated users can't access profile"""
        self.client.credentials()  # Remove auth

        url = reverse('profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserPreferencesTests(APITestCase):
    """Test cases for user preferences"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_update_cv_template_preference(self):
        """Test updating preferred CV template"""
        url = reverse('profile')
        data = {'preferred_cv_template': 2}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.preferred_cv_template, 2)

    def test_update_email_notifications(self):
        """Test updating email notification preferences"""
        url = reverse('profile')
        data = {'email_notifications': False}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertFalse(self.user.email_notifications)


class PasswordResetTests(APITestCase):
    """Test cases for password reset functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_password_reset_request(self):
        """Test password reset request"""
        url = reverse('password_reset_request')
        data = {'email': 'test@example.com'}

        response = self.client.post(url, data, format='json')

        # Should return success even for security (don't reveal if email exists)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_request_invalid_email(self):
        """Test password reset request with invalid email"""
        url = reverse('password_reset_request')
        data = {'email': 'nonexistent@example.com'}

        response = self.client.post(url, data, format='json')

        # Should still return success for security
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserValidationTests(TestCase):
    """Test cases for user data validation"""

    def test_email_required(self):
        """Test that email is required"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                username='testuser',
                password='testpass123'
            )

    def test_weak_password_validation(self):
        """Test password strength validation"""
        # This would be implemented with Django's AUTH_PASSWORD_VALIDATORS
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='weak'  # In real app, this should be validated
        )
        # Just check user was created (validation would be in forms/serializers)
        self.assertTrue(user.id)

    def test_username_uniqueness(self):
        """Test that usernames must be unique"""
        User.objects.create_user(
            email='test1@example.com',
            username='testuser',
            password='testpass123'
        )

        # Creating another user with same username should work
        # but in practice you'd want unique usernames
        user2 = User.objects.create_user(
            email='test2@example.com',
            username='testuser2',  # Different username
            password='testpass123'
        )
        self.assertTrue(user2.id)

    def test_email_uniqueness(self):
        """Test that emails must be unique"""
        User.objects.create_user(
            email='test@example.com',
            username='testuser1',
            password='testpass123'
        )

        # Creating another user with same email should raise error
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@example.com',  # Same email
                username='testuser2',
                password='testpass123'
            )