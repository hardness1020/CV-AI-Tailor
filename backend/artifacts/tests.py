"""
Unit tests for ft-001: Artifact Upload System
"""

import json
import uuid
from datetime import date
from unittest.mock import patch, Mock
from io import BytesIO
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Artifact, EvidenceLink, ArtifactProcessingJob, UploadedFile
)
from .tasks import (
    process_artifact_upload, extract_pdf_metadata,
    validate_evidence_link, analyze_github_repository
)

User = get_user_model()


class ArtifactModelTests(TestCase):
    """Test cases for Artifact model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_artifact_creation(self):
        """Test basic artifact creation"""
        artifact = Artifact.objects.create(
            user=self.user,
            title='Test Project',
            description='A test project description',
            artifact_type='project',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 1),
            technologies=['Python', 'Django'],
            collaborators=['John Doe']
        )

        self.assertEqual(artifact.title, 'Test Project')
        self.assertEqual(artifact.user, self.user)
        self.assertEqual(artifact.artifact_type, 'project')
        self.assertEqual(len(artifact.technologies), 2)
        self.assertEqual(len(artifact.collaborators), 1)
        self.assertTrue(artifact.created_at)
        self.assertTrue(artifact.updated_at)

    def test_artifact_string_representation(self):
        """Test artifact __str__ method"""
        artifact = Artifact.objects.create(
            user=self.user,
            title='Test Project',
            description='Test description'
        )
        expected = f"Test Project ({self.user.email})"
        self.assertEqual(str(artifact), expected)

    def test_artifact_ordering(self):
        """Test artifact ordering by updated_at"""
        artifact1 = Artifact.objects.create(
            user=self.user,
            title='First Project',
            description='First description'
        )
        artifact2 = Artifact.objects.create(
            user=self.user,
            title='Second Project',
            description='Second description'
        )

        artifacts = Artifact.objects.all()
        self.assertEqual(artifacts[0], artifact2)  # Most recent first
        self.assertEqual(artifacts[1], artifact1)


class EvidenceLinkModelTests(TestCase):
    """Test cases for EvidenceLink model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.artifact = Artifact.objects.create(
            user=self.user,
            title='Test Project',
            description='Test description'
        )

    def test_evidence_link_creation(self):
        """Test evidence link creation"""
        evidence = EvidenceLink.objects.create(
            artifact=self.artifact,
            url='https://github.com/user/repo',
            link_type='github',
            description='Source code repository'
        )

        self.assertEqual(evidence.artifact, self.artifact)
        self.assertEqual(evidence.url, 'https://github.com/user/repo')
        self.assertEqual(evidence.link_type, 'github')
        self.assertTrue(evidence.is_accessible)

    def test_evidence_link_with_file_data(self):
        """Test evidence link with file-specific fields"""
        evidence = EvidenceLink.objects.create(
            artifact=self.artifact,
            url='http://example.com/file.pdf',
            link_type='document',
            description='Project documentation',
            file_path='uploads/file.pdf',
            file_size=1024000,
            mime_type='application/pdf'
        )

        self.assertEqual(evidence.file_size, 1024000)
        self.assertEqual(evidence.mime_type, 'application/pdf')
        self.assertEqual(evidence.file_path, 'uploads/file.pdf')


class ArtifactProcessingJobModelTests(TestCase):
    """Test cases for ArtifactProcessingJob model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.artifact = Artifact.objects.create(
            user=self.user,
            title='Test Project',
            description='Test description'
        )

    def test_processing_job_creation(self):
        """Test processing job creation"""
        job = ArtifactProcessingJob.objects.create(
            artifact=self.artifact,
            status='pending'
        )

        self.assertEqual(job.artifact, self.artifact)
        self.assertEqual(job.status, 'pending')
        self.assertEqual(job.progress_percentage, 0)
        self.assertIsInstance(job.id, uuid.UUID)

    def test_processing_job_completion(self):
        """Test processing job completion"""
        job = ArtifactProcessingJob.objects.create(
            artifact=self.artifact,
            status='processing',
            progress_percentage=50
        )

        # Update to completed
        job.status = 'completed'
        job.progress_percentage = 100
        job.metadata_extracted = {'title': 'Extracted Title'}
        job.save()

        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.progress_percentage, 100)
        self.assertEqual(job.metadata_extracted['title'], 'Extracted Title')


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


class BulkUploadAPITests(APITestCase):
    """Test cases for bulk upload functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    @patch('artifacts.tasks.process_artifact_upload.delay')
    def test_bulk_upload_with_metadata(self, mock_task):
        """Test bulk upload with metadata only"""
        url = reverse('bulk_upload_artifacts')

        metadata = {
            'title': 'Bulk Upload Project',
            'description': 'Created via bulk upload',
            'artifact_type': 'project',
            'technologies': ['Python', 'Django'],
            'evidence_links': [
                {
                    'url': 'https://github.com/user/repo',
                    'type': 'github',
                    'description': 'Source code'
                }
            ]
        }

        data = {'metadata': json.dumps(metadata)}
        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(Artifact.objects.count(), 1)
        self.assertEqual(EvidenceLink.objects.count(), 1)

        # Check that async task was called
        mock_task.assert_called_once()

    @patch('artifacts.tasks.process_artifact_upload.delay')
    def test_bulk_upload_with_files(self, mock_task):
        """Test bulk upload with files"""
        url = reverse('bulk_upload_artifacts')

        # Create a test file
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"fake pdf content",
            content_type="application/pdf"
        )

        metadata = {
            'title': 'Project with Files',
            'description': 'Has uploaded files',
            'artifact_type': 'project'
        }

        data = {
            'metadata': json.dumps(metadata),
            'files': [test_file]
        }

        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(Artifact.objects.count(), 1)
        self.assertEqual(UploadedFile.objects.count(), 1)
        self.assertEqual(EvidenceLink.objects.count(), 1)  # File creates evidence link

    def test_bulk_upload_invalid_metadata(self):
        """Test bulk upload with invalid metadata"""
        url = reverse('bulk_upload_artifacts')

        # Missing required fields
        metadata = {
            'description': 'Missing title'
        }

        data = {'metadata': json.dumps(metadata)}
        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


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


class ArtifactTaskTests(TestCase):
    """Test cases for Celery tasks"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.artifact = Artifact.objects.create(
            user=self.user,
            title='Test Project',
            description='Test description'
        )

    @patch('artifacts.tasks.validate_evidence_link')
    @patch('artifacts.tasks.extract_pdf_metadata')
    def test_process_artifact_upload_task(self, mock_extract_pdf, mock_validate):
        """Test artifact processing task"""
        # Create processing job
        job = ArtifactProcessingJob.objects.create(
            artifact=self.artifact,
            status='pending'
        )

        # Create evidence link
        evidence = EvidenceLink.objects.create(
            artifact=self.artifact,
            url='https://example.com',
            link_type='website'
        )

        # Mock return values
        mock_extract_pdf.return_value = {'title': 'Extracted Title'}
        mock_validate.return_value = {'status': 'success', 'accessible': True}

        # Run task
        process_artifact_upload(self.artifact.id, job.id)

        # Check results
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.progress_percentage, 100)

    def test_extract_pdf_metadata(self):
        """Test PDF metadata extraction"""
        # This would require a real PDF file in test environment
        # For now, test the function handles missing files gracefully
        result = extract_pdf_metadata('nonexistent/path.pdf')
        self.assertEqual(result, {})

    @patch('artifacts.tasks.requests.head')
    def test_validate_evidence_link_success(self, mock_requests):
        """Test successful evidence link validation"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = 'https://example.com'
        mock_response.headers = {'content-type': 'text/html'}
        mock_requests.return_value = mock_response

        evidence = EvidenceLink.objects.create(
            artifact=self.artifact,
            url='https://example.com',
            link_type='website'
        )

        result = validate_evidence_link(evidence)

        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['accessible'])
        evidence.refresh_from_db()
        self.assertTrue(evidence.is_accessible)

    @patch('artifacts.tasks.requests.head')
    def test_validate_evidence_link_failure(self, mock_requests):
        """Test failed evidence link validation"""
        # Mock failed response
        mock_requests.side_effect = Exception('Connection error')

        evidence = EvidenceLink.objects.create(
            artifact=self.artifact,
            url='https://broken-link.com',
            link_type='website'
        )

        result = validate_evidence_link(evidence)

        self.assertEqual(result['status'], 'error')
        self.assertFalse(result['accessible'])
        evidence.refresh_from_db()
        self.assertFalse(evidence.is_accessible)

    @patch('artifacts.tasks.requests.get')
    def test_analyze_github_repository(self, mock_requests):
        """Test GitHub repository analysis"""
        # Mock GitHub API responses
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.json.return_value = {
            'name': 'test-repo',
            'description': 'Test repository',
            'language': 'Python',
            'stargazers_count': 10,
            'forks_count': 2,
            'created_at': '2024-01-01T00:00:00Z',
            'topics': ['django', 'python'],
            'languages_url': 'https://api.github.com/repos/user/test-repo/languages',
            'default_branch': 'main',
            'size': 1000,
            'open_issues_count': 5
        }

        lang_response = Mock()
        lang_response.status_code = 200
        lang_response.json.return_value = {'Python': 12345, 'JavaScript': 5678}

        commits_response = Mock()
        commits_response.status_code = 200
        commits_response.json.return_value = [
            {
                'sha': 'abc123def456',
                'commit': {
                    'message': 'Initial commit',
                    'author': {
                        'name': 'Test Author',
                        'date': '2024-01-01T00:00:00Z'
                    }
                }
            }
        ]

        # Configure side effects for different API calls
        mock_requests.side_effect = [repo_response, lang_response, commits_response]

        result = analyze_github_repository('https://github.com/user/test-repo')

        self.assertEqual(result['name'], 'test-repo')
        self.assertEqual(result['language'], 'Python')
        self.assertEqual(result['stars'], 10)


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