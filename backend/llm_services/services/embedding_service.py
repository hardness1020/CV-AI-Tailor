"""
Flexible Embedding Service with pgvector integration.
Implements ft-llm-002-embedding-storage.md
"""

import hashlib
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from asgiref.sync import sync_to_async

# LiteLLM for unified embeddings API
try:
    from litellm import embedding as litellm_embedding
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False
    import openai
    from openai import OpenAI

from .model_registry import ModelRegistry
from .model_selector import IntelligentModelSelector
from .performance_tracker import ModelPerformanceTracker
from ..models import EnhancedArtifact, ArtifactChunk, JobDescriptionEmbedding

logger = logging.getLogger(__name__)


class FlexibleEmbeddingService:
    """Service for generating and managing embeddings with intelligent model selection"""

    def __init__(self):
        self.registry = ModelRegistry()
        self.model_selector = IntelligentModelSelector()
        self.performance_tracker = ModelPerformanceTracker()

        # Initialize OpenAI client for direct API calls if needed
        self.openai_client = None
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY and not HAS_LITELLM:
            self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_embeddings(self, texts: List[str],
                                use_case: str = 'similarity',
                                user_id: Optional[int] = None,
                                batch_size: int = 100) -> List[Dict[str, Any]]:
        """Generate embeddings with intelligent model selection and batch processing"""

        if not texts:
            return []

        context = {
            'use_case': use_case,
            'text_count': len(texts),
            'avg_text_length': sum(len(text) for text in texts) / len(texts),
            'text_complexity': self._assess_text_complexity(texts)
        }

        # Select optimal embedding model
        selected_model = self.model_selector.select_model_for_task('embedding', context)
        model_config = self.registry.get_model_config(selected_model, 'embedding_models')

        if not model_config:
            raise ValueError(f"Unknown embedding model: {selected_model}")

        results = []
        total_cost = 0.0
        total_tokens = 0
        start_time = time.time()

        try:
            # Process in batches to handle rate limits and optimize performance
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_start_time = time.time()

                if HAS_LITELLM:
                    response = await litellm_embedding(
                        model=selected_model,
                        input=batch,
                        dimensions=model_config.get('dimensions', 1536),
                        api_key=settings.OPENAI_API_KEY
                    )
                else:
                    # Direct OpenAI API call
                    response = self.openai_client.embeddings.create(
                        model=selected_model,
                        input=batch,
                        dimensions=model_config.get('dimensions', 1536)
                    )

                batch_processing_time = int((time.time() - batch_start_time) * 1000)
                batch_tokens = response.usage.total_tokens if hasattr(response, 'usage') else len(' '.join(batch).split())
                batch_cost = self.registry.calculate_cost(selected_model, batch_tokens, model_type='embedding_models')

                total_tokens += batch_tokens
                total_cost += batch_cost

                # Process batch results
                for j, embedding_data in enumerate(response.data):
                    original_index = i + j
                    results.append({
                        'text': texts[original_index] if original_index < len(texts) else "",
                        'embedding': embedding_data.embedding,
                        'model_used': selected_model,
                        'dimensions': len(embedding_data.embedding),
                        'text_index': original_index,
                        'batch_processing_time_ms': batch_processing_time,
                        'tokens_used': batch_tokens // len(batch),  # Approximate per text
                        'cost_usd': batch_cost / len(batch)  # Distribute cost across batch
                    })

            total_processing_time = int((time.time() - start_time) * 1000)

            # Track performance
            await self.performance_tracker.record_task(
                model=selected_model,
                task_type='embedding',
                processing_time_ms=total_processing_time,
                tokens_used=total_tokens,
                cost_usd=total_cost,
                success=True,
                quality_score=0.9,  # Embeddings don't have explicit quality scores
                user_id=user_id,
                metadata={
                    'texts_processed': len(texts),
                    'batches_processed': (len(texts) + batch_size - 1) // batch_size,
                    'use_case': use_case,
                    'avg_text_length': context['avg_text_length'],
                    'model_dimensions': model_config.get('dimensions', 1536)
                }
            )

            logger.info(f"Generated {len(results)} embeddings using {selected_model} in {total_processing_time}ms")
            return results

        except Exception as e:
            logger.error(f"Embedding generation failed with {selected_model}: {e}")

            # Track failure
            processing_time = int((time.time() - start_time) * 1000)
            await self.performance_tracker.record_task(
                model=selected_model,
                task_type='embedding',
                processing_time_ms=processing_time,
                tokens_used=0,
                cost_usd=0.0,
                success=False,
                user_id=user_id
            )

            raise

    async def store_artifact_embeddings(self, artifact_id: str,
                                      content: str,
                                      chunks: List[Dict[str, Any]] = None,
                                      user_id: Optional[int] = None) -> Dict[str, Any]:
        """Store embeddings for an artifact and its chunks"""

        try:
            # Generate main content embedding
            main_embedding_result = await self.generate_embeddings(
                [content],
                use_case='artifact_storage',
                user_id=user_id
            )

            if not main_embedding_result:
                raise ValueError("Failed to generate main content embedding")

            main_result = main_embedding_result[0]

            # Store artifact embeddings using sync helper
            artifact_result = await sync_to_async(self._store_artifact_embeddings_sync)(
                artifact_id, main_result, chunks, user_id, content
            )
            enhanced_artifact = artifact_result['enhanced_artifact']
            created = artifact_result['created']

            chunk_results = []
            total_chunk_cost = 0.0

            # Process chunks if provided
            if chunks:
                chunk_texts = [chunk['content'] for chunk in chunks]
                chunk_embeddings = await self.generate_embeddings(
                    chunk_texts,
                    use_case='chunk_storage',
                    user_id=user_id
                )

                # Store chunk embeddings using sync_to_async
                for i, (chunk, embedding_result) in enumerate(zip(chunks, chunk_embeddings)):
                    content_hash = hashlib.sha256(chunk['content'].encode()).hexdigest()

                    chunk_obj, chunk_created = await sync_to_async(ArtifactChunk.objects.get_or_create)(
                        artifact=enhanced_artifact,
                        chunk_index=i,
                        defaults={
                            'content': chunk['content'],
                            'metadata': chunk.get('metadata', {}),
                            'embedding_vector': embedding_result['embedding'],
                            'content_hash': content_hash,
                            'model_used': embedding_result['model_used'],
                            'tokens_used': embedding_result['tokens_used'],
                            'processing_cost_usd': embedding_result['cost_usd']
                        }
                    )

                    if not chunk_created:
                        # Update existing chunk
                        chunk_obj.embedding_vector = embedding_result['embedding']
                        chunk_obj.model_used = embedding_result['model_used']
                        chunk_obj.tokens_used = embedding_result['tokens_used']
                        chunk_obj.processing_cost_usd = embedding_result['cost_usd']
                        await sync_to_async(chunk_obj.save)()

                    chunk_results.append({
                        'chunk_index': i,
                        'chunk_id': str(chunk_obj.id),
                        'embedding_dimensions': len(embedding_result['embedding']),
                        'cost_usd': embedding_result['cost_usd']
                    })

                    total_chunk_cost += embedding_result['cost_usd']

                # Update artifact with chunk info using sync_to_async
                enhanced_artifact.total_chunks = len(chunks) if chunks else 0
                enhanced_artifact.embedding_cost_usd += total_chunk_cost
                await sync_to_async(enhanced_artifact.save)()

                return {
                    'success': True,
                    'artifact_id': str(artifact_id),
                    'main_embedding': {
                        'model_used': main_result['model_used'],
                        'dimensions': main_result['dimensions'],
                        'cost_usd': main_result['cost_usd']
                    },
                    'chunks_processed': len(chunk_results),
                    'chunk_embeddings': chunk_results,
                    'total_cost_usd': main_result['cost_usd'] + total_chunk_cost,
                    'created_new_artifact': created
                }

        except Exception as e:
            logger.error(f"Failed to store artifact embeddings for {artifact_id}: {e}")
            raise

    def _store_artifact_embeddings_sync(self, artifact_id: str, main_result: Dict[str, Any],
                                       chunks: List[Dict[str, Any]] = None,
                                       user_id: Optional[int] = None,
                                       content: str = "") -> Dict[str, Any]:
        """Synchronous database operations for store_artifact_embeddings"""

        with transaction.atomic():
            # Update or create enhanced artifact
            enhanced_artifact, created = EnhancedArtifact.objects.get_or_create(
                id=artifact_id,
                defaults={
                    'user_id': user_id,
                    'raw_content': content,
                    'content_embedding': main_result['embedding'],
                    'summary_embedding': [0.0] * 1536,  # Default vector for pgvector field
                    'embedding_model': main_result['model_used'],
                    'embedding_dimensions': main_result['dimensions'],
                    'embedding_cost_usd': main_result['cost_usd'],
                    'last_embedding_update': timezone.now()
                }
            )

            if not created:
                # Update existing artifact
                enhanced_artifact.content_embedding = main_result['embedding']
                enhanced_artifact.embedding_model = main_result['model_used']
                enhanced_artifact.embedding_dimensions = main_result['dimensions']
                enhanced_artifact.embedding_cost_usd += main_result['cost_usd']
                enhanced_artifact.last_embedding_update = timezone.now()
                enhanced_artifact.save()

            return {
                'enhanced_artifact': enhanced_artifact,
                'created': created
            }

    async def generate_and_cache_job_embedding(self, job_description: str,
                                             company_name: str = "",
                                             role_title: str = "",
                                             user_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate and cache job description embedding"""

        # Create hash for caching
        job_text = f"{company_name} {role_title} {job_description}".strip()
        job_hash = hashlib.sha256(job_text.encode()).hexdigest()

        try:
            # Check if embedding already exists
            cached_embedding = await sync_to_async(JobDescriptionEmbedding.objects.filter(
                job_description_hash=job_hash
            ).first)()

            if cached_embedding:
                await sync_to_async(cached_embedding.update_access)()
                logger.info(f"Using cached job embedding (hash: {job_hash[:8]}...)")

                return {
                    'embedding': cached_embedding.embedding_vector,
                    'model_used': cached_embedding.model_used,
                    'dimensions': cached_embedding.dimensions,
                    'cost_usd': 0.0,  # No cost for cached embedding
                    'cached': True,
                    'job_hash': job_hash
                }

            # Generate new embedding
            embedding_results = await self.generate_embeddings(
                [job_text],
                use_case='job_matching',
                user_id=user_id
            )

            if not embedding_results:
                raise ValueError("Failed to generate job embedding")

            result = embedding_results[0]

            # Cache the embedding
            await sync_to_async(self._cache_job_embedding)(
                user_id, job_hash, company_name, role_title, result
            )

            logger.info(f"Generated and cached job embedding (hash: {job_hash[:8]}...)")

            return {
                'embedding': result['embedding'],
                'model_used': result['model_used'],
                'dimensions': result['dimensions'],
                'cost_usd': result['cost_usd'],
                'cached': False,
                'job_hash': job_hash
            }

        except Exception as e:
            logger.error(f"Failed to generate job embedding: {e}")
            raise

    def _cache_job_embedding(self, user_id: int, job_hash: str, company_name: str, role_title: str, result: Dict[str, Any]):
        """Synchronous method to cache job embedding in database"""
        try:
            with transaction.atomic():
                JobDescriptionEmbedding.objects.create(
                    user_id=user_id,
                    job_description_hash=job_hash,
                    company_name=company_name,
                    role_title=role_title,
                    embedding_vector=result['embedding'],
                    model_used=result['model_used'],
                    dimensions=result['dimensions'],
                    tokens_used=result['tokens_used'],
                    cost_usd=result['cost_usd']
                )
        except Exception as e:
            if "foreign key constraint" in str(e).lower():
                # Skip caching if user doesn't exist (common in tests)
                logger.debug(f"Skipping job embedding cache for non-existent user {user_id}")
            else:
                raise e

    def find_similar_artifacts(self, query_embedding: List[float],
                             user_id: int,
                             limit: int = 10,
                             similarity_threshold: float = 0.7,
                             content_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Find similar artifacts using vector similarity search"""

        try:
            from django.db import connection

            # Build query conditions
            where_conditions = ["ea.user_id = %s"]
            params = [user_id]

            if content_types:
                where_conditions.append("ea.content_type = ANY(%s)")
                params.append(content_types)

            # Add similarity threshold
            where_conditions.append("ea.content_embedding <=> %s::vector < %s")
            params.extend([query_embedding, 1 - similarity_threshold])

            where_clause = " AND ".join(where_conditions)
            params.append(query_embedding)  # For ORDER BY
            params.append(limit)

            with connection.cursor() as cursor:
                start_time = time.time()

                query = f"""
                    SELECT
                        ea.id,
                        ea.title,
                        ea.content_type,
                        ea.content_embedding <=> %s::vector as similarity_distance,
                        1 - (ea.content_embedding <=> %s::vector) as similarity_score,
                        ea.embedding_model,
                        ea.created_at
                    FROM enhanced_artifacts ea
                    WHERE {where_clause}
                    ORDER BY ea.content_embedding <=> %s::vector
                    LIMIT %s
                """

                # Add query_embedding twice more for the SELECT clause
                all_params = [query_embedding, query_embedding] + params

                cursor.execute(query, all_params)
                query_time_ms = int((time.time() - start_time) * 1000)

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'artifact_id': str(row[0]),
                        'title': row[1],
                        'content_type': row[2],
                        'similarity_distance': float(row[3]),
                        'similarity_score': float(row[4]),
                        'embedding_model': row[5],
                        'created_at': row[6].isoformat()
                    })

                logger.info(f"Similarity search completed in {query_time_ms}ms, found {len(results)} results")

                return results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    def rank_artifacts_by_job_relevance(self, job_embedding: List[float],
                                       artifact_ids: List[str],
                                       user_id: int) -> List[Dict[str, Any]]:
        """Rank specific artifacts by relevance to job description"""

        try:
            from django.db import connection

            with connection.cursor() as cursor:
                start_time = time.time()

                query = """
                    SELECT
                        ea.id,
                        ea.title,
                        ea.content_type,
                        ea.content_embedding <=> %s::vector as relevance_distance,
                        1 - (ea.content_embedding <=> %s::vector) as relevance_score,
                        ea.embedding_model
                    FROM enhanced_artifacts ea
                    WHERE ea.user_id = %s AND ea.id = ANY(%s)
                    ORDER BY ea.content_embedding <=> %s::vector
                """

                params = [
                    job_embedding,  # For similarity calculation
                    job_embedding,  # For score calculation
                    user_id,
                    artifact_ids,
                    job_embedding   # For ordering
                ]

                cursor.execute(query, params)
                query_time_ms = int((time.time() - start_time) * 1000)

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'artifact_id': str(row[0]),
                        'title': row[1],
                        'content_type': row[2],
                        'relevance_distance': float(row[3]),
                        'relevance_score': float(row[4]),
                        'embedding_model': row[5],
                        'explanation': self._generate_relevance_explanation(float(row[4]))
                    })

                logger.info(f"Artifact ranking completed in {query_time_ms}ms for {len(results)} artifacts")
                return results

        except Exception as e:
            logger.error(f"Artifact ranking failed: {e}")
            return []

    def _assess_text_complexity(self, texts: List[str]) -> str:
        """Assess the complexity of text content for model selection"""
        if not texts:
            return 'standard'

        avg_length = sum(len(text) for text in texts) / len(texts)
        total_text = ' '.join(texts)

        # Technical indicators
        technical_keywords = ['API', 'algorithm', 'database', 'framework', 'architecture', 'implementation']
        technical_count = sum(1 for keyword in technical_keywords if keyword.lower() in total_text.lower())

        # Complexity scoring
        complexity_score = 0

        if avg_length > 1000:
            complexity_score += 2
        elif avg_length > 500:
            complexity_score += 1

        complexity_score += min(2, technical_count)

        if complexity_score >= 3:
            return 'high'
        elif complexity_score >= 1:
            return 'medium'
        else:
            return 'standard'

    def _generate_relevance_explanation(self, similarity_score: float) -> str:
        """Generate human-readable explanation of similarity score"""
        if similarity_score >= 0.9:
            return "Highly relevant with strong semantic alignment"
        elif similarity_score >= 0.8:
            return "Very relevant with good content overlap"
        elif similarity_score >= 0.7:
            return "Relevant with moderate alignment"
        elif similarity_score >= 0.6:
            return "Some relevance with partial overlap"
        else:
            return "Limited relevance"

    def cleanup_old_embeddings(self, days_to_keep: int = 90):
        """Clean up old cached job embeddings"""
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Only clean up job embeddings that haven't been accessed recently
        deleted_count = JobDescriptionEmbedding.objects.filter(
            last_accessed__lt=cutoff_date,
            access_count__lte=2  # Only delete rarely used embeddings
        ).delete()

        logger.info(f"Cleaned up {deleted_count[0]} old job embeddings")
        return deleted_count[0]

    def get_embedding_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings"""
        from django.db.models import Count, Avg, Sum

        artifact_stats = EnhancedArtifact.objects.aggregate(
            total_artifacts=Count('id'),
            avg_dimensions=Avg('embedding_dimensions'),
            total_embedding_cost=Sum('embedding_cost_usd')
        )

        chunk_stats = ArtifactChunk.objects.aggregate(
            total_chunks=Count('id'),
            total_chunk_cost=Sum('processing_cost_usd')
        )

        job_stats = JobDescriptionEmbedding.objects.aggregate(
            total_job_embeddings=Count('id'),
            avg_access_count=Avg('access_count'),
            total_job_cost=Sum('cost_usd')
        )

        # Model usage breakdown
        model_usage = {}
        for model_name in EnhancedArtifact.objects.values_list('embedding_model', flat=True).distinct():
            count = EnhancedArtifact.objects.filter(embedding_model=model_name).count()
            model_usage[model_name] = count

        return {
            'artifact_embeddings': {
                'total_count': artifact_stats['total_artifacts'] or 0,
                'avg_dimensions': round(artifact_stats['avg_dimensions'] or 0, 1),
                'total_cost_usd': round(artifact_stats['total_embedding_cost'] or 0, 6)
            },
            'chunk_embeddings': {
                'total_count': chunk_stats['total_chunks'] or 0,
                'total_cost_usd': round(chunk_stats['total_chunk_cost'] or 0, 6)
            },
            'job_embeddings': {
                'total_count': job_stats['total_job_embeddings'] or 0,
                'avg_access_count': round(job_stats['avg_access_count'] or 0, 1),
                'total_cost_usd': round(job_stats['total_job_cost'] or 0, 6)
            },
            'model_usage': model_usage,
            'total_embeddings': (artifact_stats['total_artifacts'] or 0) + (chunk_stats['total_chunks'] or 0),
            'total_cost_usd': round(
                (artifact_stats['total_embedding_cost'] or 0) +
                (chunk_stats['total_chunk_cost'] or 0) +
                (job_stats['total_job_cost'] or 0), 6
            )
        }