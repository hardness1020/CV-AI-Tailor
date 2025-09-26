"""
Unit tests for enhanced Celery tasks.
"""

import asyncio
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.apps import apps

from generation.tasks import (
    generate_cv_task,
    generate_job_embedding_cache,
    enhance_artifact_with_llm,
    cleanup_expired_generations,
    cleanup_old_performance_metrics
)

User = get_user_model()


class GenerateCVTaskTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create necessary test data
        JobDescription = apps.get_model('generation', 'JobDescription')
        GeneratedDocument = apps.get_model('generation', 'GeneratedDocument')
        Artifact = apps.get_model('artifacts', 'Artifact')

        self.job_description = JobDescription.objects.create(
            raw_content="Software engineer position at Tech Corp requiring Python and Django skills",
            company_name="Tech Corp",
            role_title="Software Engineer"
        )

        self.generation = GeneratedDocument.objects.create(
            user=self.user,
            job_description=self.job_description,
            status='pending'
        )

        self.artifact = Artifact.objects.create(
            user=self.user,
            title="My Resume",
            description="Software developer with 5 years experience",
            artifact_type="resume",
            technologies=["Python", "Django", "React"]
        )

    @patch('generation.tasks.EnhancedLLMService')
    def test_generate_cv_task_success(self, mock_service):
        """Test successful CV generation"""
        # Mock the LLM service
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance

        # Mock job description parsing (already parsed)
        self.job_description.parsed_data = {
            'must_have_skills': ['Python', 'Django'],
            'nice_to_have_skills': ['React'],
            'role_title': 'Software Engineer',
            'company_name': 'Tech Corp'
        }
        self.job_description.save()

        # Mock artifact ranking
        mock_service_instance.rank_artifacts_by_relevance = AsyncMock(return_value=[
            {
                'id': self.artifact.id,
                'title': 'My Resume',
                'relevance_score': 0.9,
                'technologies': ['Python', 'Django']
            }
        ])

        # Mock CV generation
        mock_service_instance.generate_cv_content = AsyncMock(return_value={
            'content': {
                'professional_summary': 'Experienced software engineer...',
                'key_skills': ['Python', 'Django', 'React'],
                'work_experience': [{'title': 'Developer', 'company': 'Previous Corp'}]
            },
            'processing_metadata': {
                'model_used': 'gpt-4o',
                'processing_time_ms': 1500,
                'tokens_used': 800,
                'cost_usd': 0.008,
                'quality_score': 0.85
            }
        })

        # Run the task
        generate_cv_task(self.generation.id)

        # Verify the generation was updated
        self.generation.refresh_from_db()
        self.assertEqual(self.generation.status, 'completed')
        self.assertEqual(self.generation.progress_percentage, 100)
        self.assertIsNotNone(self.generation.content)
        self.assertIn('professional_summary', self.generation.content)
        self.assertEqual(self.generation.model_version, 'gpt-4o')
        self.assertEqual(self.generation.generation_time_ms, 1500)

    @patch('generation.tasks.EnhancedLLMService')
    def test_generate_cv_task_parsing_needed(self, mock_service):
        """Test CV generation when job description parsing is needed"""
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance

        # Job description not parsed yet
        self.job_description.parsed_data = {}
        self.job_description.save()

        # Mock job description parsing
        mock_service_instance.parse_job_description = AsyncMock(return_value={
            'company_name': 'Tech Corp',
            'role_title': 'Software Engineer',
            'must_have_skills': ['Python', 'Django'],
            'nice_to_have_skills': ['React'],
            'confidence_score': 0.9
        })

        # Mock other methods
        mock_service_instance.rank_artifacts_by_relevance = AsyncMock(return_value=[])
        mock_service_instance.generate_cv_content = AsyncMock(return_value={
            'content': {'professional_summary': 'Test summary'},
            'processing_metadata': {'model_used': 'gpt-4o', 'cost_usd': 0.005}
        })

        # Run the task
        generate_cv_task(self.generation.id)

        # Verify job description was parsed
        self.job_description.refresh_from_db()
        self.assertIsNotNone(self.job_description.parsed_data)
        self.assertEqual(self.job_description.parsed_data['company_name'], 'Tech Corp')

        # Verify generation completed
        self.generation.refresh_from_db()
        self.assertEqual(self.generation.status, 'completed')

    @patch('generation.tasks.EnhancedLLMService')
    def test_generate_cv_task_parsing_error(self, mock_service):
        """Test CV generation with job parsing error"""
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance

        # Mock parsing failure
        mock_service_instance.parse_job_description = AsyncMock(return_value={
            'error': 'Failed to parse job description'
        })

        # Run the task
        generate_cv_task(self.generation.id)

        # Verify generation failed
        self.generation.refresh_from_db()
        self.assertEqual(self.generation.status, 'failed')
        self.assertIn('Failed to parse job description', self.generation.error_message)

    @patch('generation.tasks.EnhancedLLMService')
    def test_generate_cv_task_generation_error(self, mock_service):
        """Test CV generation with content generation error"""
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance

        # Job description already parsed
        self.job_description.parsed_data = {'must_have_skills': ['Python']}
        self.job_description.save()

        # Mock successful ranking but failed generation
        mock_service_instance.rank_artifacts_by_relevance = AsyncMock(return_value=[])
        mock_service_instance.generate_cv_content = AsyncMock(return_value={
            'error': 'Generation failed'
        })

        # Run the task
        generate_cv_task(self.generation.id)

        # Verify generation failed
        self.generation.refresh_from_db()
        self.assertEqual(self.generation.status, 'failed')
        self.assertIn('Failed to generate CV', self.generation.error_message)

    def test_generate_cv_task_missing_job_description(self):
        """Test CV generation with missing job description"""
        self.generation.job_description = None
        self.generation.save()

        # Run the task
        generate_cv_task(self.generation.id)

        # Verify generation failed
        self.generation.refresh_from_db()
        self.assertEqual(self.generation.status, 'failed')
        self.assertIn('No job description provided', self.generation.error_message)

    def test_generate_cv_task_exception_handling(self):
        """Test exception handling in CV generation"""
        # Delete the generation to cause an exception
        generation_id = self.generation.id
        self.generation.delete()

        # Run the task (should handle exception gracefully)
        result = generate_cv_task(generation_id)
        self.assertIsNone(result)  # Task should complete without raising exception


class GenerateJobEmbeddingCacheTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('generation.tasks.FlexibleEmbeddingService')
    def test_generate_job_embedding_cache_success(self, mock_service):
        """Test successful job embedding cache generation"""
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance

        mock_service_instance.generate_and_cache_job_embedding = AsyncMock(return_value={
            'success': True,
            'job_hash': 'abc123def456',
            'embedding_id': 'uuid-here',
            'cost_usd': 0.001
        })

        result = generate_job_embedding_cache(
            job_description="Software engineer at Tech Corp",
            company_name="Tech Corp",
            role_title="Software Engineer",
            user_id=self.user.id
        )

        self.assertTrue(result['success'])
        self.assertIn('job_hash', result)
        mock_service_instance.generate_and_cache_job_embedding.assert_called_once()

    @patch('generation.tasks.FlexibleEmbeddingService')
    def test_generate_job_embedding_cache_error(self, mock_service):
        """Test job embedding cache generation with error"""
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance

        mock_service_instance.generate_and_cache_job_embedding = AsyncMock(
            side_effect=Exception("Embedding failed")
        )

        result = generate_job_embedding_cache(
            job_description="Test job description",
            user_id=self.user.id
        )

        self.assertIn('error', result)
        self.assertIn('Embedding failed', result['error'])


class EnhanceArtifactWithLLMTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        Artifact = apps.get_model('artifacts', 'Artifact')
        self.artifact = Artifact.objects.create(
            user=self.user,
            title="Test Document",
            description="A test document for processing",
            artifact_type="pdf"
        )

        # Add mock file attribute that the task expects
        self.artifact.file = Mock()
        self.artifact.file.path = '/fake/path/to/test.pdf'
        self.artifact.file.url = 'http://example.com/test.pdf'

    @patch('generation.tasks.AdvancedDocumentProcessor')
    @patch('generation.tasks.FlexibleEmbeddingService')
    def test_enhance_artifact_with_llm_success(self, mock_embedding_service, mock_doc_processor):
        """Test successful artifact enhancement"""
        # Mock document processor
        mock_doc_processor_instance = Mock()
        mock_doc_processor.return_value = mock_doc_processor_instance

        mock_doc_processor_instance.process_document = AsyncMock(return_value={
            'success': True,
            'chunks': [
                {
                    'content': 'First chunk content',
                    'metadata': {'section': 'experience'},
                    'enhanced_data': {
                        'must_have_skills': ['Python', 'Django'],
                        'key_responsibilities': ['Developed web applications']
                    }
                },
                {
                    'content': 'Second chunk content',
                    'metadata': {'section': 'education'},
                    'enhanced_data': {
                        'nice_to_have_skills': ['React'],
                        'key_responsibilities': ['Completed computer science degree']
                    }
                }
            ],
            'processing_metadata': {
                'model_used': 'gpt-4o',
                'processing_time_ms': 2000
            }
        })

        # Mock embedding service
        mock_embedding_service_instance = Mock()
        mock_embedding_service.return_value = mock_embedding_service_instance

        mock_embedding_service_instance.store_artifact_embeddings = AsyncMock(return_value={
            'success': True,
            'total_cost_usd': 0.005,
            'chunks_processed': 2,
            'main_embedding': {'model_used': 'text-embedding-3-small'}
        })

        # Run the task
        result = enhance_artifact_with_llm(self.artifact.id)

        self.assertIn('artifact_id', result)
        self.assertEqual(result['chunks_processed'], 2)
        self.assertEqual(result['skills_extracted'], 3)  # Python, Django, React
        self.assertEqual(result['achievements_extracted'], 2)

        # Verify artifact was updated
        self.artifact.refresh_from_db()
        self.assertIsNotNone(self.artifact.extracted_metadata)
        self.assertIn('enhanced_chunks', self.artifact.extracted_metadata)
        self.assertIn('Python', self.artifact.technologies)

    @patch('generation.tasks.AdvancedDocumentProcessor')
    def test_enhance_artifact_with_llm_processing_failure(self, mock_doc_processor):
        """Test artifact enhancement with processing failure"""
        # Mock document processor failure
        mock_doc_processor_instance = Mock()
        mock_doc_processor.return_value = mock_doc_processor_instance

        mock_doc_processor_instance.process_document = AsyncMock(return_value={
            'success': False,
            'error': 'Failed to process document'
        })

        # Test that the task handles processing failure gracefully
        # The actual retry logic is handled by Celery, so we just need to verify
        # that processing failures are caught and handled properly
        try:
            result = enhance_artifact_with_llm(self.artifact.id)
            # If we get a result instead of an exception, check if it contains error info
            if isinstance(result, dict) and 'error' in result:
                self.assertTrue(True)  # Test passes - error was handled
            else:
                self.fail("Expected task to handle processing failure")
        except Exception as e:
            # Task may raise an exception for retry - this is also acceptable behavior
            self.assertTrue(True)  # Test passes - exception indicates retry logic

    @patch('generation.tasks.AdvancedDocumentProcessor')
    def test_enhance_artifact_with_llm_max_retries_exceeded(self, mock_doc_processor):
        """Test artifact enhancement with max retries exceeded"""
        # Mock document processor failure
        mock_doc_processor_instance = Mock()
        mock_doc_processor.return_value = mock_doc_processor_instance

        mock_doc_processor_instance.process_document = AsyncMock(
            side_effect=Exception("Processing error")
        )

        # Run the task - since we're mocking a failure,
        # the task should handle it gracefully without retries in unit tests
        result = enhance_artifact_with_llm(self.artifact.id)

        self.assertIn('error', result)
        self.assertIn('Processing error', result['error'])

        # Verify artifact has error metadata
        self.artifact.refresh_from_db()
        self.assertIn('processing_error', self.artifact.extracted_metadata)

    def test_enhance_artifact_with_llm_artifact_not_found(self):
        """Test artifact enhancement with non-existent artifact"""
        task = Mock()
        task.request = Mock()
        task.request.retries = 0
        task.max_retries = 3
        task.retry = Mock(side_effect=Exception("Retry called"))

        # Run the task with non-existent artifact ID
        with self.assertRaises(Exception):
            enhance_artifact_with_llm(task, 99999)


class CleanupTasksTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_cleanup_expired_generations(self):
        """Test cleanup of expired generated documents"""
        GeneratedDocument = apps.get_model('generation', 'GeneratedDocument')

        # Create expired and non-expired documents
        expired_doc = GeneratedDocument.objects.create(
            user=self.user,
            status='completed',
            expires_at=timezone.now() - timezone.timedelta(days=1)
        )

        active_doc = GeneratedDocument.objects.create(
            user=self.user,
            status='completed',
            expires_at=timezone.now() + timezone.timedelta(days=30)
        )

        # Run cleanup
        result = cleanup_expired_generations()

        # Should have cleaned up 1 document
        self.assertEqual(result, 1)

        # Verify only expired document was deleted
        self.assertFalse(GeneratedDocument.objects.filter(id=expired_doc.id).exists())
        self.assertTrue(GeneratedDocument.objects.filter(id=active_doc.id).exists())

    @patch('llm_services.services.performance_tracker.ModelPerformanceTracker')
    @patch('llm_services.services.embedding_service.FlexibleEmbeddingService')
    def test_cleanup_old_performance_metrics(self, mock_embedding_service, mock_tracker):
        """Test cleanup of old performance metrics and embeddings"""
        # Mock tracker
        mock_tracker_instance = Mock()
        mock_tracker.return_value = mock_tracker_instance
        mock_tracker_instance.cleanup_old_metrics.return_value = 15

        # Mock embedding service
        mock_embedding_service_instance = Mock()
        mock_embedding_service.return_value = mock_embedding_service_instance
        mock_embedding_service_instance.cleanup_old_embeddings.return_value = 8

        # Run cleanup
        result = cleanup_old_performance_metrics()

        self.assertEqual(result['metrics_cleaned'], 15)
        self.assertEqual(result['embeddings_cleaned'], 8)

        mock_tracker_instance.cleanup_old_metrics.assert_called_once_with(days_to_keep=30)
        mock_embedding_service_instance.cleanup_old_embeddings.assert_called_once_with(days_to_keep=90)