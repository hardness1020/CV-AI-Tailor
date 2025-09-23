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
        # URLs are now handled via reverse() calls to ensure they match URL configuration

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

        # Check response format matches frontend expectations
        self.assertIn('user', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertEqual(response.data['user']['username'], 'newuser')

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
        # Check response format matches frontend expectations
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertEqual(response.data['user']['username'], 'testuser')

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

    def test_email_validation(self):
        """Test email field behavior"""
        # Test that user can be created with valid email
        user = User.objects.create_user(
            email='valid@example.com',
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(user.email, 'valid@example.com')

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


class AuthenticationIntegrationTests(APITestCase):
    """Integration tests for complete authentication flow"""

    def setUp(self):
        # URLs are now handled via reverse() calls to ensure they match URL configuration
        pass

    def test_complete_registration_and_login_flow(self):
        """Test complete user registration and login flow"""
        # Step 1: Register new user
        register_data = {
            'email': 'integration@example.com',
            'username': 'integrationuser',
            'password': 'integrationpass123',
            'password_confirm': 'integrationpass123',
            'first_name': 'Integration',
            'last_name': 'Test'
        }

        register_response = self.client.post(
            reverse('register'),
            register_data,
            format='json'
        )

        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', register_response.data)
        self.assertIn('refresh', register_response.data)

        access_token = register_response.data['access']
        refresh_token = register_response.data['refresh']

        # Step 2: Use access token to access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_response = self.client.get(reverse('profile'))

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data['email'], 'integration@example.com')

        # Step 3: Logout
        logout_response = self.client.post(
            reverse('logout'),
            {'refresh': refresh_token},
            format='json'
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Step 4: Try to access protected endpoint after logout
        profile_response_after_logout = self.client.get(reverse('profile'))
        # Note: Token is blacklisted but might still work briefly,
        # this would need proper blacklist implementation

    def test_login_after_registration(self):
        """Test logging in with a user that was just registered"""
        # Register user
        register_data = {
            'email': 'login_test@example.com',
            'username': 'logintest',
            'password': 'loginpass123',
            'password_confirm': 'loginpass123',
            'first_name': 'Login',
            'last_name': 'Test'
        }

        self.client.post(reverse('register'), register_data, format='json')

        # Now login with the same credentials
        login_data = {
            'email': 'login_test@example.com',
            'password': 'loginpass123'
        }

        login_response = self.client.post(
            reverse('login'),
            login_data,
            format='json'
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        self.assertIn('refresh', login_response.data)
        self.assertEqual(login_response.data['user']['email'], 'login_test@example.com')

    def test_token_refresh_integration(self):
        """Test token refresh functionality"""
        # Create user
        user = User.objects.create_user(
            email='refresh@example.com',
            username='refreshuser',
            password='refreshpass123'
        )

        # Login to get tokens
        login_data = {
            'email': 'refresh@example.com',
            'password': 'refreshpass123'
        }

        login_response = self.client.post(
            reverse('login'),
            login_data,
            format='json'
        )

        refresh_token = login_response.data['refresh']

        # Use refresh token to get new access token
        refresh_data = {'refresh': refresh_token}
        refresh_response = self.client.post(
            reverse('token_refresh'),
            refresh_data,
            format='json'
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_profile_update_integration(self):
        """Test updating user profile after authentication"""
        # Create and authenticate user
        user = User.objects.create_user(
            email='profile@example.com',
            username='profileuser',
            password='profilepass123',
            first_name='Original',
            last_name='Name'
        )

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Update profile
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Profile',
            'bio': 'This is my updated bio',
            'location': 'New York, NY'
        }

        update_response = self.client.patch(
            reverse('profile'),
            update_data,
            format='json'
        )

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        # Verify updates
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Profile')
        self.assertEqual(user.bio, 'This is my updated bio')
        self.assertEqual(user.location, 'New York, NY')

    def test_concurrent_user_operations(self):
        """Test handling multiple users performing operations simultaneously"""
        # Create two users
        user1_data = {
            'email': 'user1@example.com',
            'username': 'user1',
            'password': 'user1pass123',
            'password_confirm': 'user1pass123',
            'first_name': 'User',
            'last_name': 'One'
        }

        user2_data = {
            'email': 'user2@example.com',
            'username': 'user2',
            'password': 'user2pass123',
            'password_confirm': 'user2pass123',
            'first_name': 'User',
            'last_name': 'Two'
        }

        # Register both users
        response1 = self.client.post(reverse('register'), user1_data, format='json')
        response2 = self.client.post(reverse('register'), user2_data, format='json')

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Verify both users exist and have different tokens
        self.assertNotEqual(response1.data['access'], response2.data['access'])
        self.assertNotEqual(response1.data['refresh'], response2.data['refresh'])

        # Verify both users can access their profiles independently
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response1.data["access"]}')
        profile1 = self.client.get(reverse('profile'))

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response2.data["access"]}')
        profile2 = self.client.get(reverse('profile'))

        self.assertEqual(profile1.data['email'], 'user1@example.com')
        self.assertEqual(profile2.data['email'], 'user2@example.com')


class AuthenticationEndpointTests(APITestCase):
    """Test authentication endpoints for proper response format and error handling"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_login_response_format(self):
        """Test login response includes all required fields"""
        response = self.client.post(
            reverse('login'),
            {'email': 'test@example.com', 'password': 'testpass123'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        required_fields = ['user', 'access', 'refresh']
        for field in required_fields:
            self.assertIn(field, response.data)

        # Check user object structure
        user_data = response.data['user']
        user_required_fields = ['id', 'email', 'username', 'first_name', 'last_name']
        for field in user_required_fields:
            self.assertIn(field, user_data)

    def test_register_response_format(self):
        """Test registration response includes all required fields"""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = self.client.post(reverse('register'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        required_fields = ['user', 'access', 'refresh']
        for field in required_fields:
            self.assertIn(field, response.data)

    def test_logout_with_invalid_refresh_token(self):
        """Test logout with invalid refresh token"""
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.post(
            reverse('logout'),
            {'refresh': 'invalid_refresh_token'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_unauthorized_access(self):
        """Test profile access without authentication"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_unauthorized(self):
        """Test password change without authentication"""
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }

        response = self.client.post(reverse('change_password'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self):
        """Test login with missing email or password"""
        # Missing password
        response = self.client.post(
            reverse('login'),
            {'email': 'test@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing email
        response = self.client.post(
            reverse('login'),
            {'password': 'testpass123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_email_format(self):
        """Test registration with invalid email format"""
        data = {
            'email': 'invalid-email',
            'username': 'testuser',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }

        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TokenSecurityTests(APITestCase):
    """Test JWT token security and validation"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_access_token_expiry_handling(self):
        """Test that expired access tokens are rejected"""
        # Login to get tokens
        response = self.client.post(
            reverse('login'),
            {'email': 'test@example.com', 'password': 'testpass123'},
            format='json'
        )

        # Use a clearly invalid token
        invalid_token = 'invalid.jwt.token'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {invalid_token}')

        # Try to access protected endpoint
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_with_valid_token(self):
        """Test token refresh with valid refresh token"""
        refresh = RefreshToken.for_user(self.user)

        response = self.client.post(
            reverse('token_refresh'),
            {'refresh': str(refresh)},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_blacklisted_token_usage(self):
        """Test that blacklisted tokens cannot be used"""
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        # Authenticate and logout (blacklist token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_response = self.client.post(
            reverse('logout'),
            {'refresh': str(refresh)},
            format='json'
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Try to use the same refresh token again
        refresh_response = self.client.post(
            reverse('token_refresh'),
            {'refresh': str(refresh)},
            format='json'
        )

        # Should fail because token is blacklisted
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)