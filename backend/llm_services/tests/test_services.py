"""
Unit tests for LLM services.
"""

import json
import asyncio
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..services.enhanced_llm_service import EnhancedLLMService
from ..services.embedding_service import FlexibleEmbeddingService
from ..services.document_processor import AdvancedDocumentProcessor
from ..services.performance_tracker import ModelPerformanceTracker
from ..services.circuit_breaker_service import CircuitBreakerService
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
        """Test model selection logic"""
        mock_tracker_instance = Mock()
        mock_tracker.return_value = mock_tracker_instance
        mock_tracker_instance.get_best_model_for_task.return_value = 'gpt-4o'

        model, reasoning = self.llm_service._select_model_for_task(
            task_type='cv_generation',
            complexity_score=0.7,
            user_id=self.user.id
        )

        self.assertEqual(model, 'gpt-4o')
        self.assertIn('selected', reasoning.lower())
        mock_tracker_instance.get_best_model_for_task.assert_called_once()

    @patch('llm_services.services.enhanced_llm_service.OpenAI')
    async def test_parse_job_description(self, mock_openai):
        """Test job description parsing"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai.return_value = mock_client
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
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(self.llm_service, '_select_model_for_task') as mock_select:
            mock_select.return_value = ('gpt-4o', 'test reasoning')

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
            mock_client.chat.completions.create.assert_called_once()

    @patch('llm_services.services.enhanced_llm_service.OpenAI')
    async def test_parse_job_description_api_error(self, mock_openai):
        """Test job description parsing with API error"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with patch.object(self.llm_service, '_select_model_for_task') as mock_select:
            mock_select.return_value = ('gpt-4o', 'test reasoning')

            result = await self.llm_service.parse_job_description(
                "Job description",
                "Company",
                "Role",
                self.user.id
            )

            self.assertIn('error', result)
            self.assertIn('API Error', result['error'])

    @patch('llm_services.services.enhanced_llm_service.OpenAI')
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

        with patch.object(self.llm_service, '_select_model_for_task') as mock_select:
            mock_select.return_value = ('gpt-4o', 'test reasoning')

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

    @patch('llm_services.services.embedding_service.OpenAI')
    async def test_generate_embedding(self, mock_openai):
        """Test embedding generation"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        mock_response.usage.prompt_tokens = 50
        mock_client.embeddings.create.return_value = mock_response

        result = await self.embedding_service.generate_embedding(
            "Test content for embedding",
            self.user.id
        )

        self.assertTrue(result['success'])
        self.assertEqual(len(result['embedding']), 1536)
        self.assertIn('cost_usd', result)
        mock_client.embeddings.create.assert_called_once()

    @patch('llm_services.services.embedding_service.OpenAI')
    async def test_generate_embedding_api_error(self, mock_openai):
        """Test embedding generation with API error"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.side_effect = Exception("API Error")

        result = await self.embedding_service.generate_embedding(
            "Test content",
            self.user.id
        )

        self.assertFalse(result['success'])
        self.assertIn('error', result)

    @patch('llm_services.services.embedding_service.FlexibleEmbeddingService.generate_embedding')
    async def test_store_artifact_embeddings(self, mock_generate):
        """Test storing artifact embeddings"""
        mock_generate.return_value = {
            'success': True,
            'embedding': [0.1] * 1536,
            'cost_usd': 0.001,
            'tokens_used': 100,
            'model_used': 'text-embedding-3-small'
        }

        chunks = [
            {'content': 'Chunk 1', 'metadata': {}},
            {'content': 'Chunk 2', 'metadata': {}}
        ]

        result = await self.embedding_service.store_artifact_embeddings(
            artifact_id='123',
            content='Main content',
            chunks=chunks,
            user_id=self.user.id
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['chunks_processed'], 2)
        self.assertIn('total_cost_usd', result)

    async def test_generate_and_cache_job_embedding(self):
        """Test job embedding generation and caching"""
        with patch.object(self.embedding_service, 'generate_embedding') as mock_gen:
            mock_gen.return_value = {
                'success': True,
                'embedding': [0.1] * 1536,
                'cost_usd': 0.001,
                'tokens_used': 100,
                'model_used': 'text-embedding-3-small'
            }

            result = await self.embedding_service.generate_and_cache_job_embedding(
                job_description="Software engineer position",
                company_name="Tech Corp",
                role_title="Engineer",
                user_id=self.user.id
            )

            self.assertTrue(result['success'])
            self.assertIn('job_hash', result)

            # Check that embedding was saved to database
            embedding_exists = JobDescriptionEmbedding.objects.filter(
                user=self.user
            ).exists()
            self.assertTrue(embedding_exists)


class AdvancedDocumentProcessorTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.processor = AdvancedDocumentProcessor()

    @patch('llm_services.services.document_processor.PyPDFLoader')
    @patch('llm_services.services.document_processor.RecursiveCharacterTextSplitter')
    async def test_process_document_pdf(self, mock_splitter, mock_loader):
        """Test processing PDF document"""
        # Mock LangChain components
        mock_loader_instance = Mock()
        mock_loader.return_value = mock_loader_instance
        mock_loader_instance.load.return_value = [
            Mock(page_content="PDF content page 1", metadata={"page": 1}),
            Mock(page_content="PDF content page 2", metadata={"page": 2})
        ]

        mock_splitter_instance = Mock()
        mock_splitter.return_value = mock_splitter_instance
        mock_splitter_instance.split_documents.return_value = [
            Mock(page_content="Chunk 1", metadata={"chunk": 0}),
            Mock(page_content="Chunk 2", metadata={"chunk": 1})
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
        with patch('llm_services.services.document_processor.RecursiveCharacterTextSplitter') as mock_splitter:
            mock_splitter_instance = Mock()
            mock_splitter.return_value = mock_splitter_instance
            mock_splitter_instance.split_text.return_value = ["Text chunk 1", "Text chunk 2"]

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
        with patch('llm_services.services.document_processor.PyPDFLoader') as mock_loader:
            mock_loader.side_effect = Exception("File not found")

            result = await self.processor.process_document(
                content="/nonexistent/file.pdf",
                content_type="pdf",
                metadata={},
                user_id=self.user.id
            )

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

    def test_record_performance(self):
        """Test recording performance metric"""
        self.tracker.record_performance(
            model_name='gpt-4o',
            task_type='cv_generation',
            processing_time_ms=1500,
            tokens_used=800,
            cost_usd=Decimal('0.008'),
            success=True,
            quality_score=0.85,
            user_id=self.user.id
        )

        metric = ModelPerformanceMetric.objects.get(
            model_name='gpt-4o',
            task_type='cv_generation'
        )
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

        self.assertEqual(stats['total_requests'], 2)
        self.assertEqual(stats['success_rate'], 100.0)
        self.assertEqual(stats['avg_processing_time_ms'], 1250.0)

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

        # Test different strategies
        best_performance = self.tracker.get_best_model_for_task(
            'cv_generation', strategy='performance_first'
        )
        best_cost = self.tracker.get_best_model_for_task(
            'cv_generation', strategy='cost_optimized'
        )

        self.assertEqual(best_performance, 'gpt-4o')  # Higher quality score
        self.assertEqual(best_cost, 'gpt-4o-mini')  # Lower cost


class CircuitBreakerServiceTestCase(TestCase):
    def setUp(self):
        self.service = CircuitBreakerService()

    def test_record_success(self):
        """Test recording successful request"""
        self.service.record_success('gpt-4o')

        breaker = CircuitBreakerState.objects.get(model_name='gpt-4o')
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
            self.service.record_failure('test-model')

        breaker = CircuitBreakerState.objects.get(model_name='test-model')
        self.assertEqual(breaker.state, 'open')
        self.assertEqual(breaker.failure_count, 5)

    def test_can_make_request(self):
        """Test request permission checking"""
        # Closed circuit should allow requests
        self.assertTrue(self.service.can_make_request('new-model'))

        # Create open circuit
        CircuitBreakerState.objects.create(
            model_name='broken-model',
            state='open',
            last_failure=timezone.now()
        )

        self.assertFalse(self.service.can_make_request('broken-model'))

    def test_get_circuit_status(self):
        """Test getting circuit status"""
        CircuitBreakerState.objects.create(
            model_name='test-model',
            state='closed',
            failure_count=2
        )

        status = self.service.get_circuit_status('test-model')

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
        self.assertIn('input_cost_per_token', config)

    def test_get_models_by_criteria(self):
        """Test filtering models by criteria"""
        models = self.registry.get_models_by_criteria(
            task_type='text_generation',
            max_cost_per_token=0.00001
        )

        self.assertIsInstance(models, list)
        self.assertTrue(len(models) > 0)

        # Verify all returned models meet criteria
        for model in models:
            config = self.registry.get_model_config(model)
            self.assertLessEqual(config['input_cost_per_token'], 0.00001)

    def test_list_available_models(self):
        """Test listing all available models"""
        models = self.registry.list_available_models()

        self.assertIsInstance(models, dict)
        self.assertIn('gpt-4o', models)
        self.assertIn('claude-sonnet-4', models)

        # Verify structure
        for model_name, config in models.items():
            self.assertIn('provider', config)
            self.assertIn('capabilities', config)