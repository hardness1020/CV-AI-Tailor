"""
Unit tests for LLM services API views.
"""

import json
from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import (
    ModelPerformanceMetric,
    CircuitBreakerState,
    ModelCostTracking,
    JobDescriptionEmbedding,
    EnhancedArtifact,
    ArtifactChunk
)

User = get_user_model()


class BaseAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )

        # Create JWT tokens
        refresh = RefreshToken.for_user(self.user)
        self.user_token = str(refresh.access_token)

        staff_refresh = RefreshToken.for_user(self.staff_user)
        self.staff_token = str(staff_refresh.access_token)

    def authenticate_user(self):
        """Authenticate as regular user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')

    def authenticate_staff(self):
        """Authenticate as staff user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')


class ModelPerformanceMetricViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('llm_services:performance-metrics-list')

        # Create test metrics
        self.metric1 = ModelPerformanceMetric.objects.create(
            model_name='gpt-4o',
            task_type='cv_generation',
            processing_time_ms=1500,
            tokens_used=800,
            cost_usd=Decimal('0.008'),
            success=True,
            user=self.user
        )
        self.metric2 = ModelPerformanceMetric.objects.create(
            model_name='gpt-4o-mini',
            task_type='job_parsing',
            processing_time_ms=800,
            tokens_used=400,
            cost_usd=Decimal('0.002'),
            success=False,
            user=self.staff_user
        )

    def test_list_metrics_authenticated(self):
        """Test listing metrics as authenticated user"""
        self.authenticate_user()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        # User should only see their own metrics
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['model_name'], 'gpt-4o')

    def test_list_metrics_staff(self):
        """Test listing metrics as staff user"""
        self.authenticate_staff()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Staff should see all metrics
        self.assertEqual(len(response.data['results']), 2)

    def test_list_metrics_unauthenticated(self):
        """Test listing metrics without authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_by_model_name(self):
        """Test filtering by model name"""
        self.authenticate_user()
        response = self.client.get(self.url, {'model_name': 'gpt-4o'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['model_name'], 'gpt-4o')

    def test_filter_by_task_type(self):
        """Test filtering by task type"""
        self.authenticate_user()
        response = self.client.get(self.url, {'task_type': 'cv_generation'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_by_success(self):
        """Test filtering by success status"""
        self.authenticate_user()
        response = self.client.get(self.url, {'success': 'true'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertTrue(response.data['results'][0]['success'])

    def test_date_range_filter(self):
        """Test filtering by date range"""
        self.authenticate_user()
        today = timezone.now().date()
        response = self.client.get(self.url, {
            'date_from': str(today),
            'date_to': str(today)
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find metrics created today
        self.assertTrue(len(response.data['results']) >= 0)

    def test_summary_endpoint(self):
        """Test performance summary endpoint"""
        self.authenticate_user()
        url = reverse('llm_services:performance-metrics-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('today', response.data)
        self.assertIn('yesterday', response.data)
        self.assertIn('total_requests', response.data['today'])
        self.assertIn('success_rate', response.data['today'])


class CircuitBreakerStateViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('llm_services:circuit-breakers-list')

        self.breaker = CircuitBreakerState.objects.create(
            model_name='gpt-4o',
            state='closed',
            failure_count=0
        )

    def test_list_circuit_breakers(self):
        """Test listing circuit breakers"""
        self.authenticate_user()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['model_name'], 'gpt-4o')
        self.assertTrue(response.data[0]['is_healthy'])

    def test_reset_circuit_breaker(self):
        """Test resetting a circuit breaker"""
        self.authenticate_user()
        # First make it fail
        self.breaker.state = 'open'
        self.breaker.failure_count = 5
        self.breaker.save()

        url = reverse('llm_services:circuit-breakers-reset', kwargs={'model_name': 'gpt-4o'})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['new_state'], 'closed')

        # Verify the reset worked
        self.breaker.refresh_from_db()
        self.assertEqual(self.breaker.state, 'closed')
        self.assertEqual(self.breaker.failure_count, 0)

    def test_reset_nonexistent_breaker(self):
        """Test resetting non-existent circuit breaker"""
        self.authenticate_user()
        url = reverse('llm_services:circuit-breakers-reset', kwargs={'model_name': 'nonexistent'})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_health_status_endpoint(self):
        """Test health status endpoint"""
        self.authenticate_user()
        # Create another breaker in open state
        CircuitBreakerState.objects.create(
            model_name='broken-model',
            state='open',
            failure_count=5,
            last_failure=timezone.now()
        )

        url = reverse('llm_services:circuit-breakers-health-status')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_models'], 2)
        self.assertEqual(response.data['healthy_models'], 1)
        self.assertEqual(response.data['unhealthy_models'], 1)
        self.assertIn('models_by_state', response.data)


class ModelCostTrackingViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('llm_services:cost-tracking-list')

        self.cost_entry = ModelCostTracking.objects.create(
            user=self.user,
            date=timezone.now().date(),
            model_name='gpt-4o',
            total_cost_usd=Decimal('0.150'),
            generation_count=15,
            avg_cost_per_generation=Decimal('0.010')
        )

    def test_list_cost_tracking(self):
        """Test listing cost tracking data"""
        self.authenticate_user()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['model_name'], 'gpt-4o')

    def test_monthly_summary(self):
        """Test monthly summary endpoint"""
        self.authenticate_user()
        url = reverse('llm_services:cost-tracking-monthly-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('month', response.data)
        self.assertIn('models', response.data)
        self.assertTrue(len(response.data['models']) >= 1)


class JobDescriptionEmbeddingViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('llm_services:job-embeddings-list')

        self.embedding = JobDescriptionEmbedding.objects.create(
            user=self.user,
            job_description_hash='test_hash_123',
            company_name='Tech Corp',
            role_title='Software Engineer',
            access_count=5
        )

    def test_list_job_embeddings(self):
        """Test listing job embeddings"""
        self.authenticate_user()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['company_name'], 'Tech Corp')

    def test_cache_stats(self):
        """Test cache statistics endpoint"""
        self.authenticate_user()
        url = reverse('llm_services:job-embeddings-cache-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_embeddings', response.data)
        self.assertIn('unique_companies', response.data)
        self.assertIn('cache_hit_rate', response.data)
        self.assertEqual(response.data['total_embeddings'], 1)


class EnhancedArtifactViewSetTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('llm_services:enhanced-artifacts-list')

        self.artifact = EnhancedArtifact.objects.create(
            user=self.user,
            title='Test Resume',
            content_type='pdf',
            raw_content='Resume content...'
        )

        # Create chunks
        ArtifactChunk.objects.create(
            artifact=self.artifact,
            chunk_index=0,
            content='Chunk 1 content',
            content_hash='hash1'
        )
        ArtifactChunk.objects.create(
            artifact=self.artifact,
            chunk_index=1,
            content='Chunk 2 content',
            content_hash='hash2'
        )

    def test_list_enhanced_artifacts(self):
        """Test listing enhanced artifacts"""
        self.authenticate_user()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Resume')

    def test_get_artifact_chunks(self):
        """Test getting chunks for an artifact"""
        self.authenticate_user()
        url = reverse('llm_services:enhanced-artifacts-chunks', kwargs={'pk': self.artifact.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['chunk_index'], 0)
        self.assertEqual(response.data[1]['chunk_index'], 1)


class ModelStatsViewTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('llm_services:model-stats')

        # Create test metrics
        ModelPerformanceMetric.objects.create(
            model_name='gpt-4o',
            task_type='cv_generation',
            processing_time_ms=1000,
            cost_usd=Decimal('0.008'),
            success=True,
            user=self.user
        )
        ModelPerformanceMetric.objects.create(
            model_name='gpt-4o',
            task_type='cv_generation',
            processing_time_ms=1200,
            cost_usd=Decimal('0.010'),
            success=True,
            user=self.user
        )

    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    def test_model_stats(self, mock_cache_set, mock_cache_get):
        """Test model statistics endpoint"""
        # Mock cache miss
        mock_cache_get.return_value = None

        self.authenticate_user()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

        # Check data structure
        model_stat = response.data[0]
        self.assertIn('model_name', model_stat)
        self.assertIn('total_requests', model_stat)
        self.assertIn('success_rate', model_stat)
        self.assertIn('avg_processing_time', model_stat)
        self.assertIn('total_cost', model_stat)

        # Verify cache was set
        mock_cache_set.assert_called_once()


class ModelSelectionViewTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('llm_services:select-model')

    @patch('llm_services.views.EnhancedLLMService')
    @patch('llm_services.views.ModelRegistry')
    def test_select_model_success(self, mock_registry, mock_service):
        """Test successful model selection"""
        # Mock service
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        mock_service_instance._select_model_for_task.return_value = ('gpt-4o', 'Selected for balanced performance')

        # Mock registry
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.get_model_config.return_value = {
            'input_cost_per_token': 0.0000025
        }
        mock_registry_instance.get_models_by_criteria.return_value = ['gpt-4o-mini', 'claude-sonnet-4']

        self.authenticate_user()
        data = {
            'task_type': 'cv_generation',
            'complexity_score': 0.7,
            'strategy': 'balanced'
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['selected_model'], 'gpt-4o')
        self.assertIn('reasoning', response.data)
        self.assertIn('estimated_cost_usd', response.data)
        self.assertIn('fallback_models', response.data)

    def test_select_model_invalid_data(self):
        """Test model selection with invalid data"""
        self.authenticate_user()
        data = {
            'task_type': 'invalid_task',  # Invalid task type
            'complexity_score': 1.5  # Invalid complexity score
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('task_type', response.data)

    @patch('llm_services.views.EnhancedLLMService')
    def test_select_model_service_error(self, mock_service):
        """Test model selection with service error"""
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        mock_service_instance._select_model_for_task.side_effect = Exception("Service error")

        self.authenticate_user()
        data = {
            'task_type': 'cv_generation',
            'complexity_score': 0.5
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)


class SystemHealthViewTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('llm_services:system-health')

        # Create test data
        CircuitBreakerState.objects.create(
            model_name='gpt-4o',
            state='closed'
        )
        CircuitBreakerState.objects.create(
            model_name='broken-model',
            state='open'
        )

        ModelPerformanceMetric.objects.create(
            model_name='gpt-4o',
            task_type='cv_generation',
            processing_time_ms=1000,
            cost_usd=Decimal('0.008'),
            success=True,
            user=self.user,
            created_at=timezone.now()
        )

    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    def test_system_health(self, mock_cache_set, mock_cache_get):
        """Test system health endpoint"""
        # Mock cache miss
        mock_cache_get.return_value = None

        self.authenticate_user()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['healthy_models'], 1)
        self.assertEqual(response.data['unhealthy_models'], 1)
        self.assertEqual(response.data['circuit_breakers_open'], 1)
        self.assertIn('total_cost_today', response.data)
        self.assertIn('avg_response_time_ms', response.data)
        self.assertIn('success_rate', response.data)


class AvailableModelsViewTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('llm_services:available-models')

    @patch('llm_services.views.ModelRegistry')
    def test_available_models(self, mock_registry):
        """Test available models endpoint"""
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.list_available_models.return_value = {
            'gpt-4o': {
                'provider': 'openai',
                'context_window': 128000,
                'input_cost_per_token': 0.0000025,
                'capabilities': ['text_generation']
            },
            'claude-sonnet-4': {
                'provider': 'anthropic',
                'context_window': 200000,
                'input_cost_per_token': 0.000003,
                'capabilities': ['text_generation', 'analysis']
            }
        }

        # Create circuit breaker state
        CircuitBreakerState.objects.create(
            model_name='gpt-4o',
            state='closed'
        )

        self.authenticate_user()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('gpt-4o', response.data)
        self.assertIn('claude-sonnet-4', response.data)

        # Check that circuit breaker status is added
        gpt4o_config = response.data['gpt-4o']
        self.assertIn('circuit_breaker_status', gpt4o_config)
        self.assertIn('is_available', gpt4o_config)
        self.assertEqual(gpt4o_config['circuit_breaker_status'], 'closed')
        self.assertTrue(gpt4o_config['is_available'])

    @patch('llm_services.views.ModelRegistry')
    def test_available_models_service_error(self, mock_registry):
        """Test available models with service error"""
        mock_registry_instance = Mock()
        mock_registry.return_value = mock_registry_instance
        mock_registry_instance.list_available_models.side_effect = Exception("Registry error")

        self.authenticate_user()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)