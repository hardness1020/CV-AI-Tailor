"""
Unit tests for ft-002: CV Generation System
"""

import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    JobDescription, GeneratedDocument, CVTemplate,
    GenerationFeedback, SkillsTaxonomy
)
from .llm_service import LLMService
from .tasks import (
    generate_cv_task, calculate_skill_match_score,
    find_missing_skills, cleanup_expired_generations
)
from artifacts.models import Artifact

User = get_user_model()


class JobDescriptionModelTests(TestCase):
    """Test cases for JobDescription model"""

    def test_job_description_creation(self):
        """Test basic job description creation"""
        job_desc = JobDescription.objects.create(
            content_hash='abc123',
            raw_content='Software Engineer position at TechCorp',
            company_name='TechCorp',
            role_title='Software Engineer',
            parsing_confidence=0.9
        )

        self.assertEqual(job_desc.content_hash, 'abc123')
        self.assertEqual(job_desc.company_name, 'TechCorp')
        self.assertEqual(job_desc.parsing_confidence, 0.9)

    def test_get_or_create_from_content(self):
        """Test get_or_create_from_content method"""
        content = 'Looking for a Python developer'

        # First call should create
        job_desc1, created1 = JobDescription.get_or_create_from_content(
            content, 'TechCorp', 'Python Developer'
        )
        self.assertTrue(created1)
        self.assertEqual(job_desc1.company_name, 'TechCorp')

        # Second call should retrieve existing
        job_desc2, created2 = JobDescription.get_or_create_from_content(
            content, 'TechCorp', 'Python Developer'
        )
        self.assertFalse(created2)
        self.assertEqual(job_desc1.id, job_desc2.id)

    def test_job_description_string_representation(self):
        """Test __str__ method"""
        job_desc = JobDescription.objects.create(
            content_hash='abc123',
            raw_content='Test content',
            company_name='TechCorp',
            role_title='Engineer'
        )
        expected = 'Engineer at TechCorp'
        self.assertEqual(str(job_desc), expected)

        # Test fallback when no title/company
        job_desc2 = JobDescription.objects.create(
            content_hash='def456',
            raw_content='Test content'
        )
        self.assertIn('Job', str(job_desc2))


class GeneratedDocumentModelTests(TestCase):
    """Test cases for GeneratedDocument model"""

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

    def test_generated_document_creation(self):
        """Test basic generated document creation"""
        expires_at = timezone.now() + timedelta(days=90)

        doc = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            job_description=self.job_desc,
            expires_at=expires_at
        )

        self.assertEqual(doc.user, self.user)
        self.assertEqual(doc.document_type, 'cv')
        self.assertEqual(doc.status, 'processing')  # Default status
        self.assertIsInstance(doc.id, uuid.UUID)

    def test_generated_document_with_content(self):
        """Test generated document with CV content"""
        content = {
            'professional_summary': 'Experienced developer',
            'key_skills': ['Python', 'Django'],
            'experience': [
                {
                    'title': 'Software Engineer',
                    'organization': 'TechCorp',
                    'achievements': ['Built web apps']
                }
            ]
        }

        doc = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            content=content,
            status='completed'
        )

        self.assertEqual(doc.content['professional_summary'], 'Experienced developer')
        self.assertEqual(len(doc.content['key_skills']), 2)
        self.assertEqual(doc.status, 'completed')

    def test_generated_document_metadata(self):
        """Test document with generation metadata"""
        metadata = {
            'model_used': 'gpt-4',
            'generation_time_ms': 15000,
            'skill_match_score': 8,
            'missing_skills': ['React', 'TypeScript']
        }

        doc = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            metadata=metadata
        )

        self.assertEqual(doc.metadata['model_used'], 'gpt-4')
        self.assertEqual(doc.metadata['skill_match_score'], 8)
        self.assertEqual(len(doc.metadata['missing_skills']), 2)

    def test_document_ordering(self):
        """Test document ordering by created_at"""
        doc1 = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123'
        )
        doc2 = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='def456'
        )

        docs = GeneratedDocument.objects.all()
        self.assertEqual(docs[0], doc2)  # Most recent first


class CVTemplateModelTests(TestCase):
    """Test cases for CVTemplate model"""

    def test_cv_template_creation(self):
        """Test CV template creation"""
        template = CVTemplate.objects.create(
            name='Modern Professional',
            category='modern',
            description='A modern professional template',
            template_config={'font': 'Arial', 'color': '#000'},
            prompt_template='Generate CV with: {requirements}',
            is_premium=False,
            is_active=True
        )

        self.assertEqual(template.name, 'Modern Professional')
        self.assertEqual(template.category, 'modern')
        self.assertFalse(template.is_premium)
        self.assertTrue(template.is_active)

    def test_template_string_representation(self):
        """Test template __str__ method"""
        template = CVTemplate.objects.create(
            name='Classic',
            category='classic',
            description='Classic template'
        )
        expected = 'Classic (classic)'
        self.assertEqual(str(template), expected)


class GenerationFeedbackModelTests(TestCase):
    """Test cases for GenerationFeedback model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.generation = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123'
        )

    def test_feedback_creation(self):
        """Test feedback creation"""
        feedback = GenerationFeedback.objects.create(
            generation=self.generation,
            feedback_type='rating',
            feedback_data={'rating': 8, 'comment': 'Good quality'}
        )

        self.assertEqual(feedback.generation, self.generation)
        self.assertEqual(feedback.feedback_type, 'rating')
        self.assertEqual(feedback.feedback_data['rating'], 8)


class SkillsTaxonomyModelTests(TestCase):
    """Test cases for SkillsTaxonomy model"""

    def test_skills_taxonomy_creation(self):
        """Test skills taxonomy creation"""
        skill = SkillsTaxonomy.objects.create(
            skill_name='Python',
            category='programming',
            aliases=['Python3', 'py'],
            related_skills=['Django', 'Flask'],
            popularity_score=95
        )

        self.assertEqual(skill.skill_name, 'Python')
        self.assertEqual(skill.category, 'programming')
        self.assertEqual(len(skill.aliases), 2)
        self.assertEqual(skill.popularity_score, 95)


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


class LLMServiceTests(TestCase):
    """Test cases for LLM Service"""

    def setUp(self):
        self.llm_service = LLMService()

    @patch('generation.llm_service.openai.OpenAI')
    @override_settings(OPENAI_API_KEY='fake-key')
    def test_parse_job_description_openai(self, mock_openai):
        """Test job description parsing with OpenAI"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'role_title': 'Software Engineer',
            'must_have_skills': ['Python', 'Django'],
            'confidence_score': 0.9
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = LLMService()
        service.openai_client = mock_client

        result = service.parse_job_description(
            'Looking for Python developer',
            'TechCorp',
            'Software Engineer'
        )

        self.assertEqual(result['role_title'], 'Software Engineer')
        self.assertEqual(len(result['must_have_skills']), 2)
        self.assertEqual(result['confidence_score'], 0.9)

    def test_rank_artifacts_by_relevance(self):
        """Test artifact ranking by relevance"""
        artifacts = [
            {
                'id': 1,
                'title': 'Django Web App',
                'description': 'E-commerce platform built with Django',
                'technologies': ['Python', 'Django', 'PostgreSQL']
            },
            {
                'id': 2,
                'title': 'React Dashboard',
                'description': 'Analytics dashboard built with React',
                'technologies': ['JavaScript', 'React', 'Node.js']
            }
        ]

        job_requirements = ['Python', 'Django', 'Web Development']

        ranked = self.llm_service.rank_artifacts_by_relevance(artifacts, job_requirements)

        # Django project should rank higher
        self.assertEqual(ranked[0]['id'], 1)
        self.assertGreater(ranked[0]['relevance_score'], ranked[1]['relevance_score'])

    def test_rank_artifacts_empty_input(self):
        """Test artifact ranking with empty input"""
        result = self.llm_service.rank_artifacts_by_relevance([], [])
        self.assertEqual(result, [])

        artifacts = [{'id': 1, 'title': 'Test'}]
        result = self.llm_service.rank_artifacts_by_relevance(artifacts, [])
        self.assertEqual(len(result), 1)


class GenerationTaskTests(TestCase):
    """Test cases for generation Celery tasks"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.job_desc = JobDescription.objects.create(
            content_hash='abc123',
            raw_content='Python developer position',
            parsed_data={
                'must_have_skills': ['Python', 'Django'],
                'nice_to_have_skills': ['React']
            }
        )
        self.artifact = Artifact.objects.create(
            user=self.user,
            title='Django Project',
            technologies=['Python', 'Django']
        )

    def test_calculate_skill_match_score(self):
        """Test skill matching score calculation"""
        user_skills = ['Python', 'Django', 'JavaScript']
        job_requirements = ['Python', 'Django', 'React']

        score = calculate_skill_match_score(user_skills, job_requirements)

        # Should match 2 out of 3 requirements
        expected_score = int((2/3) * 10)
        self.assertEqual(score, expected_score)

    def test_calculate_skill_match_score_empty(self):
        """Test skill matching with empty inputs"""
        self.assertEqual(calculate_skill_match_score([], ['Python']), 0)
        self.assertEqual(calculate_skill_match_score(['Python'], []), 0)

    def test_find_missing_skills(self):
        """Test finding missing skills"""
        user_skills = ['Python', 'Django']
        required_skills = ['Python', 'Django', 'React', 'TypeScript']

        missing = find_missing_skills(user_skills, required_skills)

        self.assertEqual(len(missing), 2)
        self.assertIn('React', missing)
        self.assertIn('TypeScript', missing)

    def test_find_missing_skills_partial_match(self):
        """Test partial skill matching"""
        user_skills = ['JavaScript Programming', 'Python Development']
        required_skills = ['JavaScript', 'Python', 'React']

        missing = find_missing_skills(user_skills, required_skills)

        # JavaScript and Python should be matched, only React missing
        self.assertEqual(len(missing), 1)
        self.assertIn('React', missing)

    @patch('generation.tasks.LLMService')
    def test_generate_cv_task_no_llm(self, mock_llm_service):
        """Test CV generation task without LLM service"""
        generation = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            job_description=self.job_desc
        )

        # Mock LLM service to return error
        mock_service = Mock()
        mock_service.parse_job_description.return_value = {'error': 'No LLM service available'}
        mock_llm_service.return_value = mock_service

        generate_cv_task(str(generation.id))

        generation.refresh_from_db()
        self.assertEqual(generation.status, 'failed')
        self.assertIn('Failed to parse job description', generation.error_message)

    def test_cleanup_expired_generations(self):
        """Test cleanup of expired generations"""
        # Create expired generation
        expired_time = timezone.now() - timedelta(days=1)
        GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            expires_at=expired_time
        )

        # Create valid generation
        future_time = timezone.now() + timedelta(days=1)
        GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='def456',
            expires_at=future_time
        )

        # Run cleanup
        deleted_count = cleanup_expired_generations()

        self.assertEqual(deleted_count, 1)
        self.assertEqual(GeneratedDocument.objects.count(), 1)


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