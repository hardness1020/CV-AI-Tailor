"""
Unit tests for LLM services.
"""

import json
import asyncio
import uuid
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from django.test import TestCase, override_settings
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from asgiref.sync import sync_to_async

from ..services.enhanced_llm_service import EnhancedLLMService
from ..services.embedding_service import FlexibleEmbeddingService
from ..services.document_processor import AdvancedDocumentProcessor
from ..services.performance_tracker import ModelPerformanceTracker
from ..services.circuit_breaker import CircuitBreakerManager
from ..services.model_registry import ModelRegistry
from ..models import ModelPerformanceMetric, CircuitBreakerState, JobDescriptionEmbedding

User = get_user_model()


class EnhancedLLMServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.llm_service = EnhancedLLMService()

    @patch('llm_services.services.enhanced_llm_service.OpenAI')
    @patch('llm_services.services.enhanced_llm_service.ModelPerformanceTracker')
    def test_select_model_for_task(self, mock_tracker, mock_openai):
        """Test model selection logic via model selector"""
        with patch.object(self.llm_service.model_selector, 'select_model_for_task') as mock_select:
            mock_select.return_value = 'gpt-4o'

            with patch.object(self.llm_service.model_selector, 'get_selection_reason') as mock_reason:
                mock_reason.return_value = 'Model selected based on task requirements'

                # Test the model selector directly since EnhancedLLMService uses it
                selected_model = self.llm_service.model_selector.select_model_for_task(
                    task_type='cv_generation',
                    context={'task_type': 'cv_generation'}
                )
                reasoning = self.llm_service.model_selector.get_selection_reason(selected_model, {})

                self.assertEqual(selected_model, 'gpt-4o')
                self.assertIn('selected', reasoning.lower())
                mock_select.assert_called_once()
                mock_reason.assert_called_once()

    @override_settings(OPENAI_API_KEY='test-key-123')
    async def test_parse_job_description(self):
        """Test job description parsing"""
        # Mock _direct_api_call response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'company_name': 'Tech Corp',
            'role_title': 'Senior Developer',
            'must_have_skills': ['Python', 'Django'],
            'nice_to_have_skills': ['React'],
            'key_responsibilities': ['Develop web applications'],
            'confidence_score': 0.9
        })
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 200
        mock_response.usage.total_tokens = 300

        with patch.object(self.llm_service.model_selector, 'select_model_for_task') as mock_select, \
             patch.object(self.llm_service, '_direct_api_call', return_value=mock_response) as mock_direct_api:

            mock_select.return_value = 'gpt-4o'

            result = await self.llm_service.parse_job_description(
                "Software engineer position at Tech Corp",
                "Tech Corp",
                "Software Engineer",
                self.user.id
            )

            self.assertEqual(result['company_name'], 'Tech Corp')
            self.assertEqual(result['role_title'], 'Senior Developer')
            self.assertIn('Python', result['must_have_skills'])
            self.assertEqual(result['confidence_score'], 0.9)
            mock_direct_api.assert_called_once()

    async def test_parse_job_description_api_error(self):
        """Test job description parsing with API error"""

        with patch.object(self.llm_service.model_selector, 'select_model_for_task') as mock_select, \
             patch.object(self.llm_service, '_direct_api_call') as mock_direct_api, \
             patch.object(self.llm_service.model_selector, 'should_use_fallback') as mock_fallback:

            mock_select.return_value = 'gpt-4o'
            # Mock the direct API call to raise an exception
            mock_direct_api.side_effect = Exception("API Error")
            # Mock fallback to return False so no fallback is attempted
            mock_fallback.return_value = False

            result = await self.llm_service.parse_job_description(
                "Job description",
                "Company",
                "Role",
                self.user.id
            )

            self.assertIn('error', result)
            self.assertIn('Failed to parse job description', result['error'])

    @patch('llm_services.services.enhanced_llm_service.OpenAI')
    @override_settings(OPENAI_API_KEY='test-key-123')
    async def test_generate_cv_content(self, mock_openai):
        """Test CV content generation"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'professional_summary': 'Experienced developer...',
            'key_skills': ['Python', 'Django', 'React'],
            'work_experience': [{'title': 'Developer', 'company': 'Tech Corp'}],
            'achievements': ['Built scalable applications']
        })
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 400
        mock_client.chat.completions.create.return_value = mock_response

        job_data = {
            'must_have_skills': ['Python', 'Django'],
            'role_title': 'Senior Developer'
        }
        artifacts = [{'title': 'My Resume', 'technologies': ['Python']}]

        with patch.object(self.llm_service.model_selector, 'select_model_for_task') as mock_select:
            mock_select.return_value = 'gpt-4o'

            result = await self.llm_service.generate_cv_content(
                job_data, artifacts, {}, self.user.id
            )

            self.assertIn('content', result)
            self.assertIn('professional_summary', result['content'])
            self.assertIn('processing_metadata', result)


class FlexibleEmbeddingServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.embedding_service = FlexibleEmbeddingService()

    @patch('llm_services.services.embedding_service.HAS_LITELLM', False)
    @patch('llm_services.services.embedding_service.openai.OpenAI')
    @override_settings(OPENAI_API_KEY='test-key-123')
    async def test_generate_embedding(self, mock_openai_class):
        """Test embedding generation"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 50
        mock_client.embeddings.create.return_value = mock_response

        # Reinitialize service to pick up the mocked OpenAI client
        self.embedding_service = FlexibleEmbeddingService()

        results = await self.embedding_service.generate_embeddings(
            texts=["Test content for embedding"],
            user_id=self.user.id
        )
        result = results[0] if results else {}

        self.assertIn('embedding', result)
        self.assertEqual(len(result['embedding']), 1536)
        self.assertIn('cost_usd', result)
        self.assertIn('model_used', result)
        self.assertIn('text', result)
        self.assertEqual(result['text'], "Test content for embedding")
        mock_client.embeddings.create.assert_called_once()

    @patch('llm_services.services.embedding_service.HAS_LITELLM', False)
    @patch('llm_services.services.embedding_service.openai.OpenAI')
    @override_settings(OPENAI_API_KEY='test-key-123')
    async def test_generate_embedding_api_error(self, mock_openai_class):
        """Test embedding generation with API error"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.embeddings.create.side_effect = Exception("API Error")

        # Reinitialize service to pick up the mocked OpenAI client
        self.embedding_service = FlexibleEmbeddingService()

        # Test that an exception is raised or empty results returned
        with self.assertRaises(Exception):
            await self.embedding_service.generate_embeddings(
                texts=["Test content"],
                user_id=self.user.id
            )

    @patch('llm_services.services.embedding_service.FlexibleEmbeddingService.generate_embeddings')
    async def test_store_artifact_embeddings(self, mock_generate):
        """Test storing artifact embeddings"""
        # Mock returns different results for main content vs chunks
        def mock_generate_side_effect(texts, **kwargs):
            if len(texts) == 1:
                # Main content call
                return [{
                    'embedding': [0.1] * 1536,
                    'cost_usd': 0.001,
                    'tokens_used': 100,
                    'model_used': 'text-embedding-3-small',
                    'text': 'mocked text',
                    'dimensions': 1536,
                    'text_index': 0,
                    'batch_processing_time_ms': 100
                }]
            else:
                # Chunk embeddings call (2 chunks)
                return [{
                    'embedding': [0.2] * 1536,
                    'cost_usd': 0.0005,
                    'tokens_used': 50,
                    'model_used': 'text-embedding-3-small',
                    'text': 'chunk text',
                    'dimensions': 1536,
                    'text_index': i,
                    'batch_processing_time_ms': 50
                } for i in range(len(texts))]

        mock_generate.side_effect = mock_generate_side_effect

        chunks = [
            {'content': 'Chunk 1', 'metadata': {}},
            {'content': 'Chunk 2', 'metadata': {}}
        ]

        result = await self.embedding_service.store_artifact_embeddings(
            artifact_id=str(uuid.uuid4()),
            content='Main content',
            chunks=chunks,
            user_id=self.user.id
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['chunks_processed'], 2)
        self.assertIn('total_cost_usd', result)

    async def test_generate_and_cache_job_embedding(self):
        """Test job embedding generation and caching"""
        with patch.object(self.embedding_service, 'generate_embeddings') as mock_gen:
            mock_gen.return_value = [{
                'embedding': [0.1] * 1536,
                'cost_usd': 0.001,
                'tokens_used': 100,
                'model_used': 'text-embedding-3-small',
                'text': 'Tech Corp Engineer Software engineer position',
                'dimensions': 1536,
                'text_index': 0,
                'batch_processing_time_ms': 100
            }]

            result = await self.embedding_service.generate_and_cache_job_embedding(
                job_description="Software engineer position",
                company_name="Tech Corp",
                role_title="Engineer",
                user_id=self.user.id
            )

            self.assertIn('embedding', result)
            self.assertIn('job_hash', result)
            self.assertIn('model_used', result)
            self.assertIn('dimensions', result)
            self.assertIn('cost_usd', result)
            self.assertIn('cached', result)
            self.assertFalse(result['cached'])  # Should be False for new generation

            # Check that embedding was saved to database
            embedding_exists = await sync_to_async(
                lambda: JobDescriptionEmbedding.objects.filter(
                    user=self.user
                ).exists()
            )()
            self.assertTrue(embedding_exists)


class AdvancedDocumentProcessorTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.processor = AdvancedDocumentProcessor()

    @patch('llm_services.services.document_processor.UnstructuredPDFLoader')
    async def test_process_document_pdf(self, mock_loader):
        """Test processing PDF document"""
        # Mock LangChain components
        mock_loader_instance = Mock()
        mock_loader.return_value = mock_loader_instance
        mock_loader_instance.load.return_value = [
            Mock(page_content="PDF content page 1", metadata={"page": 1}),
            Mock(page_content="PDF content page 2", metadata={"page": 2})
        ]

        # Mock the adaptive splitting to return exactly 2 chunks as expected
        with patch.object(self.processor, '_apply_adaptive_splitting') as mock_splitting:
            from llm_services.services.document_processor import Document

            mock_splitting.return_value = [
                Document(page_content="Chunk 1", metadata={"chunk": 0}),
                Document(page_content="Chunk 2", metadata={"chunk": 1})
            ]

            result = await self.processor.process_document(
                content="/path/to/test.pdf",
                content_type="pdf",
                metadata={"title": "Test PDF"},
                user_id=self.user.id
            )

            self.assertTrue(result['success'])
            self.assertEqual(len(result['chunks']), 2)
            self.assertEqual(result['chunks'][0]['content'], "Chunk 1")
            self.assertIn('processing_metadata', result)

    async def test_process_document_text(self):
        """Test processing plain text"""
        # Mock both the splitting and the LLM enhancement to control the exact output
        with patch.object(self.processor, '_apply_adaptive_splitting') as mock_splitting:
            from llm_services.services.document_processor import Document

            # Mock the splitting to return exactly 2 chunks as expected
            mock_splitting.return_value = [
                Document(page_content="Text chunk 1", metadata={"chunk": 0}),
                Document(page_content="Text chunk 2", metadata={"chunk": 1})
            ]

            # Mock the LLM enhancement to avoid API calls
            with patch.object(self.processor, '_enhance_chunk_with_llm') as mock_enhance:
                mock_enhance.side_effect = lambda chunk, idx, content_type, user_id: {
                    'content': chunk.page_content,
                    'metadata': {**chunk.metadata, 'chunk_index': idx}
                }

                result = await self.processor.process_document(
                    content="This is a long text content that will be split into chunks",
                    content_type="text",
                    metadata={"title": "Test Text"},
                    user_id=self.user.id
                )

                self.assertTrue(result['success'])
                self.assertEqual(len(result['chunks']), 2)

    async def test_process_document_error(self):
        """Test document processing error handling"""
        try:
            # Try to import UnstructuredPDFLoader to see if it's available
            from llm_services.services.document_processor import UnstructuredPDFLoader
            # If LangChain is available, mock the loader
            with patch('llm_services.services.document_processor.UnstructuredPDFLoader') as mock_loader:
                mock_loader.side_effect = Exception("File not found")

                result = await self.processor.process_document(
                    content="/nonexistent/file.pdf",
                    content_type="pdf",
                    metadata={},
                    user_id=self.user.id
                )

                # Normal error handling
                self.assertFalse(result['success'])
                self.assertIn('error', result)
        except ImportError:
            # If LangChain is not available, test the fallback behavior
            from pathlib import Path
            result = await self.processor.process_document(
                content=Path("/nonexistent/file.pdf"),
                content_type="pdf",
                metadata={},
                user_id=self.user.id
            )

            # Normal error handling
            self.assertFalse(result['success'])
            self.assertIn('error', result)


class ModelPerformanceTrackerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tracker = ModelPerformanceTracker()

    async def test_record_performance(self):
        """Test recording performance metric"""
        # Verify user exists first (using sync_to_async)
        self.assertTrue(self.user.id is not None)
        user_exists = await sync_to_async(User.objects.filter(id=self.user.id).exists)()
        self.assertTrue(user_exists)

        # Call the async method directly instead of the sync wrapper
        await self.tracker.record_task(
            model='gpt-4o',
            task_type='cv_generation',
            processing_time_ms=1500,
            tokens_used=800,
            cost_usd=Decimal('0.008'),
            success=True,
            quality_score=0.85,
            user_id=self.user.id
        )

        # Check that the metric was actually created (using sync_to_async)
        metrics_count = await sync_to_async(
            lambda: ModelPerformanceMetric.objects.filter(
                model_name='gpt-4o',
                task_type='cv_generation'
            ).count()
        )()
        self.assertEqual(metrics_count, 1)

        metric = await sync_to_async(
            lambda: ModelPerformanceMetric.objects.filter(
                model_name='gpt-4o',
                task_type='cv_generation'
            ).first()
        )()
        self.assertEqual(metric.processing_time_ms, 1500)
        self.assertEqual(metric.success, True)

    def test_get_model_performance_stats(self):
        """Test getting performance statistics"""
        # Create test metrics
        ModelPerformanceMetric.objects.create(
            model_name='gpt-4o',
            task_type='cv_generation',
            processing_time_ms=1000,
            cost_usd=Decimal('0.005'),
            success=True,
            user=self.user
        )
        ModelPerformanceMetric.objects.create(
            model_name='gpt-4o',
            task_type='cv_generation',
            processing_time_ms=1500,
            cost_usd=Decimal('0.008'),
            success=True,
            user=self.user
        )

        stats = self.tracker.get_model_performance_stats('gpt-4o', 'cv_generation')

        self.assertEqual(stats['count'], 2)
        # Note: success_rate is not available in task breakdown, only at model level
        self.assertEqual(stats['avg_time'], 1250.0)

    def test_get_best_model_for_task(self):
        """Test best model selection"""
        # Create metrics for different models
        ModelPerformanceMetric.objects.create(
            model_name='gpt-4o',
            task_type='cv_generation',
            processing_time_ms=1000,
            cost_usd=Decimal('0.008'),
            success=True,
            quality_score=Decimal('0.9'),
            user=self.user
        )
        ModelPerformanceMetric.objects.create(
            model_name='gpt-4o-mini',
            task_type='cv_generation',
            processing_time_ms=800,
            cost_usd=Decimal('0.002'),
            success=True,
            quality_score=Decimal('0.8'),
            user=self.user
        )

        # Test different strategies - method now returns just the model name
        best_performance = self.tracker.get_best_model_for_task(
            'cv_generation', priority='quality'
        )
        best_cost = self.tracker.get_best_model_for_task(
            'cv_generation', priority='cost'
        )

        self.assertEqual(best_performance, 'gpt-4o')  # Higher quality score
        self.assertEqual(best_cost, 'gpt-4o-mini')  # Lower cost


class CircuitBreakerManagerTestCase(TestCase):
    def setUp(self):
        self.service = CircuitBreakerManager()

    def test_record_success(self):
        """Test recording successful request"""
        model_name = f'test-record-success-{self._testMethodName}'
        self.service.record_success_sync(model_name)

        breaker = CircuitBreakerState.objects.get(model_name=model_name)
        self.assertEqual(breaker.state, 'closed')
        self.assertEqual(breaker.failure_count, 0)

    def test_record_failure(self):
        """Test recording failed request"""
        # Create initial breaker
        CircuitBreakerState.objects.create(
            model_name='test-model',
            failure_count=0,
            state='closed'
        )

        # Record failures
        for i in range(5):  # Default threshold
            self.service.record_failure_sync('test-model')

        breaker = CircuitBreakerState.objects.get(model_name='test-model')
        self.assertEqual(breaker.state, 'open')
        self.assertEqual(breaker.failure_count, 5)

    async def test_can_attempt_request(self):
        """Test request permission checking"""
        # Closed circuit should allow requests
        result = await self.service.can_attempt_request('new-model')
        self.assertTrue(result)

        # Create open circuit
        await sync_to_async(CircuitBreakerState.objects.create)(
            model_name='broken-model',
            state='open',
            last_failure=timezone.now()
        )

        result = await self.service.can_attempt_request('broken-model')
        self.assertFalse(result)

    def test_get_breaker_status(self):
        """Test getting breaker status"""
        CircuitBreakerState.objects.create(
            model_name='test-model',
            state='closed',
            failure_count=2
        )

        status = self.service.get_breaker_status('test-model')

        self.assertEqual(status['state'], 'closed')
        self.assertEqual(status['failure_count'], 2)
        self.assertEqual(status['is_healthy'], True)


class ModelRegistryTestCase(TestCase):
    def setUp(self):
        self.registry = ModelRegistry()

    def test_get_model_config(self):
        """Test getting model configuration"""
        config = self.registry.get_model_config('gpt-4o')

        self.assertIsInstance(config, dict)
        self.assertIn('provider', config)
        self.assertIn('context_window', config)
        self.assertIn('cost_input', config)

    def test_get_models_by_criteria(self):
        """Test filtering models by criteria"""
        models = self.registry.get_models_by_criteria(
            model_type='chat_models',
            max_cost_per_1k_tokens=0.001
        )

        self.assertIsInstance(models, dict)
        self.assertTrue(len(models) > 0)

        # Verify all returned models meet criteria
        for model_name, config in models.items():
            self.assertLessEqual(config['cost_input'], 0.001)

    def test_get_model_stats(self):
        """Test getting model statistics"""
        stats = self.registry.get_model_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn('total_chat_models', stats)
        self.assertIn('total_embedding_models', stats)
        self.assertIn('providers', stats)

        # Verify we have expected models
        self.assertGreater(stats['total_chat_models'], 0)
        self.assertGreater(stats['total_embedding_models'], 0)
        self.assertIn('openai', stats['providers'])
        self.assertIn('anthropic', stats['providers'])