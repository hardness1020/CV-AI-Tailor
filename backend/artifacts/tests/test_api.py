"""
Unit tests for artifacts app API endpoints
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from artifacts.models import Artifact, ArtifactProcessingJob

User = get_user_model()


class ArtifactAPITests(APITestCase):
    """Test cases for Artifact API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_create_artifact(self):
        """Test artifact creation via API"""
        url = reverse('artifact_list_create')
        data = {
            'title': 'API Test Project',
            'description': 'Created via API',
            'artifact_type': 'project',
            'start_date': '2024-01-01',
            'end_date': '2024-06-01',
            'technologies': ['Python', 'Django', 'React'],
            'collaborators': ['Alice', 'Bob']
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Artifact.objects.count(), 1)

        artifact = Artifact.objects.first()
        self.assertEqual(artifact.title, 'API Test Project')
        self.assertEqual(artifact.user, self.user)
        self.assertEqual(len(artifact.technologies), 3)

    def test_list_artifacts(self):
        """Test listing user's artifacts"""
        # Create test artifacts
        Artifact.objects.create(
            user=self.user,
            title='Project 1',
            description='First project'
        )
        Artifact.objects.create(
            user=self.user,
            title='Project 2',
            description='Second project'
        )

        url = reverse('artifact_list_create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_retrieve_artifact(self):
        """Test retrieving specific artifact"""
        artifact = Artifact.objects.create(
            user=self.user,
            title='Test Project',
            description='Test description'
        )

        url = reverse('artifact_detail', kwargs={'pk': artifact.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Project')

    def test_update_artifact(self):
        """Test updating artifact"""
        artifact = Artifact.objects.create(
            user=self.user,
            title='Original Title',
            description='Original description'
        )

        url = reverse('artifact_detail', kwargs={'pk': artifact.pk})
        data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'technologies': ['Updated Tech']
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artifact.refresh_from_db()
        self.assertEqual(artifact.title, 'Updated Title')

    def test_delete_artifact(self):
        """Test deleting artifact"""
        artifact = Artifact.objects.create(
            user=self.user,
            title='To Delete',
            description='Will be deleted'
        )

        url = reverse('artifact_detail', kwargs={'pk': artifact.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Artifact.objects.count(), 0)

    def test_unauthorized_access(self):
        """Test that unauthenticated users can't access artifacts"""
        self.client.credentials()  # Remove auth

        url = reverse('artifact_list_create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_isolation(self):
        """Test that users can only see their own artifacts"""
        # Create another user with artifact
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='otherpass123'
        )
        Artifact.objects.create(
            user=other_user,
            title='Other User Project',
            description='Should not be visible'
        )

        # Create artifact for current user
        Artifact.objects.create(
            user=self.user,
            title='My Project',
            description='Should be visible'
        )

        url = reverse('artifact_list_create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'My Project')


class ArtifactProcessingStatusAPITests(APITestCase):
    """Test cases for processing status endpoint"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.artifact = Artifact.objects.create(
            user=self.user,
            title='Test Project',
            description='Test description'
        )

    def test_processing_status_success(self):
        """Test successful processing status retrieval"""
        # Create processing job
        job = ArtifactProcessingJob.objects.create(
            artifact=self.artifact,
            status='completed',
            progress_percentage=100
        )

        url = reverse('artifact_processing_status', kwargs={'artifact_id': self.artifact.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['progress_percentage'], 100)

    def test_processing_status_not_found(self):
        """Test processing status for non-existent artifact"""
        url = reverse('artifact_processing_status', kwargs={'artifact_id': 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ArtifactSuggestionsAPITests(APITestCase):
    """Test cases for artifact suggestions endpoint"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_get_all_suggestions(self):
        """Test getting all technology suggestions"""
        url = reverse('artifact_suggestions')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('suggestions', response.data)
        self.assertTrue(len(response.data['suggestions']) > 0)

    def test_filter_suggestions(self):
        """Test filtering technology suggestions"""
        url = reverse('artifact_suggestions')
        response = self.client.get(url, {'q': 'python'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        suggestions = response.data['suggestions']

        # All suggestions should contain 'python' (case insensitive)
        for suggestion in suggestions:
            self.assertIn('python', suggestion.lower())