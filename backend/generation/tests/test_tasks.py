"""
Unit tests for generation app Celery tasks
"""

from unittest.mock import patch, Mock, AsyncMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from generation.models import (
    JobDescription, GeneratedDocument, CVTemplate
)
from generation.tasks import (
    generate_cv_task, calculate_skill_match_score,
    find_missing_skills, cleanup_expired_generations
)
from artifacts.models import Artifact

User = get_user_model()


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

    @patch('generation.tasks.EnhancedLLMService')
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
        # Make async methods return appropriate coroutines
        mock_service.rank_artifacts_by_relevance = AsyncMock(return_value=[])
        mock_service.generate_cv_content = AsyncMock(return_value={'error': 'Service unavailable'})
        mock_llm_service.return_value = mock_service

        generate_cv_task(str(generation.id))

        generation.refresh_from_db()
        self.assertEqual(generation.status, 'failed')
        self.assertIn('Failed to generate CV', generation.error_message)

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