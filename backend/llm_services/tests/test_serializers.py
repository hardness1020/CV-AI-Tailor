"""
Unit tests for LLM services serializers.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from ..models import (
    ModelPerformanceMetric,
    CircuitBreakerState,
    ModelCostTracking,
    JobDescriptionEmbedding,
    EnhancedArtifact,
    ArtifactChunk
)
from ..serializers import (
    ModelPerformanceMetricSerializer,
    CircuitBreakerStateSerializer,
    ModelCostTrackingSerializer,
    JobDescriptionEmbeddingSerializer,
    EnhancedArtifactSerializer,
    ArtifactChunkSerializer,
    ModelStatsSerializer,
    ModelSelectionRequestSerializer,
    ModelSelectionResponseSerializer,
    SystemHealthSerializer
)

User = get_user_model()


class ModelPerformanceMetricSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.metric = ModelPerformanceMetric.objects.create(
            model_name='gpt-4o',
            task_type='cv_generation',
            processing_time_ms=1500,
            tokens_used=800,
            cost_usd=Decimal('0.008'),
            quality_score=Decimal('0.85'),
            success=True,
            complexity_score=Decimal('0.6'),
            selection_strategy='balanced',
            fallback_used=False,
            metadata={'test': 'data'},
            user=self.user
        )

    def test_serialize_metric(self):
        """Test serializing a performance metric"""
        serializer = ModelPerformanceMetricSerializer(self.metric)
        data = serializer.data

        self.assertEqual(data['model_name'], 'gpt-4o')
        self.assertEqual(data['task_type'], 'cv_generation')
        self.assertEqual(data['processing_time_ms'], 1500)
        self.assertEqual(data['tokens_used'], 800)
        self.assertEqual(data['cost_usd'], '0.008000')
        self.assertEqual(data['quality_score'], '0.85')
        self.assertTrue(data['success'])
        self.assertEqual(data['user_email'], 'test@example.com')
        self.assertEqual(data['metadata'], {'test': 'data'})

    def test_deserialize_metric(self):
        """Test deserializing metric data"""
        data = {
            'model_name': 'claude-sonnet-4',
            'task_type': 'job_parsing',
            'processing_time_ms': 2000,
            'tokens_used': 1200,
            'cost_usd': '0.012000',
            'quality_score': '0.90',
            'success': True,
            'complexity_score': '0.7',
            'selection_strategy': 'performance_first',
            'fallback_used': True,
            'metadata': {'parser': 'v2'}
        }

        serializer = ModelPerformanceMetricSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Verify specific field values
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['model_name'], 'claude-sonnet-4')
        self.assertEqual(validated_data['cost_usd'], Decimal('0.012000'))
        self.assertTrue(validated_data['fallback_used'])

    def test_validation_errors(self):
        """Test serializer validation"""
        # Missing required fields
        serializer = ModelPerformanceMetricSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('model_name', serializer.errors)
        self.assertIn('task_type', serializer.errors)


class CircuitBreakerStateSerializerTestCase(TestCase):
    def setUp(self):
        self.breaker = CircuitBreakerState.objects.create(
            model_name='gpt-4o',
            failure_count=2,
            state='closed',
            failure_threshold=5,
            timeout_duration=30
        )

    def test_serialize_circuit_breaker(self):
        """Test serializing circuit breaker state"""
        serializer = CircuitBreakerStateSerializer(self.breaker)
        data = serializer.data

        self.assertEqual(data['model_name'], 'gpt-4o')
        self.assertEqual(data['failure_count'], 2)
        self.assertEqual(data['state'], 'closed')
        self.assertEqual(data['state_display'], 'Closed')
        self.assertEqual(data['failure_threshold'], 5)
        self.assertEqual(data['timeout_duration'], 30)
        self.assertTrue(data['is_healthy'])  # closed state is healthy

    def test_unhealthy_circuit_breaker(self):
        """Test serializing unhealthy circuit breaker"""
        self.breaker.state = 'open'
        self.breaker.save()

        serializer = CircuitBreakerStateSerializer(self.breaker)
        data = serializer.data

        self.assertEqual(data['state'], 'open')
        self.assertEqual(data['state_display'], 'Open')
        self.assertFalse(data['is_healthy'])

    def test_deserialize_circuit_breaker(self):
        """Test deserializing circuit breaker data"""
        data = {
            'model_name': 'new-model',
            'failure_count': 0,
            'state': 'closed',
            'failure_threshold': 10,
            'timeout_duration': 60
        }

        serializer = CircuitBreakerStateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data['model_name'], 'new-model')
        self.assertEqual(validated_data['failure_threshold'], 10)


class ModelCostTrackingSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.cost_entry = ModelCostTracking.objects.create(
            user=self.user,
            date=timezone.now().date(),
            model_name='gpt-4o',
            total_cost_usd=Decimal('0.150'),
            generation_count=15,
            avg_cost_per_generation=Decimal('0.010'),
            total_tokens_used=15000,
            avg_tokens_per_generation=1000
        )

    def test_serialize_cost_tracking(self):
        """Test serializing cost tracking data"""
        serializer = ModelCostTrackingSerializer(self.cost_entry)
        data = serializer.data

        self.assertEqual(data['user_email'], 'test@example.com')
        self.assertEqual(data['model_name'], 'gpt-4o')
        self.assertEqual(data['total_cost_usd'], '0.150000')
        self.assertEqual(data['generation_count'], 15)
        self.assertEqual(data['avg_cost_per_generation'], '0.010000')
        self.assertEqual(data['total_tokens_used'], 15000)
        self.assertEqual(data['avg_tokens_per_generation'], 1000)

    def test_deserialize_cost_tracking(self):
        """Test deserializing cost tracking data"""
        data = {
            'date': '2025-01-15',
            'model_name': 'claude-sonnet-4',
            'total_cost_usd': '0.250000',
            'generation_count': 10,
            'avg_cost_per_generation': '0.025000',
            'total_tokens_used': 5000,
            'avg_tokens_per_generation': 500
        }

        serializer = ModelCostTrackingSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data['model_name'], 'claude-sonnet-4')
        self.assertEqual(validated_data['total_cost_usd'], Decimal('0.250000'))


class JobDescriptionEmbeddingSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.embedding = JobDescriptionEmbedding.objects.create(
            user=self.user,
            job_description_hash='abc123def456',
            company_name='Tech Corp',
            role_title='Software Engineer',
            model_used='text-embedding-3-small',
            dimensions=1536,
            tokens_used=200,
            cost_usd=Decimal('0.0002'),
            access_count=5
        )

    def test_serialize_job_embedding(self):
        """Test serializing job description embedding"""
        serializer = JobDescriptionEmbeddingSerializer(self.embedding)
        data = serializer.data

        self.assertEqual(data['user_email'], 'test@example.com')
        self.assertEqual(data['job_description_hash'], 'abc123def456')
        self.assertEqual(data['company_name'], 'Tech Corp')
        self.assertEqual(data['role_title'], 'Software Engineer')
        self.assertEqual(data['model_used'], 'text-embedding-3-small')
        self.assertEqual(data['dimensions'], 1536)
        self.assertEqual(data['tokens_used'], 200)
        self.assertEqual(data['cost_usd'], '0.000200')
        self.assertEqual(data['access_count'], 5)

    def test_embedding_vector_write_only(self):
        """Test that embedding_vector is write-only"""
        serializer = JobDescriptionEmbeddingSerializer(self.embedding)
        data = serializer.data

        # embedding_vector should not be in serialized data
        self.assertNotIn('embedding_vector', data)

    def test_deserialize_job_embedding(self):
        """Test deserializing job embedding data"""
        data = {
            'company_name': 'New Corp',
            'role_title': 'Senior Engineer',
            'model_used': 'text-embedding-3-large',
            'dimensions': 3072,
            'tokens_used': 300,
            'cost_usd': '0.0003',
            'embedding_vector': [0.1, 0.2, 0.3] * 1024  # 3072 dimensions
        }

        serializer = JobDescriptionEmbeddingSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data['company_name'], 'New Corp')
        self.assertEqual(validated_data['dimensions'], 3072)
        self.assertIn('embedding_vector', validated_data)


class EnhancedArtifactSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.artifact = EnhancedArtifact.objects.create(
            user=self.user,
            title='Test Resume',
            content_type='pdf',
            raw_content='Resume content...',
            embedding_cost_usd=Decimal('0.005'),
            total_chunks=3,
            processing_time_ms=2000
        )

        # Create chunks for cost calculation
        ArtifactChunk.objects.create(
            artifact=self.artifact,
            chunk_index=0,
            content='Chunk 1',
            content_hash='hash1',
            processing_cost_usd=Decimal('0.001')
        )
        ArtifactChunk.objects.create(
            artifact=self.artifact,
            chunk_index=1,
            content='Chunk 2',
            content_hash='hash2',
            processing_cost_usd=Decimal('0.002')
        )

    def test_serialize_enhanced_artifact(self):
        """Test serializing enhanced artifact"""
        serializer = EnhancedArtifactSerializer(self.artifact)
        data = serializer.data

        self.assertEqual(data['user_email'], 'test@example.com')
        self.assertEqual(data['title'], 'Test Resume')
        self.assertEqual(data['content_type'], 'pdf')
        self.assertEqual(data['embedding_cost_usd'], '0.005000')
        self.assertEqual(data['total_chunks'], 3)
        self.assertEqual(data['processing_time_ms'], 2000)

        # Test calculated total processing cost
        expected_cost = Decimal('0.005') + Decimal('0.001') + Decimal('0.002')  # embedding + chunks
        self.assertEqual(Decimal(data['total_processing_cost']), expected_cost)

    def test_embedding_fields_write_only(self):
        """Test that embedding fields are write-only"""
        serializer = EnhancedArtifactSerializer(self.artifact)
        data = serializer.data

        # Embedding fields should not be in serialized data
        self.assertNotIn('content_embedding', data)
        self.assertNotIn('summary_embedding', data)

    def test_deserialize_enhanced_artifact(self):
        """Test deserializing enhanced artifact data"""
        data = {
            'title': 'New Document',
            'content_type': 'markdown',
            'embedding_model': 'text-embedding-3-large',
            'embedding_dimensions': 3072,
            'embedding_cost_usd': '0.010',
            'processing_time_ms': 3000,
            'content_embedding': [0.1] * 3072,
            'summary_embedding': [0.2] * 3072
        }

        serializer = EnhancedArtifactSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data['title'], 'New Document')
        self.assertEqual(validated_data['embedding_dimensions'], 3072)
        self.assertIn('content_embedding', validated_data)
        self.assertIn('summary_embedding', validated_data)


class ArtifactChunkSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.artifact = EnhancedArtifact.objects.create(
            user=self.user,
            title='Test Document',
            content_type='text',
            raw_content='Document content...'
        )

        self.chunk = ArtifactChunk.objects.create(
            artifact=self.artifact,
            chunk_index=0,
            content='First chunk content...',
            metadata={'section': 'introduction'},
            content_hash='abc123',
            model_used='text-embedding-3-small',
            tokens_used=150,
            processing_cost_usd=Decimal('0.0015')
        )

    def test_serialize_artifact_chunk(self):
        """Test serializing artifact chunk"""
        serializer = ArtifactChunkSerializer(self.chunk)
        data = serializer.data

        self.assertEqual(data['artifact_title'], 'Test Document')
        self.assertEqual(data['chunk_index'], 0)
        self.assertEqual(data['content'], 'First chunk content...')
        self.assertEqual(data['metadata'], {'section': 'introduction'})
        self.assertEqual(data['content_hash'], 'abc123')
        self.assertEqual(data['model_used'], 'text-embedding-3-small')
        self.assertEqual(data['tokens_used'], 150)
        self.assertEqual(data['processing_cost_usd'], '0.001500')

    def test_embedding_vector_write_only(self):
        """Test that embedding_vector is write-only"""
        serializer = ArtifactChunkSerializer(self.chunk)
        data = serializer.data

        # embedding_vector should not be in serialized data
        self.assertNotIn('embedding_vector', data)

    def test_deserialize_artifact_chunk(self):
        """Test deserializing artifact chunk data"""
        data = {
            'chunk_index': 1,
            'content': 'Second chunk content...',
            'metadata': {'section': 'body'},
            'model_used': 'text-embedding-3-large',
            'tokens_used': 200,
            'processing_cost_usd': '0.0020',
            'embedding_vector': [0.1, 0.2, 0.3] * 512
        }

        serializer = ArtifactChunkSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data['chunk_index'], 1)
        self.assertEqual(validated_data['content'], 'Second chunk content...')
        self.assertIn('embedding_vector', validated_data)


class ModelStatsSerializerTestCase(TestCase):
    def test_serialize_model_stats(self):
        """Test serializing model statistics"""
        stats_data = {
            'model_name': 'gpt-4o',
            'total_requests': 150,
            'success_rate': 96.5,
            'avg_processing_time_ms': 1250.0,
            'total_cost_usd': Decimal('1.275'),
            'avg_quality_score': 0.85,
            'last_used': timezone.now()
        }

        serializer = ModelStatsSerializer(data=stats_data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data['model_name'], 'gpt-4o')
        self.assertEqual(validated_data['total_requests'], 150)
        self.assertEqual(validated_data['success_rate'], 96.5)


class ModelSelectionRequestSerializerTestCase(TestCase):
    def test_valid_request_data(self):
        """Test valid model selection request"""
        data = {
            'task_type': 'cv_generation',
            'complexity_score': 0.7,
            'user_budget': '0.05',
            'strategy': 'balanced'
        }

        serializer = ModelSelectionRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data['task_type'], 'cv_generation')
        self.assertEqual(validated_data['complexity_score'], 0.7)
        self.assertEqual(validated_data['strategy'], 'balanced')

    def test_invalid_task_type(self):
        """Test invalid task type"""
        data = {
            'task_type': 'invalid_task',
            'complexity_score': 0.5
        }

        serializer = ModelSelectionRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('task_type', serializer.errors)

    def test_invalid_complexity_score(self):
        """Test invalid complexity score"""
        data = {
            'task_type': 'cv_generation',
            'complexity_score': 1.5  # > 1.0
        }

        serializer = ModelSelectionRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('complexity_score', serializer.errors)

    def test_optional_fields(self):
        """Test that optional fields work correctly"""
        data = {
            'task_type': 'embedding'
            # All other fields optional
        }

        serializer = ModelSelectionRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class ModelSelectionResponseSerializerTestCase(TestCase):
    def test_serialize_selection_response(self):
        """Test serializing model selection response"""
        response_data = {
            'selected_model': 'gpt-4o',
            'reasoning': 'Selected GPT-4o for balanced performance and cost',
            'estimated_cost_usd': Decimal('0.025'),
            'fallback_models': ['gpt-4o-mini', 'claude-sonnet-4']
        }

        serializer = ModelSelectionResponseSerializer(data=response_data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data['selected_model'], 'gpt-4o')
        self.assertEqual(len(validated_data['fallback_models']), 2)


class SystemHealthSerializerTestCase(TestCase):
    def test_serialize_system_health(self):
        """Test serializing system health data"""
        health_data = {
            'healthy_models': 5,
            'unhealthy_models': 1,
            'circuit_breakers_open': 1,
            'total_cost_today': Decimal('0.45'),
            'avg_response_time_ms': 1150.2,
            'success_rate': 95.5
        }

        serializer = SystemHealthSerializer(data=health_data)
        self.assertTrue(serializer.is_valid())

        validated_data = serializer.validated_data
        self.assertEqual(validated_data['healthy_models'], 5)
        self.assertEqual(validated_data['unhealthy_models'], 1)
        self.assertEqual(validated_data['success_rate'], 95.5)