from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from artifacts.models import Artifact, EvidenceLink, UploadedFile
from artifacts.serializers import (
    ArtifactUpdateSerializer, EvidenceLinkCreateSerializer,
    EvidenceLinkUpdateSerializer, BulkArtifactUpdateSerializer
)

User = get_user_model()


class ArtifactEditingAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword'
        )
        self.other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='testpassword'
        )

        # Create JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        # Create test artifacts
        self.artifact = Artifact.objects.create(
            user=self.user,
            title='Test Project',
            description='Test description',
            artifact_type='project',
            technologies=['Python', 'Django'],
            collaborators=['john@example.com']
        )

        self.other_artifact = Artifact.objects.create(
            user=self.other_user,
            title='Other User Project',
            description='Other description',
            artifact_type='project'
        )

    def test_partial_update_artifact(self):
        """Test partial artifact update with PATCH"""
        url = reverse('artifact_detail', kwargs={'pk': self.artifact.pk})
        data = {
            'title': 'Updated Project Title',
            'description': 'Updated description'
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.artifact.refresh_from_db()
        self.assertEqual(self.artifact.title, 'Updated Project Title')
        self.assertEqual(self.artifact.description, 'Updated description')
        # Unchanged fields should remain the same
        self.assertEqual(self.artifact.artifact_type, 'project')

    def test_full_update_artifact(self):
        """Test full artifact update with PUT"""
        url = reverse('artifact_detail', kwargs={'pk': self.artifact.pk})
        data = {
            'title': 'Completely New Title',
            'description': 'Completely new description',
            'artifact_type': 'publication',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'technologies': ['Python', 'React'],
            'collaborators': ['jane@example.com']
        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.artifact.refresh_from_db()
        self.assertEqual(self.artifact.title, 'Completely New Title')
        self.assertEqual(self.artifact.artifact_type, 'publication')
        self.assertEqual(self.artifact.technologies, ['Python', 'React'])

    def test_cannot_update_other_user_artifact(self):
        """Test that users cannot update other users' artifacts"""
        url = reverse('artifact_detail', kwargs={'pk': self.other_artifact.pk})
        data = {'title': 'Hacked Title'}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.other_artifact.refresh_from_db()
        self.assertNotEqual(self.other_artifact.title, 'Hacked Title')

    def test_update_artifact_validation_errors(self):
        """Test validation errors during artifact update"""
        url = reverse('artifact_detail', kwargs={'pk': self.artifact.pk})
        data = {
            'title': '',  # Required field
            'start_date': '2023-12-31',
            'end_date': '2023-01-01'  # End before start
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_add_evidence_link(self):
        """Test adding evidence link to artifact"""
        url = reverse('add_evidence_link', kwargs={'artifact_id': self.artifact.pk})
        data = {
            'url': 'https://github.com/user/project',
            'link_type': 'github',
            'description': 'Project repository'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EvidenceLink.objects.count(), 1)
        evidence_link = EvidenceLink.objects.first()
        self.assertEqual(evidence_link.artifact, self.artifact)
        self.assertEqual(evidence_link.url, 'https://github.com/user/project')
        self.assertEqual(evidence_link.link_type, 'github')

    def test_add_evidence_link_invalid_url(self):
        """Test adding evidence link with invalid URL"""
        url = reverse('add_evidence_link', kwargs={'artifact_id': self.artifact.pk})
        data = {
            'url': 'invalid-url',
            'link_type': 'github',
            'description': 'Invalid URL'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('url', response.data)
        self.assertEqual(EvidenceLink.objects.count(), 0)

    def test_update_evidence_link(self):
        """Test updating existing evidence link"""
        evidence_link = EvidenceLink.objects.create(
            artifact=self.artifact,
            url='https://old-url.com',
            link_type='website',
            description='Old description'
        )

        url = reverse('evidence_link_detail', kwargs={'link_id': evidence_link.pk})
        data = {
            'url': 'https://new-url.com',
            'link_type': 'github',
            'description': 'New description'
        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        evidence_link.refresh_from_db()
        self.assertEqual(evidence_link.url, 'https://new-url.com')
        self.assertEqual(evidence_link.link_type, 'github')
        self.assertEqual(evidence_link.description, 'New description')

    def test_delete_evidence_link(self):
        """Test deleting evidence link"""
        evidence_link = EvidenceLink.objects.create(
            artifact=self.artifact,
            url='https://example.com',
            link_type='website',
            description='Test link'
        )

        url = reverse('evidence_link_detail', kwargs={'link_id': evidence_link.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(EvidenceLink.objects.count(), 0)

    def test_cannot_update_other_user_evidence_link(self):
        """Test that users cannot update other users' evidence links"""
        evidence_link = EvidenceLink.objects.create(
            artifact=self.other_artifact,
            url='https://example.com',
            link_type='website',
            description='Other user link'
        )

        url = reverse('evidence_link_detail', kwargs={'link_id': evidence_link.pk})
        data = {'url': 'https://hacked.com'}

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        evidence_link.refresh_from_db()
        self.assertNotEqual(evidence_link.url, 'https://hacked.com')

    def test_bulk_add_technologies(self):
        """Test bulk adding technologies to multiple artifacts"""
        artifact2 = Artifact.objects.create(
            user=self.user,
            title='Project 2',
            description='Second project',
            technologies=['Java']
        )

        url = reverse('bulk_update_artifacts')
        data = {
            'artifact_ids': [self.artifact.pk, artifact2.pk],
            'action': 'add_technologies',
            'values': {
                'technologies': ['Docker', 'Kubernetes']
            }
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['successful'], 2)
        self.assertEqual(response.data['failed'], 0)

        self.artifact.refresh_from_db()
        artifact2.refresh_from_db()

        # Check that technologies were added to both artifacts
        self.assertIn('Docker', self.artifact.technologies)
        self.assertIn('Kubernetes', self.artifact.technologies)
        self.assertIn('Python', self.artifact.technologies)  # Original tech preserved

        self.assertIn('Docker', artifact2.technologies)
        self.assertIn('Java', artifact2.technologies)  # Original tech preserved

    def test_bulk_remove_technologies(self):
        """Test bulk removing technologies from multiple artifacts"""
        artifact2 = Artifact.objects.create(
            user=self.user,
            title='Project 2',
            description='Second project',
            technologies=['Python', 'Java', 'React']
        )

        url = reverse('bulk_update_artifacts')
        data = {
            'artifact_ids': [self.artifact.pk, artifact2.pk],
            'action': 'remove_technologies',
            'values': {
                'technologies': ['Python']
            }
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['successful'], 2)

        self.artifact.refresh_from_db()
        artifact2.refresh_from_db()

        # Python should be removed, other technologies preserved
        self.assertNotIn('Python', self.artifact.technologies)
        self.assertIn('Django', self.artifact.technologies)

        self.assertNotIn('Python', artifact2.technologies)
        self.assertIn('Java', artifact2.technologies)
        self.assertIn('React', artifact2.technologies)

    def test_bulk_update_artifact_type(self):
        """Test bulk updating artifact types"""
        artifact2 = Artifact.objects.create(
            user=self.user,
            title='Project 2',
            description='Second project',
            artifact_type='project'
        )

        url = reverse('bulk_update_artifacts')
        data = {
            'artifact_ids': [self.artifact.pk, artifact2.pk],
            'action': 'update_type',
            'values': {
                'artifact_type': 'publication'
            }
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['successful'], 2)

        self.artifact.refresh_from_db()
        artifact2.refresh_from_db()

        self.assertEqual(self.artifact.artifact_type, 'publication')
        self.assertEqual(artifact2.artifact_type, 'publication')

    def test_bulk_update_with_invalid_artifact_ids(self):
        """Test bulk update with some invalid artifact IDs"""
        url = reverse('bulk_update_artifacts')
        data = {
            'artifact_ids': [self.artifact.pk, 9999, self.other_artifact.pk],  # Include other user's artifact
            'action': 'add_technologies',
            'values': {
                'technologies': ['Docker']
            }
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not found or not owned', response.data['error'])

    def test_bulk_update_validation_errors(self):
        """Test bulk update with validation errors"""
        url = reverse('bulk_update_artifacts')

        # Missing required fields
        data = {
            'artifact_ids': [self.artifact.pk],
            'action': 'add_technologies',
            'values': {}  # Missing technologies
        }

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid artifact type
        data = {
            'artifact_ids': [self.artifact.pk],
            'action': 'update_type',
            'values': {
                'artifact_type': 'invalid_type'
            }
        }

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ArtifactEditingSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword'
        )

        self.artifact = Artifact.objects.create(
            user=self.user,
            title='Test Project',
            description='Test description',
            artifact_type='project'
        )

    def test_artifact_update_serializer_validation(self):
        """Test ArtifactUpdateSerializer validation"""
        # Valid data
        data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        }
        serializer = ArtifactUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Invalid date range - but this validation doesn't require title/description
        data = {
            'title': 'Test',
            'description': 'Test desc',
            'start_date': '2023-12-31',
            'end_date': '2023-01-01'
        }
        serializer = ArtifactUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_evidence_link_create_serializer(self):
        """Test EvidenceLinkCreateSerializer"""
        # Valid data
        data = {
            'url': 'https://github.com/user/project',
            'link_type': 'github',
            'description': 'Project repository'
        }
        serializer = EvidenceLinkCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Invalid URL
        data = {
            'url': 'invalid-url',
            'link_type': 'github',
            'description': 'Invalid URL'
        }
        serializer = EvidenceLinkCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('url', serializer.errors)

    def test_bulk_artifact_update_serializer(self):
        """Test BulkArtifactUpdateSerializer validation"""
        # Valid technologies action
        data = {
            'artifact_ids': [1, 2, 3],
            'action': 'add_technologies',
            'values': {
                'technologies': ['Python', 'Django']
            }
        }
        serializer = BulkArtifactUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Invalid - missing technologies for technologies action
        data = {
            'artifact_ids': [1, 2, 3],
            'action': 'add_technologies',
            'values': {}
        }
        serializer = BulkArtifactUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        # Valid type update
        data = {
            'artifact_ids': [1, 2],
            'action': 'update_type',
            'values': {
                'artifact_type': 'publication'
            }
        }
        serializer = BulkArtifactUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Invalid artifact type
        data = {
            'artifact_ids': [1],
            'action': 'update_type',
            'values': {
                'artifact_type': 'invalid_type'
            }
        }
        serializer = BulkArtifactUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        # Too many artifact IDs
        data = {
            'artifact_ids': list(range(101)),  # 101 IDs, max is 100
            'action': 'add_technologies',
            'values': {'technologies': ['Python']}
        }
        serializer = BulkArtifactUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('artifact_ids', serializer.errors)


class ArtifactEditingModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword'
        )

    def test_artifact_update_preserves_metadata(self):
        """Test that artifact updates preserve extracted metadata"""
        artifact = Artifact.objects.create(
            user=self.user,
            title='Original Title',
            description='Original description',
            extracted_metadata={'key': 'value', 'processed': True}
        )

        # Update artifact
        artifact.title = 'Updated Title'
        artifact.save()

        artifact.refresh_from_db()
        self.assertEqual(artifact.title, 'Updated Title')
        self.assertEqual(artifact.extracted_metadata, {'key': 'value', 'processed': True})

    def test_evidence_link_cascade_delete(self):
        """Test that evidence links are deleted when artifact is deleted"""
        artifact = Artifact.objects.create(
            user=self.user,
            title='Test Project',
            description='Test description'
        )

        evidence_link = EvidenceLink.objects.create(
            artifact=artifact,
            url='https://example.com',
            link_type='website',
            description='Test link'
        )

        self.assertEqual(EvidenceLink.objects.count(), 1)

        artifact.delete()

        self.assertEqual(EvidenceLink.objects.count(), 0)

    def test_evidence_link_validation_metadata_updates(self):
        """Test evidence link validation metadata handling"""
        artifact = Artifact.objects.create(
            user=self.user,
            title='Test Project',
            description='Test description'
        )

        evidence_link = EvidenceLink.objects.create(
            artifact=artifact,
            url='https://example.com',
            link_type='website',
            description='Test link',
            validation_metadata={'status': 'pending'}
        )

        # Update validation metadata
        evidence_link.validation_metadata = {'status': 'validated', 'response_code': 200}
        evidence_link.is_accessible = True
        evidence_link.save()

        evidence_link.refresh_from_db()
        self.assertEqual(evidence_link.validation_metadata['status'], 'validated')
        self.assertTrue(evidence_link.is_accessible)