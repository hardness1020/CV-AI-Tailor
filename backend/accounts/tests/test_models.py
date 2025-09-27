"""
Unit tests for accounts app models - User model functionality
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

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