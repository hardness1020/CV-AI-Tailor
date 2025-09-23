"""
Unit tests for ft-003: Document Export System
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, mock_open
from io import BytesIO
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.files.storage import default_storage
from django.http import HttpResponse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ExportJob, ExportTemplate, ExportAnalytics
from .document_generators import PDFGenerator, DOCXGenerator
from .tasks import (
    export_document_task, generate_pdf_document, generate_docx_document,
    cleanup_expired_exports, validate_evidence_links_for_export
)
from generation.models import GeneratedDocument, JobDescription

User = get_user_model()


class ExportTemplateModelTests(TestCase):
    """Test cases for ExportTemplate model"""

    def test_export_template_creation(self):
        """Test basic export template creation"""
        template = ExportTemplate.objects.create(
            name='Professional Modern',
            category='modern',
            description='A professional modern template',
            template_config={
                'font_family': 'Arial',
                'font_size': 12,
                'margins': {'top': 1, 'bottom': 1, 'left': 1, 'right': 1}
            },
            css_styles='body { font-family: Arial; }',
            is_premium=False,
            is_active=True
        )

        self.assertEqual(template.name, 'Professional Modern')
        self.assertEqual(template.category, 'modern')
        self.assertFalse(template.is_premium)
        self.assertTrue(template.is_active)
        self.assertEqual(template.template_config['font_family'], 'Arial')

    def test_template_string_representation(self):
        """Test template __str__ method"""
        template = ExportTemplate.objects.create(
            name='Classic',
            category='classic',
            description='Classic template'
        )
        expected = 'Classic (classic)'
        self.assertEqual(str(template), expected)


class ExportJobModelTests(TestCase):
    """Test cases for ExportJob model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.job_desc = JobDescription.objects.create(
            content_hash='abc123',
            raw_content='Test job description'
        )
        self.generated_doc = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            job_description=self.job_desc,
            status='completed',
            content={
                'professional_summary': 'Experienced developer',
                'key_skills': ['Python', 'Django']
            }
        )
        self.template = ExportTemplate.objects.create(
            name='Test Template',
            category='modern',
            description='Test template'
        )

    def test_export_job_creation(self):
        """Test basic export job creation"""
        job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            template=self.template,
            export_options={'include_evidence': True}
        )

        self.assertEqual(job.user, self.user)
        self.assertEqual(job.generated_document, self.generated_doc)
        self.assertEqual(job.format, 'pdf')
        self.assertEqual(job.template, self.template)
        self.assertEqual(job.status, 'processing')  # Default status
        self.assertIsInstance(job.id, uuid.UUID)

    def test_export_job_with_file_info(self):
        """Test export job with completed file information"""
        job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            status='completed',
            file_path='exports/cv_1_test.pdf',
            file_size=2048,
            download_count=3
        )

        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.file_path, 'exports/cv_1_test.pdf')
        self.assertEqual(job.file_size, 2048)
        self.assertEqual(job.download_count, 3)

    def test_download_url_property(self):
        """Test download_url property"""
        # Completed job should have download URL
        job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            status='completed',
            file_path='exports/test.pdf'
        )
        expected_url = f"/api/v1/export/{job.id}/download"
        self.assertEqual(job.download_url, expected_url)

        # Processing job should not have download URL
        job2 = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            status='processing'
        )
        self.assertIsNone(job2.download_url)

    def test_export_job_ordering(self):
        """Test export job ordering by created_at"""
        job1 = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf'
        )
        job2 = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='docx'
        )

        jobs = ExportJob.objects.all()
        self.assertEqual(jobs[0], job2)  # Most recent first


class ExportAnalyticsModelTests(TestCase):
    """Test cases for ExportAnalytics model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.generated_doc = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123'
        )
        self.export_job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf'
        )

    def test_analytics_creation(self):
        """Test analytics record creation"""
        analytics = ExportAnalytics.objects.create(
            export_job=self.export_job,
            event_type='downloaded',
            metadata={'user_agent': 'Mozilla/5.0', 'referrer': 'direct'},
            user_agent='Mozilla/5.0 Chrome',
            ip_address='192.168.1.1'
        )

        self.assertEqual(analytics.export_job, self.export_job)
        self.assertEqual(analytics.event_type, 'downloaded')
        self.assertEqual(analytics.ip_address, '192.168.1.1')


class ExportAPITests(APITestCase):
    """Test cases for Export API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Create test data
        self.job_desc = JobDescription.objects.create(
            content_hash='abc123',
            raw_content='Test job description'
        )
        self.generated_doc = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            job_description=self.job_desc,
            status='completed',
            content={
                'professional_summary': 'Experienced developer',
                'key_skills': ['Python', 'Django'],
                'experience': [
                    {
                        'title': 'Software Engineer',
                        'organization': 'TechCorp',
                        'achievements': ['Built web applications']
                    }
                ]
            }
        )
        self.template = ExportTemplate.objects.create(
            name='Test Template',
            category='modern',
            description='Test template',
            is_active=True
        )

    @patch('export.tasks.export_document_task.delay')
    def test_export_document_pdf(self, mock_task):
        """Test PDF export request"""
        url = reverse('export_document', kwargs={'generation_id': self.generated_doc.id})
        data = {
            'format': 'pdf',
            'template_id': self.template.id,
            'options': {
                'include_evidence': False,
                'page_margins': 'normal',
                'font_size': 12
            },
            'sections': {
                'include_professional_summary': True,
                'include_skills': True,
                'include_experience': True
            }
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('export_id', response.data)
        self.assertEqual(response.data['status'], 'processing')

        # Check that export job was created
        self.assertEqual(ExportJob.objects.count(), 1)
        export_job = ExportJob.objects.first()
        self.assertEqual(export_job.format, 'pdf')
        self.assertEqual(export_job.template, self.template)

        # Check that async task was called
        mock_task.assert_called_once()

    @patch('export.tasks.export_document_task.delay')
    def test_export_document_docx(self, mock_task):
        """Test DOCX export request"""
        url = reverse('export_document', kwargs={'generation_id': self.generated_doc.id})
        data = {
            'format': 'docx',
            'options': {
                'include_evidence': True,
                'evidence_format': 'hyperlinks'
            }
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        export_job = ExportJob.objects.first()
        self.assertEqual(export_job.format, 'docx')
        self.assertTrue(export_job.export_options['options']['include_evidence'])

    def test_export_document_not_found(self):
        """Test export request for non-existent generation"""
        fake_id = str(uuid.uuid4())
        url = reverse('export_document', kwargs={'generation_id': fake_id})
        data = {'format': 'pdf'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_export_document_invalid_template(self):
        """Test export request with invalid template"""
        url = reverse('export_document', kwargs={'generation_id': self.generated_doc.id})
        data = {
            'format': 'pdf',
            'template_id': 99999  # Non-existent template
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_export_status(self):
        """Test export status endpoint"""
        export_job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            status='completed',
            progress_percentage=100,
            file_path='exports/test.pdf',
            file_size=2048
        )

        url = reverse('export_status', kwargs={'export_id': export_job.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['progress_percentage'], 100)
        self.assertEqual(response.data['file_size'], 2048)

    def test_export_status_not_found(self):
        """Test export status for non-existent export"""
        fake_id = str(uuid.uuid4())
        url = reverse('export_status', kwargs={'export_id': fake_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('export.views.default_storage')
    def test_download_export_success(self, mock_storage):
        """Test successful file download"""
        # Mock file content
        file_content = b'%PDF-1.4 fake pdf content'
        mock_file = Mock()
        mock_file.read.return_value = file_content
        mock_storage.open.return_value = mock_file
        mock_storage.exists.return_value = True

        export_job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            status='completed',
            file_path='exports/test.pdf',
            file_size=len(file_content),
            expires_at=timezone.now() + timedelta(hours=1)
        )

        url = reverse('download_export', kwargs={'export_id': export_job.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])

        # Check download count was incremented
        export_job.refresh_from_db()
        self.assertEqual(export_job.download_count, 1)

        # Check analytics was created
        self.assertEqual(ExportAnalytics.objects.count(), 1)

    def test_download_export_not_found(self):
        """Test download for non-existent export"""
        fake_id = str(uuid.uuid4())
        url = reverse('download_export', kwargs={'export_id': fake_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    @patch('export.views.default_storage')
    def test_download_export_expired(self, mock_storage):
        """Test download of expired export"""
        mock_storage.exists.return_value = True

        export_job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            status='completed',
            file_path='exports/test.pdf',
            expires_at=timezone.now() - timedelta(hours=1)  # Expired
        )

        url = reverse('download_export', kwargs={'export_id': export_job.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_410_GONE)

    def test_user_exports_list(self):
        """Test listing user's exports"""
        # Create test exports
        ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf'
        )
        ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='docx'
        )

        url = reverse('user_exports_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    @patch('export.views.default_storage')
    def test_delete_export_job(self, mock_storage):
        """Test deleting export job"""
        mock_storage.exists.return_value = True

        export_job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            file_path='exports/test.pdf'
        )

        url = reverse('export_job_detail', kwargs={'pk': export_job.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ExportJob.objects.count(), 0)

        # Check that file deletion was attempted
        mock_storage.delete.assert_called_once_with('exports/test.pdf')


class ExportTemplateAPITests(APITestCase):
    """Test cases for Export Template API"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Create test templates
        ExportTemplate.objects.create(
            name='Modern',
            category='modern',
            description='Modern template',
            is_active=True
        )
        ExportTemplate.objects.create(
            name='Classic',
            category='classic',
            description='Classic template',
            is_active=True
        )
        ExportTemplate.objects.create(
            name='Inactive',
            category='modern',
            description='Inactive template',
            is_active=False
        )

    def test_list_active_templates(self):
        """Test listing only active templates"""
        url = reverse('export_templates_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Only active templates

        template_names = [t['name'] for t in response.data['results']]
        self.assertIn('Modern', template_names)
        self.assertIn('Classic', template_names)
        self.assertNotIn('Inactive', template_names)


class ExportAnalyticsAPITests(APITestCase):
    """Test cases for export analytics API"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.generated_doc = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123'
        )

        self.template = ExportTemplate.objects.create(
            name='Test Template',
            category='modern',
            description='Test template'
        )

        # Create test exports
        ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            template=self.template,
            status='completed',
            download_count=2,
            file_size=2048
        )
        ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='docx',
            status='completed',
            download_count=1,
            file_size=1024
        )
        ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            status='failed'
        )

    def test_export_analytics(self):
        """Test export analytics endpoint"""
        url = reverse('export_analytics')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        analytics = response.data
        self.assertEqual(analytics['total_exports'], 3)
        self.assertEqual(analytics['completed_exports'], 2)
        self.assertEqual(analytics['failed_exports'], 1)
        self.assertEqual(analytics['total_downloads'], 3)  # 2 + 1

        # Check format distribution
        self.assertEqual(analytics['format_distribution']['pdf'], 2)
        self.assertEqual(analytics['format_distribution']['docx'], 1)

        # Check template usage
        self.assertEqual(analytics['template_usage']['Test Template'], 1)


class DocumentGeneratorTests(TestCase):
    """Test cases for document generators"""

    def setUp(self):
        self.sample_content = {
            'personal_info': {
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '+1234567890'
            },
            'professional_summary': 'Experienced software engineer',
            'key_skills': ['Python', 'Django', 'React'],
            'experience': [
                {
                    'title': 'Software Engineer',
                    'organization': 'TechCorp',
                    'duration': '2020 - Present',
                    'achievements': ['Built web applications', 'Led team projects']
                }
            ]
        }
        self.sample_options = {
            'options': {
                'include_evidence': False,
                'font_size': 12
            }
        }

    def test_pdf_generator_creation(self):
        """Test PDF generator instantiation"""
        generator = PDFGenerator()
        self.assertIsNotNone(generator)

    @patch('export.document_generators.SimpleDocTemplate')
    def test_pdf_generation(self, mock_doc_template):
        """Test PDF document generation"""
        # Mock ReportLab components
        mock_doc = Mock()
        mock_doc.build = Mock()
        mock_doc_template.return_value = mock_doc

        generator = PDFGenerator()
        result = generator.generate_cv(self.sample_content, self.sample_options)

        # Should return bytes
        self.assertIsInstance(result, bytes)
        mock_doc.build.assert_called_once()

    def test_docx_generator_creation(self):
        """Test DOCX generator instantiation"""
        generator = DOCXGenerator()
        self.assertIsNotNone(generator)

    @patch('export.document_generators.Document')
    def test_docx_generation(self, mock_document):
        """Test DOCX document generation"""
        # Mock python-docx components
        mock_doc = Mock()
        mock_buffer = BytesIO()
        mock_doc.save = Mock(side_effect=lambda buf: buf.write(b'fake docx'))
        mock_document.return_value = mock_doc

        generator = DOCXGenerator()
        result = generator.generate_cv(self.sample_content, self.sample_options)

        # Should return bytes
        self.assertIsInstance(result, bytes)
        mock_doc.save.assert_called_once()


class ExportTaskTests(TestCase):
    """Test cases for export Celery tasks"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.generated_doc = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            status='completed',
            content={
                'professional_summary': 'Experienced developer',
                'key_skills': ['Python', 'Django']
            }
        )

    @patch('export.tasks.generate_pdf_document')
    @patch('export.tasks.default_storage')
    def test_export_document_task_pdf(self, mock_storage, mock_generate_pdf):
        """Test PDF export task"""
        # Mock PDF generation
        fake_pdf_content = b'%PDF-1.4 fake pdf content'
        mock_generate_pdf.return_value = fake_pdf_content

        # Mock storage
        mock_storage.save.return_value = 'exports/test.pdf'

        export_job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf'
        )

        export_document_task(str(export_job.id))

        export_job.refresh_from_db()
        self.assertEqual(export_job.status, 'completed')
        self.assertEqual(export_job.progress_percentage, 100)
        self.assertEqual(export_job.file_size, len(fake_pdf_content))
        self.assertIsNotNone(export_job.completed_at)

        # Check analytics was created
        self.assertEqual(ExportAnalytics.objects.count(), 1)

    @patch('export.tasks.generate_docx_document')
    @patch('export.tasks.default_storage')
    def test_export_document_task_docx(self, mock_storage, mock_generate_docx):
        """Test DOCX export task"""
        fake_docx_content = b'fake docx content'
        mock_generate_docx.return_value = fake_docx_content
        mock_storage.save.return_value = 'exports/test.docx'

        export_job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='docx'
        )

        export_document_task(str(export_job.id))

        export_job.refresh_from_db()
        self.assertEqual(export_job.status, 'completed')
        self.assertEqual(export_job.file_size, len(fake_docx_content))

    def test_export_task_no_content(self):
        """Test export task with no content"""
        # Create generation without content
        empty_doc = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='def456',
            status='completed'
            # No content field
        )

        export_job = ExportJob.objects.create(
            user=self.user,
            generated_document=empty_doc,
            format='pdf'
        )

        export_document_task(str(export_job.id))

        export_job.refresh_from_db()
        self.assertEqual(export_job.status, 'failed')
        self.assertIn('No content available', export_job.error_message)

    def test_cleanup_expired_exports(self):
        """Test cleanup of expired export files"""
        # Create expired export
        expired_time = timezone.now() - timedelta(hours=1)
        expired_job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            status='completed',
            file_path='exports/expired.pdf',
            expires_at=expired_time
        )

        # Create valid export
        future_time = timezone.now() + timedelta(hours=1)
        valid_job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf',
            status='completed',
            file_path='exports/valid.pdf',
            expires_at=future_time
        )

        with patch('export.tasks.default_storage') as mock_storage:
            mock_storage.exists.return_value = True
            deleted_count = cleanup_expired_exports()

        self.assertEqual(deleted_count, 1)
        self.assertEqual(ExportJob.objects.count(), 1)
        self.assertEqual(ExportJob.objects.first().id, valid_job.id)

    @patch('export.tasks.requests.head')
    def test_validate_evidence_links_for_export(self, mock_requests):
        """Test evidence link validation for export"""
        # Create content with evidence links
        content_with_evidence = {
            'experience': [
                {
                    'title': 'Engineer',
                    'evidence_references': ['https://github.com/user/repo']
                }
            ],
            'projects': [
                {
                    'name': 'Web App',
                    'evidence_url': 'https://demo.app.com'
                }
            ]
        }

        self.generated_doc.content = content_with_evidence
        self.generated_doc.save()

        export_job = ExportJob.objects.create(
            user=self.user,
            generated_document=self.generated_doc,
            format='pdf'
        )

        # Mock successful validation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.return_value = mock_response

        validated_count = validate_evidence_links_for_export(str(export_job.id))

        self.assertEqual(validated_count, 2)  # 2 links validated

        export_job.refresh_from_db()
        validated_links = export_job.export_options.get('validated_evidence_links', [])
        self.assertEqual(len(validated_links), 2)


class ExportAuthorizationTests(APITestCase):
    """Test authorization and user isolation for export endpoints"""

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

        self.doc1 = GeneratedDocument.objects.create(
            user=self.user1,
            document_type='cv',
            job_description_hash='abc123',
            status='completed'
        )
        self.doc2 = GeneratedDocument.objects.create(
            user=self.user2,
            document_type='cv',
            job_description_hash='def456',
            status='completed'
        )

    def test_unauthorized_access(self):
        """Test that unauthenticated users can't access export endpoints"""
        url = reverse('export_document', kwargs={'generation_id': self.doc1.id})
        response = self.client.post(url, {'format': 'pdf'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_isolation(self):
        """Test that users can only export their own documents"""
        # Authenticate as user1
        token = RefreshToken.for_user(self.user1).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # User1 should not be able to export user2's document
        url = reverse('export_document', kwargs={'generation_id': self.doc2.id})
        response = self.client.post(url, {'format': 'pdf'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # User1 should be able to export their own document
        url = reverse('export_document', kwargs={'generation_id': self.doc1.id})
        with patch('export.tasks.export_document_task.delay'):
            response = self.client.post(url, {'format': 'pdf'})
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_export_job_isolation(self):
        """Test that users can only access their own export jobs"""
        export1 = ExportJob.objects.create(
            user=self.user1,
            generated_document=self.doc1,
            format='pdf'
        )
        export2 = ExportJob.objects.create(
            user=self.user2,
            generated_document=self.doc2,
            format='pdf'
        )

        # Authenticate as user1
        token = RefreshToken.for_user(self.user1).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # User1 should only see their exports
        url = reverse('user_exports_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(export1.id))

        # User1 should not access user2's export
        url = reverse('export_status', kwargs={'export_id': export2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)