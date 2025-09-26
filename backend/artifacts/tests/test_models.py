"""
Unit tests for artifacts app models
"""

import uuid
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from artifacts.models import (
    Artifact, EvidenceLink, ArtifactProcessingJob, UploadedFile
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