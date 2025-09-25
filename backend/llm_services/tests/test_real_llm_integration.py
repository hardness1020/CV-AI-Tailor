"""
Real LLM API Integration Tests

These tests make actual API calls to LLM providers to verify integration works correctly.
They are designed to minimize token usage while ensuring core functionality works.

To run these tests:
1. Set environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY (optional)
2. Run with: python manage.py test llm_services.tests.test_real_llm_integration
3. Or pytest: pytest llm_services/tests/test_real_llm_integration.py -v

Note: These tests will consume actual API tokens and incur costs.
"""

import os
import pytest
import asyncio
import logging
from decimal import Decimal
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from unittest import skipIf

from ..services.enhanced_llm_service import EnhancedLLMService
from ..services.embedding_service import FlexibleEmbeddingService
from ..services.document_processor import AdvancedDocumentProcessor

User = get_user_model()
logger = logging.getLogger(__name__)

# Skip tests if API keys are not available
OPENAI_KEY_AVAILABLE = bool(os.environ.get('OPENAI_API_KEY'))
ANTHROPIC_KEY_AVAILABLE = bool(os.environ.get('ANTHROPIC_API_KEY'))

# Minimal test data to reduce token usage
MINIMAL_JOB_DESC = "Python dev. Skills: Django, REST APIs."
MINIMAL_ARTIFACTS = [
    {
        'id': 1,
        'title': 'API Project',
        'description': 'Built REST API with Django',
        'artifact_type': 'project',
        'technologies': ['Python', 'Django'],
        'start_date': '2023-01-01',
        'end_date': '2023-06-01'
    }
]
MINIMAL_JOB_DATA = {
    'company_name': 'TestCorp',
    'role_title': 'Python Dev',
    'must_have_skills': ['Python'],
    'nice_to_have_skills': ['Django'],
    'key_responsibilities': ['Build APIs']
}


class RealLLMIntegrationTestCase(TestCase):
    """Test real LLM API integration with minimal token usage"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.llm_service = EnhancedLLMService()

    @skipIf(not OPENAI_KEY_AVAILABLE, "OpenAI API key not available")
    def test_real_job_description_parsing(self):
        """Test real job description parsing with minimal tokens"""

        async def run_test():
            result = await self.llm_service.parse_job_description(
                job_description=MINIMAL_JOB_DESC,
                company_name="TestCorp",
                role_title="Dev",
                user_id=self.user.id
            )

            # Verify basic structure without checking specific content
            # (since LLM outputs can vary)
            self.assertIsInstance(result, dict)
            self.assertNotIn('error', result, f"API call failed: {result}")

            # Check expected fields exist
            expected_fields = ['company_name', 'role_title', 'must_have_skills', 'processing_metadata']
            for field in expected_fields:
                self.assertIn(field, result, f"Missing field: {field}")

            # Verify metadata tracking
            metadata = result.get('processing_metadata', {})
            self.assertIn('model_used', metadata)
            self.assertIn('processing_time_ms', metadata)
            self.assertGreater(metadata.get('tokens_used', 0), 0)

            # Verify cost tracking
            cost = metadata.get('cost_usd', 0)
            self.assertGreater(cost, 0)
            self.assertLess(cost, 0.01, "Test used too many tokens")  # Safety check

            logger.info(f"Job parsing test - Tokens: {metadata.get('tokens_used', 0)}, "
                       f"Cost: ${cost:.6f}, Model: {metadata.get('model_used', 'unknown')}")

            return result

        # Run async test
        result = asyncio.run(run_test())
        self.assertTrue(result)

    @skipIf(not OPENAI_KEY_AVAILABLE, "OpenAI API key not available")
    def test_real_cv_generation_minimal(self):
        """Test real CV generation with minimal input to reduce tokens"""

        async def run_test():
            result = await self.llm_service.generate_cv_content(
                job_data=MINIMAL_JOB_DATA,
                artifacts=MINIMAL_ARTIFACTS,
                generation_preferences={'style': 'concise'},
                user_id=self.user.id
            )

            # Verify basic structure
            self.assertIsInstance(result, dict)
            self.assertNotIn('error', result, f"CV generation failed: {result}")

            # Check content structure
            content = result.get('content', {})
            self.assertIsInstance(content, dict)
            self.assertTrue(len(content) > 0, "No content generated")

            # Verify processing metadata
            metadata = result.get('processing_metadata', {})
            self.assertIn('model_used', metadata)
            self.assertGreater(metadata.get('tokens_used', 0), 0)

            # Cost safety check
            cost = metadata.get('cost_usd', 0)
            self.assertLess(cost, 0.05, "Test used too many tokens")  # Higher limit for CV gen

            logger.info(f"CV generation test - Tokens: {metadata.get('tokens_used', 0)}, "
                       f"Cost: ${cost:.6f}, Model: {metadata.get('model_used', 'unknown')}")

            return result

        result = asyncio.run(run_test())
        self.assertTrue(result)

    @skipIf(not OPENAI_KEY_AVAILABLE, "OpenAI API key not available")
    def test_real_artifact_ranking(self):
        """Test real artifact ranking with minimal data"""

        async def run_test():
            job_skills = ['Python', 'Django']
            result = await self.llm_service.rank_artifacts_by_relevance(
                artifacts=MINIMAL_ARTIFACTS,
                job_requirements=job_skills,
                user_id=self.user.id
            )

            # Verify basic structure
            self.assertIsInstance(result, list)
            self.assertTrue(len(result) > 0, "No ranked artifacts returned")

            # Check first ranked artifact has expected fields
            first_artifact = result[0]
            self.assertIn('id', first_artifact)
            self.assertIn('relevance_score', first_artifact)
            self.assertIn('title', first_artifact)

            # Score should be 0-10
            score = first_artifact.get('relevance_score', 0)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 10)

            logger.info(f"Artifact ranking test - Artifacts ranked: {len(result)}, "
                       f"Top score: {score}")

            return result

        result = asyncio.run(run_test())
        self.assertTrue(result)


class RealEmbeddingIntegrationTestCase(TestCase):
    """Test real embedding API integration"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.embedding_service = FlexibleEmbeddingService()

    @skipIf(not OPENAI_KEY_AVAILABLE, "OpenAI API key not available")
    def test_real_embedding_generation(self):
        """Test real embedding generation with minimal text"""

        async def run_test():
            # Use very short text to minimize tokens
            test_text = "Python developer"

            result = await self.embedding_service.generate_embedding(
                content=test_text,
                user_id=self.user.id
            )

            # Verify basic structure
            self.assertIsInstance(result, dict)
            self.assertTrue(result.get('success', False), f"Embedding failed: {result}")

            # Check embedding vector
            embedding = result.get('embedding', [])
            self.assertIsInstance(embedding, list)
            self.assertGreater(len(embedding), 0, "Empty embedding vector")
            self.assertEqual(len(embedding), 1536, "Unexpected embedding dimension")

            # Verify all values are numbers
            for val in embedding[:5]:  # Check first 5 values
                self.assertIsInstance(val, (int, float))

            # Check cost tracking
            cost = result.get('cost_usd', 0)
            self.assertGreater(cost, 0)
            self.assertLess(cost, 0.001, "Embedding test used too many tokens")

            logger.info(f"Embedding test - Tokens: {result.get('tokens_used', 0)}, "
                       f"Cost: ${cost:.6f}, Model: {result.get('model_used', 'unknown')}")

            return result

        result = asyncio.run(run_test())
        self.assertTrue(result)

    @skipIf(not OPENAI_KEY_AVAILABLE, "OpenAI API key not available")
    def test_real_job_embedding_cache(self):
        """Test real job description embedding with caching"""

        async def run_test():
            result = await self.embedding_service.generate_and_cache_job_embedding(
                job_description=MINIMAL_JOB_DESC,
                company_name="TestCorp",
                role_title="Dev",
                user_id=self.user.id
            )

            # Verify basic structure
            self.assertIsInstance(result, dict)
            self.assertTrue(result.get('success', False), f"Job embedding failed: {result}")

            # Check job hash for caching
            job_hash = result.get('job_hash', '')
            self.assertTrue(job_hash, "No job hash generated")
            self.assertEqual(len(job_hash), 64, "Invalid SHA256 hash length")  # SHA256 = 64 chars

            # Verify embedding
            embedding_data = result.get('embedding_data', {})
            self.assertIsInstance(embedding_data, dict)
            self.assertIn('embedding', embedding_data)

            # Test caching - call again and should be cached
            cached_result = await self.embedding_service.generate_and_cache_job_embedding(
                job_description=MINIMAL_JOB_DESC,
                company_name="TestCorp",
                role_title="Dev",
                user_id=self.user.id
            )

            # Should get same hash and cached result
            self.assertEqual(cached_result.get('job_hash'), job_hash)
            self.assertTrue(cached_result.get('cache_hit', False), "Caching not working")

            logger.info(f"Job embedding cache test - Hash: {job_hash[:8]}..., "
                       f"Cached: {cached_result.get('cache_hit', False)}")

            return result

        result = asyncio.run(run_test())
        self.assertTrue(result)


class RealDocumentProcessorTestCase(TestCase):
    """Test real document processing with LangChain"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.processor = AdvancedDocumentProcessor()

    def test_real_text_processing(self):
        """Test real text processing and chunking"""

        async def run_test():
            # Use minimal text content to avoid token usage
            test_content = """Python Developer Resume

            Skills: Python, Django, REST APIs
            Experience: 3 years backend development
            Projects: Built e-commerce API, payment system"""

            result = await self.processor.process_document(
                content=test_content,
                content_type='text',
                metadata={'title': 'Test Resume'},
                user_id=self.user.id
            )

            # Verify basic structure
            self.assertIsInstance(result, dict)
            self.assertTrue(result.get('success', False), f"Processing failed: {result}")

            # Check chunks
            chunks = result.get('chunks', [])
            self.assertIsInstance(chunks, list)
            self.assertGreater(len(chunks), 0, "No chunks generated")

            # Verify chunk structure
            first_chunk = chunks[0]
            self.assertIn('content', first_chunk)
            self.assertIn('metadata', first_chunk)
            self.assertTrue(len(first_chunk['content']) > 0, "Empty chunk content")

            # Check processing metadata
            processing_metadata = result.get('processing_metadata', {})
            self.assertIn('total_chunks', processing_metadata)
            self.assertEqual(processing_metadata['total_chunks'], len(chunks))

            logger.info(f"Text processing test - Chunks: {len(chunks)}, "
                       f"Total chars: {sum(len(c['content']) for c in chunks)}")

            return result

        result = asyncio.run(run_test())
        self.assertTrue(result)


class APIBudgetSafetyTestCase(TestCase):
    """Safety tests to ensure we don't accidentally use too many tokens"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @skipIf(not OPENAI_KEY_AVAILABLE, "OpenAI API key not available")
    def test_token_usage_limits(self):
        """Test that our minimal test cases stay within safe token limits"""

        async def run_test():
            llm_service = EnhancedLLMService()

            # Test job parsing with strict token limits
            result = await llm_service.parse_job_description(
                job_description="Python dev",  # Extremely minimal
                company_name="Co",
                role_title="Dev",
                user_id=self.user.id
            )

            self.assertNotIn('error', result)

            # Strict token limit check
            metadata = result.get('processing_metadata', {})
            tokens_used = metadata.get('tokens_used', 0)
            cost_usd = metadata.get('cost_usd', 0)

            # Safety thresholds
            MAX_TOKENS = 500  # Very conservative limit
            MAX_COST_USD = 0.01  # 1 cent maximum

            self.assertLessEqual(tokens_used, MAX_TOKENS,
                               f"Token usage {tokens_used} exceeds safety limit {MAX_TOKENS}")
            self.assertLessEqual(cost_usd, MAX_COST_USD,
                               f"Cost ${cost_usd:.6f} exceeds safety limit ${MAX_COST_USD}")

            logger.warning(f"SAFETY CHECK - Tokens: {tokens_used}/{MAX_TOKENS}, "
                          f"Cost: ${cost_usd:.6f}/${MAX_COST_USD}")

            return result

        result = asyncio.run(run_test())
        self.assertTrue(result)

    def test_input_size_validation(self):
        """Validate that our test inputs are appropriately sized"""

        # Check our test data sizes
        job_desc_tokens = len(MINIMAL_JOB_DESC.split())
        artifact_desc_tokens = sum(len(a.get('description', '').split()) for a in MINIMAL_ARTIFACTS)

        # Conservative token estimates (1 word ≈ 1.3 tokens)
        estimated_job_tokens = job_desc_tokens * 1.3
        estimated_artifact_tokens = artifact_desc_tokens * 1.3

        # Safety limits
        MAX_JOB_TOKENS = 20  # Very small job descriptions
        MAX_ARTIFACT_TOKENS = 50  # Small artifact descriptions

        self.assertLessEqual(estimated_job_tokens, MAX_JOB_TOKENS,
                           f"Job description too large: ~{estimated_job_tokens} tokens")
        self.assertLessEqual(estimated_artifact_tokens, MAX_ARTIFACT_TOKENS,
                           f"Artifact descriptions too large: ~{estimated_artifact_tokens} tokens")

        logger.info(f"Input size validation - Job: ~{estimated_job_tokens} tokens, "
                   f"Artifacts: ~{estimated_artifact_tokens} tokens")


# Test configuration for different environments
class RealAPITestSuite:
    """Test suite configuration for real API testing"""
    # Configuration values for real API testing
    TEST_SETTINGS = {
        'MODEL_SELECTION_STRATEGY': 'cost_optimized',
        'MODEL_BUDGETS': {
            'test_tier': {'daily_limit_usd': 0.50}  # 50 cents max for all tests
        },
        'LOGGING': {
            'version': 1,
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                },
            },
            'loggers': {
                'llm_services': {
                    'handlers': ['console'],
                    'level': 'INFO',
                },
            },
        }
    }


if __name__ == '__main__':
    # Run with: python manage.py test llm_services.tests.test_real_llm_integration
    import django
    from django.conf import settings
    from django.test.utils import get_runner

    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_tailor.settings')
        django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["llm_services.tests.test_real_llm_integration"])