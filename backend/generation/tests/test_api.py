"""
Unit tests for generation app API endpoints
"""

import uuid
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from generation.models import (
    JobDescription, GeneratedDocument, CVTemplate,
    GenerationFeedback, SkillsTaxonomy
)
from artifacts.models import Artifact

User = get_user_model()


class CVGenerationAPITests(APITestCase):
    """Test cases for CV Generation API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Create test artifacts
        self.artifact = Artifact.objects.create(
            user=self.user,
            title='E-commerce Platform',
            description='Full-stack web application',
            technologies=['Python', 'Django', 'React']
        )

    @patch('generation.tasks.generate_cv_task.delay')
    def test_generate_cv_request(self, mock_task):
        """Test CV generation request"""
        url = reverse('generate_cv')
        data = {
            'job_description': 'Looking for Python developer with Django experience',
            'company_name': 'TechCorp',
            'role_title': 'Python Developer',
            'template_id': 1,
            'generation_preferences': {
                'tone': 'professional',
                'length': 'detailed'
            }
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('generation_id', response.data)
        self.assertEqual(response.data['status'], 'processing')

        # Check that generation document was created
        self.assertEqual(GeneratedDocument.objects.count(), 1)
        generation = GeneratedDocument.objects.first()
        self.assertEqual(generation.user, self.user)

        # Check that async task was called
        mock_task.assert_called_once()

    def test_generate_cv_invalid_data(self):
        """Test CV generation with invalid data"""
        url = reverse('generate_cv')
        data = {
            'job_description': '',  # Empty description should fail validation
            'company_name': 'TechCorp'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generation_status_completed(self):
        """Test getting status of completed generation"""
        # Create completed generation
        generation = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            status='completed',
            content={
                'professional_summary': 'Experienced developer',
                'key_skills': ['Python', 'Django']
            }
        )

        url = reverse('generation_status', kwargs={'generation_id': generation.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('content', response.data)

    def test_generation_status_processing(self):
        """Test getting status of processing generation"""
        generation = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            status='processing',
            progress_percentage=50
        )

        url = reverse('generation_status', kwargs={'generation_id': generation.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'processing')
        self.assertEqual(response.data['progress_percentage'], 50)

    def test_generation_status_not_found(self):
        """Test getting status of non-existent generation"""
        fake_id = str(uuid.uuid4())
        url = reverse('generation_status', kwargs={'generation_id': fake_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_generations_list(self):
        """Test listing user's generations"""
        # Create test generations
        GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123'
        )
        GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='def456'
        )

        url = reverse('user_generations_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_rate_generation(self):
        """Test rating a generation"""
        generation = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            status='completed'
        )

        url = reverse('rate_generation', kwargs={'generation_id': generation.id})
        data = {
            'rating': 8,
            'feedback': 'Great quality CV'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        generation.refresh_from_db()
        self.assertEqual(generation.user_rating, 8)
        self.assertEqual(generation.user_feedback, 'Great quality CV')

        # Check feedback was created
        self.assertEqual(GenerationFeedback.objects.count(), 1)


class CVTemplateAPITests(APITestCase):
    """Test cases for CV Template API"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Create test templates
        CVTemplate.objects.create(
            name='Modern',
            category='modern',
            description='Modern template',
            is_active=True
        )
        CVTemplate.objects.create(
            name='Classic',
            category='classic',
            description='Classic template',
            is_active=True
        )
        CVTemplate.objects.create(
            name='Inactive',
            category='modern',
            description='Inactive template',
            is_active=False
        )

    def test_list_active_templates(self):
        """Test listing only active templates"""
        url = reverse('cv_templates_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Only active templates

        template_names = [t['name'] for t in response.data['results']]
        self.assertIn('Modern', template_names)
        self.assertIn('Classic', template_names)
        self.assertNotIn('Inactive', template_names)


class GenerationAnalyticsAPITests(APITestCase):
    """Test cases for generation analytics API"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Create test generations with ratings
        GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            status='completed',
            user_rating=8,
            template_id=1
        )
        GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='def456',
            status='completed',
            user_rating=9,
            template_id=1
        )
        GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='ghi789',
            status='failed'
        )

    def test_generation_analytics(self):
        """Test generation analytics endpoint"""
        url = reverse('generation_analytics')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        analytics = response.data
        self.assertEqual(analytics['total_generations'], 3)
        self.assertEqual(analytics['completed_generations'], 2)
        self.assertEqual(analytics['failed_generations'], 1)
        self.assertEqual(analytics['average_rating'], 8.5)  # (8+9)/2


class GenerationAuthorizationTests(APITestCase):
    """Test authorization and user isolation for generation endpoints"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='password123'
        )

    def test_unauthorized_access(self):
        """Test that unauthenticated users can't access generation endpoints"""
        url = reverse('generate_cv')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        url = reverse('user_generations_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_isolation(self):
        """Test that users can only see their own generations"""
        # Create generations for both users
        generation1 = GeneratedDocument.objects.create(
            user=self.user1,
            document_type='cv',
            job_description_hash='abc123'
        )
        generation2 = GeneratedDocument.objects.create(
            user=self.user2,
            document_type='cv',
            job_description_hash='def456'
        )

        # Authenticate as user1
        token = RefreshToken.for_user(self.user1).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # User1 should only see their generation
        url = reverse('user_generations_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(generation1.id))

        # User1 should not be able to access user2's generation
        url = reverse('generation_status', kwargs={'generation_id': generation2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)