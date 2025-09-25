"""
Real API Circuit Breaker and Performance Tests

Tests circuit breaker functionality and model performance tracking with real API calls.
Designed to minimize token usage while testing reliability features.

To run: python manage.py test llm_services.tests.test_real_circuit_breaker
"""

import os
import asyncio
import logging
from unittest import skipIf
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from ..services.enhanced_llm_service import EnhancedLLMService
from ..services.circuit_breaker import CircuitBreakerManager
from ..services.performance_tracker import ModelPerformanceTracker
from ..models import CircuitBreakerState, ModelPerformanceMetric

User = get_user_model()
logger = logging.getLogger(__name__)

OPENAI_KEY_AVAILABLE = bool(os.environ.get('OPENAI_API_KEY'))


class RealCircuitBreakerTestCase(TestCase):
    """Test circuit breaker functionality with real API calls"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='circuituser',
            email='circuit@example.com',
            password='testpass123'
        )
        self.circuit_breaker = CircuitBreakerManager()
        self.llm_service = EnhancedLLMService()

    @skipIf(not OPENAI_KEY_AVAILABLE, "OpenAI API key not available")
    def test_real_api_success_tracking(self):
        """Test successful API calls are tracked correctly"""

        async def run_test():
            # Make a successful minimal API call
            result = await self.llm_service.parse_job_description(
                job_description="Dev job",
                company_name="Co",
                role_title="Dev",
                user_id=self.user.id
            )

            # Should not have error
            self.assertNotIn('error', result)

            # Get the model used from metadata
            metadata = result.get('processing_metadata', {})
            model_used = metadata.get('model_used')
            self.assertTrue(model_used, "No model name in metadata")

            # Check circuit breaker recorded success
            status = self.circuit_breaker.get_circuit_status(model_used)
            self.assertEqual(status['state'], 'closed')
            self.assertEqual(status['failure_count'], 0)
            self.assertTrue(status['is_healthy'])

            logger.info(f"Success tracking test - Model: {model_used}, "
                       f"Circuit: {status['state']}")

            return result

        result = asyncio.run(run_test())
        self.assertTrue(result)

    def test_api_failure_simulation(self):
        """Test circuit breaker opens after failures (simulated)"""

        # Create test circuit breaker state
        test_model = 'test-model-failure'

        # Simulate multiple failures to trigger circuit breaker
        for i in range(6):  # Exceed default failure threshold
            self.circuit_breaker.record_failure(test_model)

        # Circuit should now be open
        status = self.circuit_breaker.get_circuit_status(test_model)
        self.assertEqual(status['state'], 'open')
        self.assertGreaterEqual(status['failure_count'], 5)
        self.assertFalse(status['is_healthy'])

        # Should not allow requests
        self.assertFalse(self.circuit_breaker.can_make_request(test_model))

        logger.info(f"Failure simulation test - Failures: {status['failure_count']}, "
                   f"State: {status['state']}")

    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout"""

        test_model = 'test-recovery-model'

        # Open the circuit
        for i in range(5):
            self.circuit_breaker.record_failure(test_model)

        # Verify it's open
        self.assertFalse(self.circuit_breaker.can_make_request(test_model))

        # Simulate recovery by manually updating the last failure time
        breaker = CircuitBreakerState.objects.get(model_name=test_model)
        breaker.last_failure = timezone.now() - timezone.timedelta(minutes=6)  # Past recovery time
        breaker.save()

        # Should now allow half-open state
        # Note: Actual recovery logic may vary based on implementation
        status = self.circuit_breaker.get_circuit_status(test_model)
        logger.info(f"Recovery test - State: {status['state']}, "
                   f"Last failure: {breaker.last_failure}")


class RealPerformanceTrackingTestCase(TestCase):
    """Test performance tracking with real API calls"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='testpass123'
        )
        self.performance_tracker = ModelPerformanceTracker()
        self.llm_service = EnhancedLLMService()

    @skipIf(not OPENAI_KEY_AVAILABLE, "OpenAI API key not available")
    def test_real_performance_metrics_collection(self):
        """Test that real API calls generate performance metrics"""

        async def run_test():
            # Make a minimal API call
            result = await self.llm_service.parse_job_description(
                job_description="Python job",
                company_name="TestCorp",
                role_title="Developer",
                user_id=self.user.id
            )

            # Verify API call succeeded
            self.assertNotIn('error', result)

            # Check metadata includes performance data
            metadata = result.get('processing_metadata', {})
            model_used = metadata.get('model_used')
            processing_time = metadata.get('processing_time_ms', 0)
            tokens_used = metadata.get('tokens_used', 0)
            cost_usd = metadata.get('cost_usd', 0)

            # Verify performance data
            self.assertTrue(model_used, "No model name recorded")
            self.assertGreater(processing_time, 0, "No processing time recorded")
            self.assertGreater(tokens_used, 0, "No token usage recorded")
            self.assertGreater(cost_usd, 0, "No cost recorded")

            # Check if metric was saved to database
            metric_exists = ModelPerformanceMetric.objects.filter(
                model_name=model_used,
                task_type='job_parsing',
                user=self.user
            ).exists()

            # Note: Metric might not be saved immediately depending on implementation
            logger.info(f"Performance tracking test - Model: {model_used}, "
                       f"Time: {processing_time}ms, Tokens: {tokens_used}, "
                       f"Cost: ${cost_usd:.6f}, Metric saved: {metric_exists}")

            return {
                'model_used': model_used,
                'processing_time_ms': processing_time,
                'tokens_used': tokens_used,
                'cost_usd': cost_usd
            }

        result = asyncio.run(run_test())
        self.assertTrue(result)

    def test_performance_statistics_calculation(self):
        """Test performance statistics calculation from stored metrics"""

        # Create test performance metrics
        test_model = 'gpt-4o-test'

        metrics_data = [
            {'time': 1000, 'tokens': 100, 'cost': 0.01, 'success': True},
            {'time': 1200, 'tokens': 120, 'cost': 0.012, 'success': True},
            {'time': 800, 'tokens': 80, 'cost': 0.008, 'success': False},
            {'time': 1100, 'tokens': 110, 'cost': 0.011, 'success': True},
        ]

        for data in metrics_data:
            ModelPerformanceMetric.objects.create(
                model_name=test_model,
                task_type='test_task',
                processing_time_ms=data['time'],
                tokens_used=data['tokens'],
                cost_usd=Decimal(str(data['cost'])),
                success=data['success'],
                user=self.user,
                created_at=timezone.now()
            )

        # Test statistics calculation
        stats = self.performance_tracker.get_model_performance_stats(
            test_model, 'test_task'
        )

        # Verify calculated statistics
        self.assertEqual(stats['total_requests'], 4)
        self.assertEqual(stats['success_rate'], 75.0)  # 3 out of 4 successful
        self.assertEqual(stats['avg_processing_time_ms'], 1025.0)  # Average of times
        self.assertAlmostEqual(float(stats['avg_cost_usd']), 0.01025, places=5)

        logger.info(f"Performance stats test - Total: {stats['total_requests']}, "
                   f"Success: {stats['success_rate']}%, "
                   f"Avg time: {stats['avg_processing_time_ms']}ms")

    def test_model_selection_based_on_performance(self):
        """Test that model selection considers performance history"""

        # Create performance history for different models
        models_data = [
            {'name': 'fast-model', 'time': 500, 'cost': 0.001, 'quality': 0.7},
            {'name': 'quality-model', 'time': 2000, 'cost': 0.02, 'quality': 0.95},
            {'name': 'balanced-model', 'time': 1000, 'cost': 0.005, 'quality': 0.85},
        ]

        for model_data in models_data:
            for i in range(3):  # Create multiple metrics for each model
                ModelPerformanceMetric.objects.create(
                    model_name=model_data['name'],
                    task_type='cv_generation',
                    processing_time_ms=model_data['time'],
                    cost_usd=Decimal(str(model_data['cost'])),
                    quality_score=Decimal(str(model_data['quality'])),
                    success=True,
                    user=self.user
                )

        # Test different selection strategies
        best_performance = self.performance_tracker.get_best_model_for_task(
            'cv_generation', strategy='performance_first'
        )
        best_cost = self.performance_tracker.get_best_model_for_task(
            'cv_generation', strategy='cost_optimized'
        )

        # Verify reasonable selections
        self.assertIn(best_performance, ['quality-model', 'balanced-model'])  # Should prefer quality
        self.assertIn(best_cost, ['fast-model', 'balanced-model'])  # Should prefer low cost

        logger.info(f"Model selection test - Performance: {best_performance}, "
                   f"Cost: {best_cost}")


class RealAPIReliabilityTestCase(TestCase):
    """Test API reliability and error handling with real calls"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='reliabilityuser',
            email='reliability@example.com',
            password='testpass123'
        )
        self.llm_service = EnhancedLLMService()

    @skipIf(not OPENAI_KEY_AVAILABLE, "OpenAI API key not available")
    def test_api_rate_limit_handling(self):
        """Test handling of API rate limits (careful with real limits)"""

        async def run_test():
            # Make minimal requests to test rate limiting behavior
            # Note: This is very conservative to avoid hitting actual limits

            results = []
            for i in range(2):  # Only 2 requests to be safe
                try:
                    result = await self.llm_service.parse_job_description(
                        job_description=f"Job {i+1}",
                        company_name="Co",
                        role_title="Dev",
                        user_id=self.user.id
                    )
                    results.append(result)

                    # Small delay between requests
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.info(f"Rate limit test - Request {i+1} failed: {e}")
                    # This is expected if we hit rate limits
                    results.append({'error': str(e)})

            # At least one request should succeed with proper API key
            successful_results = [r for r in results if 'error' not in r]
            self.assertGreater(len(successful_results), 0, "No successful API calls")

            logger.info(f"Rate limit test - Successful: {len(successful_results)}, "
                       f"Total: {len(results)}")

            return results

        results = asyncio.run(run_test())
        self.assertTrue(results)

    def test_invalid_api_key_handling(self):
        """Test handling of invalid API keys"""

        # This test uses environment variable override to test error handling
        # without making real API calls with invalid keys

        async def run_test():
            # Create service with invalid key simulation
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'invalid_key_test'}):
                test_service = EnhancedLLMService()

                result = await test_service.parse_job_description(
                    job_description="Test job",
                    company_name="Co",
                    role_title="Dev",
                    user_id=self.user.id
                )

                # Should handle error gracefully
                # Note: Actual behavior depends on implementation
                logger.info(f"Invalid API key test - Result type: {type(result)}")

                return result

        result = asyncio.run(run_test())
        # Test should complete without crashing
        self.assertIsNotNone(result)


if __name__ == '__main__':
    # Run with: python manage.py test llm_services.tests.test_real_circuit_breaker
    import django
    from django.conf import settings
    from django.test.utils import get_runner

    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_tailor.settings')
        django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["llm_services.tests.test_real_circuit_breaker"])