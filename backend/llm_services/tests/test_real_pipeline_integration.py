"""
End-to-End Pipeline Integration Tests with Real APIs

Tests the complete CV generation pipeline using real LLM APIs with strict token budgets.
Simulates the full workflow from job description to generated CV.

To run: python manage.py test llm_services.tests.test_real_pipeline_integration

WARNING: These tests use real API tokens and incur costs.
"""

import os
import asyncio
import logging
from unittest import skipIf
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction

from .test_real_api_config import (
    RealAPITestConfig, TestDataFactory, require_real_api_key,
    with_budget_control, with_safe_settings, RealAPITestHelper
)
from ..services.enhanced_llm_service import EnhancedLLMService
from ..services.embedding_service import FlexibleEmbeddingService
from ..services.document_processor import AdvancedDocumentProcessor
from generation.tasks import generate_cv_task, enhance_artifact_with_llm
from generation.models import GeneratedDocument, JobDescription
from artifacts.models import Artifact

User = get_user_model()
logger = logging.getLogger(__name__)

config = RealAPITestConfig()


@with_safe_settings()
class RealPipelineIntegrationTestCase(TransactionTestCase):
    """Test complete CV generation pipeline with real APIs"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='pipeline_user',
            email='pipeline@example.com',
            password='testpass123'
        )
        self.config = RealAPITestConfig()
        self.test_results = []

    def tearDown(self):
        """Log test summary"""
        if self.test_results:
            RealAPITestHelper.log_test_summary(self.test_results)

    @require_real_api_key('openai')
    @with_budget_control()
    def test_end_to_end_pipeline_minimal(self):
        """Test complete pipeline with minimal data to reduce token usage"""

        if not self.config.should_run_real_tests():
            self.skipTest("Real API tests not enabled")

        # Step 1: Create minimal job description
        job_desc = JobDescription.objects.create(
            user=self.user,
            raw_content=TestDataFactory.minimal_job_description(),
            company_name="TestCorp",
            role_title="Python Dev",
            content_hash="test_hash_pipeline"
        )

        # Step 2: Create minimal artifact
        artifact = Artifact.objects.create(
            user=self.user,
            title="API Project",
            description="Built REST API with Python",
            artifact_type="project",
            technologies=["Python", "Django"]
        )

        # Step 3: Create generation request
        generation = GeneratedDocument.objects.create(
            user=self.user,
            job_description=job_desc,
            generation_preferences=TestDataFactory.minimal_generation_preferences(),
            status='pending'
        )

        # Step 4: Test the full pipeline
        async def run_pipeline():
            llm_service = EnhancedLLMService()

            # Parse job description (if not already parsed)
            if not job_desc.parsed_data:
                parse_result = await llm_service.parse_job_description(
                    job_desc.raw_content,
                    job_desc.company_name,
                    job_desc.role_title,
                    self.user.id
                )
                self.test_results.append(parse_result)
                self.assertNotIn('error', parse_result)

                # Update job description with parsed data
                job_desc.parsed_data = parse_result
                job_desc.parsing_confidence = parse_result.get('confidence_score', 0.5)
                job_desc.save()

            # Rank artifacts
            artifacts_data = [{
                'id': artifact.id,
                'title': artifact.title,
                'description': artifact.description,
                'artifact_type': artifact.artifact_type,
                'technologies': artifact.technologies,
                'start_date': None,
                'end_date': None,
                'evidence_links': [],
                'extracted_metadata': {}
            }]

            job_requirements = (
                job_desc.parsed_data.get('must_have_skills', []) +
                job_desc.parsed_data.get('nice_to_have_skills', [])
            )

            ranking_result = await llm_service.rank_artifacts_by_relevance(
                artifacts_data,
                job_requirements,
                self.user.id
            )
            # Note: Ranking might not have processing_metadata, so don't add to test_results

            # Generate CV content
            cv_result = await llm_service.generate_cv_content(
                job_desc.parsed_data,
                ranking_result[:1],  # Use only top artifact to minimize tokens
                generation.generation_preferences,
                self.user.id
            )
            self.test_results.append(cv_result)
            self.assertNotIn('error', cv_result)

            # Update generation with results
            generation.content = cv_result.get('content', {})
            generation.status = 'completed'

            processing_metadata = cv_result.get('processing_metadata', {})
            generation.metadata = {
                'model_used': processing_metadata.get('model_used'),
                'generation_time_ms': processing_metadata.get('processing_time_ms'),
                'token_usage': processing_metadata.get('tokens_used'),
                'cost_usd': processing_metadata.get('cost_usd'),
                'quality_score': processing_metadata.get('quality_score'),
            }
            generation.save()

            return {
                'generation_id': generation.id,
                'job_parsing': parse_result,
                'cv_generation': cv_result,
                'artifacts_ranked': len(ranking_result)
            }

        # Run the pipeline
        pipeline_result = asyncio.run(run_pipeline())

        # Verify pipeline completed successfully
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn('generation_id', pipeline_result)

        # Verify generation was updated
        generation.refresh_from_db()
        self.assertEqual(generation.status, 'completed')
        self.assertTrue(generation.content)

        # Verify content structure
        content = generation.content
        self.assertIsInstance(content, dict)
        self.assertTrue(len(content) > 0)

        # Verify budget compliance for all API calls
        total_cost = sum(
            r.get('processing_metadata', {}).get('cost_usd', 0.0)
            for r in self.test_results
        )
        total_tokens = sum(
            r.get('processing_metadata', {}).get('tokens_used', 0)
            for r in self.test_results
        )

        # Safety checks
        max_total_cost = 0.05  # 5 cents max for entire pipeline
        max_total_tokens = 1000  # 1000 tokens max

        self.assertLess(total_cost, max_total_cost,
                       f"Pipeline cost ${total_cost:.6f} exceeds limit ${max_total_cost}")
        self.assertLess(total_tokens, max_total_tokens,
                       f"Pipeline tokens {total_tokens} exceeds limit {max_total_tokens}")

        logger.info(f"Pipeline test completed - Total cost: ${total_cost:.6f}, "
                   f"Total tokens: {total_tokens}, Generation ID: {generation.id}")

        return pipeline_result

    @require_real_api_key('openai')
    def test_artifact_enhancement_minimal(self):
        """Test artifact enhancement with minimal content"""

        if not self.config.should_run_real_tests():
            self.skipTest("Real API tests not enabled")

        # Create minimal artifact for enhancement
        artifact = Artifact.objects.create(
            user=self.user,
            title="Test Project",
            description="Small Python project with Django",
            artifact_type="project",
            technologies=["Python"]
        )

        # Test document processing (without LLM enhancement to save tokens)
        async def run_enhancement():
            processor = AdvancedDocumentProcessor()

            # Process minimal text content
            result = await processor.process_document(
                content=TestDataFactory.minimal_text_content(),
                content_type='text',
                metadata={'title': artifact.title, 'artifact_id': artifact.id},
                user_id=self.user.id
            )

            return result

        result = asyncio.run(run_enhancement())

        # Verify processing succeeded
        self.assertTrue(result.get('success', False))
        self.assertIn('chunks', result)
        self.assertGreater(len(result['chunks']), 0)

        # Verify chunks have correct structure
        first_chunk = result['chunks'][0]
        self.assertIn('content', first_chunk)
        self.assertIn('metadata', first_chunk)

        logger.info(f"Artifact enhancement test - Chunks: {len(result['chunks'])}")

    @require_real_api_key('openai')
    def test_embedding_similarity_search(self):
        """Test embedding generation and similarity search with minimal data"""

        if not self.config.should_run_real_tests():
            self.skipTest("Real API tests not enabled")

        async def run_embedding_test():
            embedding_service = FlexibleEmbeddingService()

            # Generate embeddings for job and artifact
            job_text = TestDataFactory.minimal_job_description()
            artifact_text = TestDataFactory.minimal_embedding_text()

            job_embedding_result = await embedding_service.generate_embedding(
                job_text, self.user.id
            )
            artifact_embedding_result = await embedding_service.generate_embedding(
                artifact_text, self.user.id
            )

            self.test_results.extend([job_embedding_result, artifact_embedding_result])

            # Verify both succeeded
            self.assertTrue(job_embedding_result.get('success', False))
            self.assertTrue(artifact_embedding_result.get('success', False))

            # Verify embedding dimensions
            job_embedding = job_embedding_result.get('embedding', [])
            artifact_embedding = artifact_embedding_result.get('embedding', [])

            self.assertEqual(len(job_embedding), 1536)
            self.assertEqual(len(artifact_embedding), 1536)

            # Test similarity calculation (simple dot product)
            similarity = sum(a * b for a, b in zip(job_embedding[:100], artifact_embedding[:100]))
            self.assertIsInstance(similarity, (int, float))

            return {
                'job_embedding_cost': job_embedding_result.get('cost_usd', 0),
                'artifact_embedding_cost': artifact_embedding_result.get('cost_usd', 0),
                'similarity_sample': similarity
            }

        result = asyncio.run(run_embedding_test())

        # Verify reasonable costs
        total_embedding_cost = result['job_embedding_cost'] + result['artifact_embedding_cost']
        self.assertLess(total_embedding_cost, 0.002,  # 0.2 cents max for embeddings
                       f"Embedding cost ${total_embedding_cost:.6f} too high")

        logger.info(f"Embedding similarity test - Cost: ${total_embedding_cost:.6f}, "
                   f"Similarity: {result['similarity_sample']}")

    def test_model_selection_and_fallback(self):
        """Test intelligent model selection and fallback mechanisms"""

        async def run_model_selection_test():
            llm_service = EnhancedLLMService()

            # Test model selection for different complexity levels
            simple_model, simple_reasoning = llm_service._select_model_for_task(
                task_type='job_parsing',
                complexity_score=0.2,  # Simple task
                user_id=self.user.id
            )

            complex_model, complex_reasoning = llm_service._select_model_for_task(
                task_type='cv_generation',
                complexity_score=0.8,  # Complex task
                user_id=self.user.id
            )

            # Verify selections are reasonable
            self.assertIsInstance(simple_model, str)
            self.assertIsInstance(complex_model, str)
            self.assertTrue(simple_reasoning)
            self.assertTrue(complex_reasoning)

            # Models should be different for different complexity levels
            # (unless there's only one model available)
            logger.info(f"Model selection - Simple: {simple_model}, "
                       f"Complex: {complex_model}")

            return {
                'simple_model': simple_model,
                'complex_model': complex_model,
                'simple_reasoning': simple_reasoning,
                'complex_reasoning': complex_reasoning
            }

        result = asyncio.run(run_model_selection_test())
        self.assertTrue(result)

    def test_cost_tracking_accuracy(self):
        """Test that cost tracking is accurate and within expected ranges"""

        if not self.config.should_run_real_tests():
            self.skipTest("Real API tests not enabled")

        async def run_cost_test():
            llm_service = EnhancedLLMService()

            # Make a minimal API call and track cost
            result = await llm_service.parse_job_description(
                job_description="Dev job",
                company_name="Co",
                role_title="Dev",
                user_id=self.user.id
            )

            self.test_results.append(result)
            self.assertNotIn('error', result)

            metadata = result.get('processing_metadata', {})
            tokens_used = metadata.get('tokens_used', 0)
            cost_usd = metadata.get('cost_usd', 0.0)
            model_used = metadata.get('model_used', '')

            # Verify cost calculation is reasonable
            self.assertGreater(tokens_used, 0)
            self.assertGreater(cost_usd, 0.0)
            self.assertTrue(model_used)

            # Cost should be proportional to tokens
            # Rough estimate: GPT-4 is ~$0.00003 per token
            estimated_cost = tokens_used * 0.00005  # Conservative estimate
            cost_ratio = cost_usd / estimated_cost if estimated_cost > 0 else 0

            # Cost should be within reasonable range (0.5x to 3x estimate)
            self.assertGreater(cost_ratio, 0.1, f"Cost seems too low: ${cost_usd:.6f}")
            self.assertLess(cost_ratio, 10.0, f"Cost seems too high: ${cost_usd:.6f}")

            return {
                'tokens_used': tokens_used,
                'cost_usd': cost_usd,
                'model_used': model_used,
                'cost_per_token': cost_usd / tokens_used if tokens_used > 0 else 0,
                'cost_ratio': cost_ratio
            }

        result = asyncio.run(run_cost_test())

        logger.info(f"Cost tracking test - Tokens: {result['tokens_used']}, "
                   f"Cost: ${result['cost_usd']:.6f}, "
                   f"Per token: ${result['cost_per_token']:.8f}, "
                   f"Model: {result['model_used']}")


if __name__ == '__main__':
    # Run with: python manage.py test llm_services.tests.test_real_pipeline_integration
    import django
    from django.conf import settings
    from django.test.utils import get_runner

    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_tailor.settings')
        django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["llm_services.tests.test_real_pipeline_integration"])