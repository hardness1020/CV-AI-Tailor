"""
Enhanced LLM Service with flexible model selection and latest AI models.
Implements ft-llm-003-flexible-model-selection.md
"""

import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async

# LiteLLM for unified API access
try:
    from litellm import completion, acompletion
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False
    # Fallback to direct API calls
    import openai
    from openai import OpenAI
    from openai import (
        APIConnectionError,
        APIStatusError,
        RateLimitError,
        AuthenticationError,
        PermissionDeniedError,
        BadRequestError,
        InternalServerError
    )
    import anthropic

from .model_registry import ModelRegistry
from .model_selector import IntelligentModelSelector
from .performance_tracker import ModelPerformanceTracker
from .circuit_breaker import CircuitBreakerManager
from ..models import ModelPerformanceMetric, CircuitBreakerState

logger = logging.getLogger(__name__)


class EnhancedLLMService:
    """
    Enhanced LLM service with intelligent model selection, performance tracking,
    and circuit breaker patterns.
    """

    def __init__(self):
        self.model_selector = IntelligentModelSelector()
        self.registry = ModelRegistry()
        self.performance_tracker = ModelPerformanceTracker()
        self.circuit_breaker = CircuitBreakerManager()

        # Initialize clients
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients"""
        self.openai_client = None
        self.anthropic_client = None

        # Initialize OpenAI
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            if not HAS_LITELLM:
                self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        # Initialize Anthropic
        if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
            if not HAS_LITELLM:
                self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def parse_job_description(self, job_description: str, company_name: str = "",
                                  role_title: str = "", user_id: Optional[int] = None) -> Dict[str, Any]:
        """Enhanced job description parsing with intelligent model selection"""

        context = {
            'job_description': job_description,
            'company_name': company_name,
            'role_title': role_title,
            'task_type': 'job_parsing'
        }

        # Select optimal model
        selected_model = self.model_selector.select_model_for_task('job_parsing', context)

        # Check circuit breaker
        if not await self.circuit_breaker.can_attempt_request(selected_model):
            fallback_model = self.model_selector.get_fallback_model(selected_model, 'job_parsing')
            if fallback_model:
                selected_model = fallback_model
            else:
                return {"error": "All models unavailable due to circuit breaker"}

        start_time = time.time()

        try:
            # Build parsing prompt
            prompt = self._build_parsing_prompt(job_description, company_name, role_title)

            # Make API call
            if HAS_LITELLM:
                response = await acompletion(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are a job description parser. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000,
                    api_key=self._get_api_key_for_model(selected_model)
                )
            else:
                response = await self._direct_api_call(selected_model, prompt, max_tokens=1000, temperature=0.1)

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Extract JSON content from response, handling markdown code blocks
            response_content = response.choices[0].message.content.strip()
            if response_content.startswith('```json'):
                # Remove markdown code block markers
                response_content = response_content[7:]  # Remove '```json'
                if response_content.endswith('```'):
                    response_content = response_content[:-3]  # Remove trailing '```'
            elif response_content.startswith('```'):
                # Remove generic code block markers
                response_content = response_content[3:]
                if response_content.endswith('```'):
                    response_content = response_content[:-3]

            result = json.loads(response_content.strip())

            # Calculate cost
            cost = self.registry.calculate_cost(
                selected_model,
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )

            # Record success
            await self.circuit_breaker.record_success(selected_model)

            # Track performance
            await self.performance_tracker.record_task(
                model=selected_model,
                task_type='job_parsing',
                processing_time_ms=processing_time_ms,
                tokens_used=response.usage.total_tokens,
                cost_usd=cost,
                success=True,
                quality_score=result.get('confidence_score', 0.8),
                user_id=user_id,
                complexity_score=self.model_selector._calculate_complexity_score(context)
            )

            return {
                **result,
                'processing_metadata': {
                    'model_used': selected_model,
                    'processing_time_ms': processing_time_ms,
                    'tokens_used': response.usage.total_tokens,
                    'cost_usd': float(cost),
                    'selection_reason': self.model_selector.get_selection_reason(selected_model, context),
                    'fallback_used': False,
                    'quality_score': result.get('confidence_score', 0.8)
                }
            }

        except json.JSONDecodeError as e:
            response_content = getattr(response.choices[0].message, 'content', 'No content') if 'response' in locals() else 'No response'
            logger.error(f"Failed to parse LLM response as JSON: {e}. Response content: {response_content[:200]}")
            return {"error": "Failed to parse job description - invalid JSON response"}

        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded for {selected_model} during job parsing: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='job_parsing', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )

            # Rate limits should trigger fallback more aggressively
            if self.model_selector.should_use_fallback(selected_model, {'error_type': 'rate_limit'}):
                fallback_model = self.model_selector.get_fallback_model(selected_model, 'job_parsing')
                if fallback_model and fallback_model != selected_model:
                    logger.info(f"Rate limit fallback to {fallback_model}")
                    context['fallback_attempt'] = True
                    return await self._retry_with_fallback(fallback_model, context, 'job_parsing', user_id)

            return {"error": "Rate limit exceeded. Please try again later."}

        except AuthenticationError as e:
            logger.error(f"Authentication error for {selected_model}: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='job_parsing', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )
            return {"error": "Authentication failed. Please check API credentials."}

        except PermissionDeniedError as e:
            logger.error(f"Permission denied for {selected_model}: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='job_parsing', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )
            return {"error": "Access denied to the requested model."}

        except APIConnectionError as e:
            logger.error(f"Connection error for {selected_model}: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='job_parsing', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )

            # Connection errors should definitely trigger fallback
            if self.model_selector.should_use_fallback(selected_model, {'error_type': 'connection'}):
                fallback_model = self.model_selector.get_fallback_model(selected_model, 'job_parsing')
                if fallback_model and fallback_model != selected_model:
                    logger.info(f"Connection error fallback to {fallback_model}")
                    context['fallback_attempt'] = True
                    return await self._retry_with_fallback(fallback_model, context, 'job_parsing', user_id)

            return {"error": "Connection error. Please check your internet connection."}

        except BadRequestError as e:
            logger.error(f"Bad request for {selected_model}: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            # Don't record circuit breaker failure for bad requests - it's our fault, not the API's
            await self.performance_tracker.record_task(
                model=selected_model, task_type='job_parsing', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )
            return {"error": f"Invalid request: {str(e)}"}

        except InternalServerError as e:
            logger.error(f"Internal server error for {selected_model}: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='job_parsing', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )

            # Server errors should trigger fallback
            if self.model_selector.should_use_fallback(selected_model, {'error_type': 'server_error'}):
                fallback_model = self.model_selector.get_fallback_model(selected_model, 'job_parsing')
                if fallback_model and fallback_model != selected_model:
                    logger.info(f"Server error fallback to {fallback_model}")
                    context['fallback_attempt'] = True
                    return await self._retry_with_fallback(fallback_model, context, 'job_parsing', user_id)

            return {"error": "Service temporarily unavailable. Please try again."}

        except Exception as e:
            logger.error(f"Unexpected error during job parsing with {selected_model}: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='job_parsing', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )

            # Generic errors should still trigger fallback
            if self.model_selector.should_use_fallback(selected_model, {'error_type': 'unknown'}):
                fallback_model = self.model_selector.get_fallback_model(selected_model, 'job_parsing')
                if fallback_model and fallback_model != selected_model:
                    logger.info(f"Generic error fallback to {fallback_model}")
                    context['fallback_attempt'] = True
                    return await self._retry_with_fallback(fallback_model, context, 'job_parsing', user_id)

            return {"error": f"Failed to parse job description: {str(e)}"}

    async def generate_cv_content(self, job_data: Dict[str, Any], artifacts: List[Dict[str, Any]],
                                preferences: Dict[str, Any] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Enhanced CV generation with intelligent model selection"""

        if preferences is None:
            preferences = {}

        context = {
            'job_data': job_data,
            'artifacts': artifacts,
            'preferences': preferences,
            'task_type': 'cv_generation',
            'job_description': job_data.get('raw_content', ''),
            'requires_creative_writing': preferences.get('tone') == 'creative'
        }

        # Select optimal model
        selected_model = self.model_selector.select_model_for_task('cv_generation', context)

        # Check circuit breaker
        if not await self.circuit_breaker.can_attempt_request(selected_model):
            fallback_model = self.model_selector.get_fallback_model(selected_model, 'cv_generation')
            if fallback_model:
                selected_model = fallback_model
            else:
                return {"error": "All models unavailable due to circuit breaker"}

        start_time = time.time()

        try:
            # Build generation prompt
            prompt = self._build_cv_generation_prompt(job_data, artifacts, preferences)

            # Make API call
            if HAS_LITELLM:
                response = await acompletion(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are a professional CV writer. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2500,
                    api_key=self._get_api_key_for_model(selected_model)
                )
            else:
                response = await self._direct_api_call(selected_model, prompt, max_tokens=2500, temperature=0.3)

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Parse response based on provider
            if self._get_provider_for_model(selected_model) == "anthropic":
                # Handle Anthropic response format
                content_text = response.content[0].text if hasattr(response, 'content') else response.choices[0].message.content
                try:
                    result = json.loads(content_text)
                except json.JSONDecodeError:
                    # Try to extract JSON from text response
                    result = self._extract_json_from_text(content_text)
            else:
                # Handle OpenAI response format
                response_content = response.choices[0].message.content.strip()
                if response_content.startswith('```json'):
                    response_content = response_content[7:]
                    if response_content.endswith('```'):
                        response_content = response_content[:-3]
                elif response_content.startswith('```'):
                    response_content = response_content[3:]
                    if response_content.endswith('```'):
                        response_content = response_content[:-3]

                result = json.loads(response_content.strip())

            # Calculate quality score
            quality_score = self._calculate_cv_quality_score(result, job_data)

            # Calculate cost
            if hasattr(response, 'usage'):
                tokens_used = response.usage.total_tokens
                cost = self.registry.calculate_cost(selected_model, response.usage.prompt_tokens, response.usage.completion_tokens)
            else:
                tokens_used = len(prompt.split()) + len(str(result).split())  # Rough estimate
                cost = self.registry.calculate_cost(selected_model, int(tokens_used * 0.7), int(tokens_used * 0.3))

            # Record success
            await self.circuit_breaker.record_success(selected_model)

            # Track performance
            await self.performance_tracker.record_task(
                model=selected_model,
                task_type='cv_generation',
                processing_time_ms=processing_time_ms,
                tokens_used=tokens_used,
                cost_usd=cost,
                success=True,
                quality_score=quality_score,
                user_id=user_id,
                complexity_score=self.model_selector._calculate_complexity_score(context)
            )

            return {
                'content': result,
                'processing_metadata': {
                    'model_used': selected_model,
                    'processing_time_ms': processing_time_ms,
                    'tokens_used': tokens_used,
                    'cost_usd': float(cost),
                    'quality_score': quality_score,
                    'selection_reason': self.model_selector.get_selection_reason(selected_model, context),
                    'complexity_score': self.model_selector._calculate_complexity_score(context),
                    'fallback_used': context.get('fallback_attempt', False)
                }
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse CV generation response as JSON: {e}")
            return {"error": "Failed to generate valid CV content - invalid JSON response"}

        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded for {selected_model} during CV generation: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='cv_generation', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )

            if self.model_selector.should_use_fallback(selected_model, {'error_type': 'rate_limit'}):
                fallback_model = self.model_selector.get_fallback_model(selected_model, 'cv_generation')
                if fallback_model and fallback_model != selected_model:
                    logger.info(f"Rate limit fallback to {fallback_model} for CV generation")
                    context['fallback_attempt'] = True
                    return await self._retry_with_fallback(fallback_model, context, 'cv_generation', user_id)

            return {"error": "Rate limit exceeded. Please try again later."}

        except AuthenticationError as e:
            logger.error(f"Authentication error for {selected_model} during CV generation: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='cv_generation', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )
            return {"error": "Authentication failed. Please check API credentials."}

        except PermissionDeniedError as e:
            logger.error(f"Permission denied for {selected_model} during CV generation: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='cv_generation', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )
            return {"error": "Access denied to the requested model."}

        except APIConnectionError as e:
            logger.error(f"Connection error for {selected_model} during CV generation: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='cv_generation', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )

            if self.model_selector.should_use_fallback(selected_model, {'error_type': 'connection'}):
                fallback_model = self.model_selector.get_fallback_model(selected_model, 'cv_generation')
                if fallback_model and fallback_model != selected_model:
                    logger.info(f"Connection error fallback to {fallback_model} for CV generation")
                    context['fallback_attempt'] = True
                    return await self._retry_with_fallback(fallback_model, context, 'cv_generation', user_id)

            return {"error": "Connection error. Please check your internet connection."}

        except BadRequestError as e:
            logger.error(f"Bad request for {selected_model} during CV generation: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='cv_generation', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )
            return {"error": f"Invalid request: {str(e)}"}

        except InternalServerError as e:
            logger.error(f"Internal server error for {selected_model} during CV generation: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='cv_generation', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )

            if self.model_selector.should_use_fallback(selected_model, {'error_type': 'server_error'}):
                fallback_model = self.model_selector.get_fallback_model(selected_model, 'cv_generation')
                if fallback_model and fallback_model != selected_model:
                    logger.info(f"Server error fallback to {fallback_model} for CV generation")
                    context['fallback_attempt'] = True
                    return await self._retry_with_fallback(fallback_model, context, 'cv_generation', user_id)

            return {"error": "Service temporarily unavailable. Please try again."}

        except Exception as e:
            logger.error(f"Unexpected error during CV generation with {selected_model}: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self.circuit_breaker.record_failure(selected_model)
            await self.performance_tracker.record_task(
                model=selected_model, task_type='cv_generation', processing_time_ms=processing_time_ms,
                tokens_used=0, cost_usd=0.0, success=False, user_id=user_id
            )

            if self.model_selector.should_use_fallback(selected_model, {'error_type': 'unknown'}):
                fallback_model = self.model_selector.get_fallback_model(selected_model, 'cv_generation')
                if fallback_model and fallback_model != selected_model:
                    logger.info(f"Generic error fallback to {fallback_model} for CV generation")
                    context['fallback_attempt'] = True
                    return await self._retry_with_fallback(fallback_model, context, 'cv_generation', user_id)

            return {"error": f"Failed to generate CV content: {str(e)}"}

    async def rank_artifacts_by_relevance(self, artifacts: List[Dict[str, Any]],
                                        job_requirements: List[str],
                                        user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Enhanced artifact ranking with semantic similarity (when embeddings available)"""

        if not artifacts or not job_requirements:
            return artifacts

        # Try semantic ranking first (if embedding service is available)
        try:
            from .embedding_service import FlexibleEmbeddingService
            embedding_service = FlexibleEmbeddingService()

            # Generate job requirements embedding
            job_text = " ".join(job_requirements)
            job_embedding_result = await embedding_service.generate_embeddings([job_text], use_case='similarity')

            if job_embedding_result:
                job_embedding = job_embedding_result[0]['embedding']

                # Use embedding-based similarity (if artifacts have embeddings)
                return await self._semantic_ranking(artifacts, job_embedding, user_id)

        except ImportError:
            logger.info("Embedding service not available, falling back to keyword-based ranking")
        except Exception as e:
            logger.warning(f"Semantic ranking failed, falling back to keyword-based: {e}")

        # Fallback to keyword-based ranking (enhanced version of original)
        return self._keyword_based_ranking(artifacts, job_requirements)

    def _keyword_based_ranking(self, artifacts: List[Dict[str, Any]], job_requirements: List[str]) -> List[Dict[str, Any]]:
        """Enhanced keyword-based relevance scoring"""
        job_keywords = set()
        for req in job_requirements:
            job_keywords.update(req.lower().split())

        # Remove common words that don't add value
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        job_keywords = job_keywords - stop_words

        for artifact in artifacts:
            relevance_score = 0
            max_possible_score = 0

            # Check title (highest weight)
            title = artifact.get('title', '').lower()
            title_words = set(title.split()) - stop_words
            title_matches = len(title_words.intersection(job_keywords))
            relevance_score += title_matches * 3
            max_possible_score += len(job_keywords) * 3

            # Check description
            description = artifact.get('description', '').lower()
            desc_words = set(description.split()) - stop_words
            desc_matches = len(desc_words.intersection(job_keywords))
            relevance_score += desc_matches * 2
            max_possible_score += len(job_keywords) * 2

            # Check technologies (high weight)
            tech_words = set()
            for tech in artifact.get('technologies', []):
                tech_words.update(tech.lower().split())
            tech_words = tech_words - stop_words
            tech_matches = len(tech_words.intersection(job_keywords))
            relevance_score += tech_matches * 4
            max_possible_score += len(job_keywords) * 4

            # Check achievements
            achievements = artifact.get('achievements', '') or artifact.get('extracted_metadata', {}).get('achievements', [])
            if isinstance(achievements, list):
                achievements_text = ' '.join(achievements).lower()
            else:
                achievements_text = str(achievements).lower()

            achievement_words = set(achievements_text.split()) - stop_words
            achievement_matches = len(achievement_words.intersection(job_keywords))
            relevance_score += achievement_matches * 2

            # Normalize score (0-10)
            if max_possible_score > 0:
                normalized_score = (relevance_score / max_possible_score) * 10
            else:
                normalized_score = 0

            artifact['relevance_score'] = min(10, max(0, normalized_score))

        # Sort by relevance score
        return sorted(artifacts, key=lambda x: x.get('relevance_score', 0), reverse=True)

    async def _semantic_ranking(self, artifacts: List[Dict[str, Any]], job_embedding: List[float], user_id: Optional[int]) -> List[Dict[str, Any]]:
        """Rank artifacts using semantic similarity with job requirements"""
        try:
            from .embedding_service import FlexibleEmbeddingService
            embedding_service = FlexibleEmbeddingService()

            # Generate embeddings for each artifact if they don't have them
            for artifact in artifacts:
                if 'embedding' not in artifact:
                    # Create text representation of artifact
                    artifact_text = f"{artifact.get('title', '')} {artifact.get('description', '')} {' '.join(artifact.get('technologies', []))}"
                    if artifact_text.strip():
                        embedding_results = await embedding_service.generate_embeddings([artifact_text], use_case='similarity', user_id=user_id)
                        if embedding_results and embedding_results[0].get('embedding'):
                            artifact['embedding'] = embedding_results[0]['embedding']

                # Calculate cosine similarity with job embedding
                if 'embedding' in artifact:
                    artifact_embedding = artifact['embedding']
                    similarity = self._cosine_similarity(job_embedding, artifact_embedding)
                    # Convert similarity to 0-10 scale
                    artifact['relevance_score'] = round(similarity * 10, 2)
                else:
                    # Fallback to basic score if no embedding available
                    artifact['relevance_score'] = 5.0

            # Sort by relevance score
            return sorted(artifacts, key=lambda x: x.get('relevance_score', 0), reverse=True)

        except Exception as e:
            logger.warning(f"Semantic ranking failed: {e}, falling back to basic scoring")
            # Fallback: add basic relevance scores to all artifacts
            for i, artifact in enumerate(artifacts):
                # Give a basic score based on position (higher for first items)
                artifact['relevance_score'] = max(1.0, 10.0 - (i * 1.0))
            return sorted(artifacts, key=lambda x: x.get('relevance_score', 0), reverse=True)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math

        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _get_api_key_for_model(self, model_name: str) -> str:
        """Get appropriate API key for model"""
        provider = self._get_provider_for_model(model_name)
        if provider == "openai":
            return settings.OPENAI_API_KEY
        elif provider == "anthropic":
            return settings.ANTHROPIC_API_KEY
        return ""

    def _get_provider_for_model(self, model_name: str) -> str:
        """Get provider name for a model"""
        config = self.registry.get_model_config(model_name)
        return config.get('provider', 'openai') if config else 'openai'

    async def _direct_api_call(self, model_name: str, prompt: str, max_tokens: int = 1000, temperature: float = 0.3):
        """Direct API call when LiteLLM is not available"""
        provider = self._get_provider_for_model(model_name)

        if provider == "openai" and self.openai_client:
            return self.openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a professional assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
        elif provider == "anthropic" and self.anthropic_client:
            return self.anthropic_client.messages.create(
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
        else:
            raise Exception(f"No API client available for {provider}")

    async def _retry_with_fallback(self, fallback_model: str, context: Dict[str, Any], task_type: str, user_id: Optional[int]):
        """Retry operation with fallback model"""
        if task_type == 'job_parsing':
            return await self.parse_job_description(
                context['job_description'],
                context.get('company_name', ''),
                context.get('role_title', ''),
                user_id
            )
        elif task_type == 'cv_generation':
            return await self.generate_cv_content(
                context['job_data'],
                context['artifacts'],
                context.get('preferences', {}),
                user_id
            )

    def _build_parsing_prompt(self, job_description: str, company_name: str, role_title: str) -> str:
        """Build optimized prompt for job description parsing"""
        return f'''
Parse this job description and extract structured information:

Company: {company_name}
Role: {role_title}
Job Description:
{job_description}

Extract the following information and return as valid JSON:
{{
  "role_title": "The job title/position",
  "seniority_level": "junior, mid, senior, lead, principal, etc.",
  "company_info": {{ "name": "{company_name}", "industry": "if mentioned", "size": "if mentioned" }},
  "must_have_skills": ["required skills and technologies"],
  "nice_to_have_skills": ["preferred skills"],
  "key_responsibilities": ["top 5 main responsibilities"],
  "company_values": ["keywords related to company culture/values"],
  "experience_requirements": {{ "years": "years of experience", "education": "education requirements" }},
  "confidence_score": 0.95
}}

Return only valid JSON, no additional text.
        '''

    def _build_cv_generation_prompt(self, job_data: Dict[str, Any], artifacts: List[Dict[str, Any]], preferences: Dict[str, Any]) -> str:
        """Build optimized prompt for CV generation"""
        # This would use Jinja2 templating similar to the original service
        # For brevity, returning a simplified version
        return f'''
Generate a professional CV based on job requirements and user artifacts.

Job Requirements: {json.dumps(job_data, indent=2)}

User Artifacts (top 5 most relevant):
{json.dumps(artifacts[:5], indent=2)}

Preferences: {json.dumps(preferences, indent=2)}

Return a JSON structure with professional_summary, key_skills, experience, projects, education, and certifications.
Ensure all content is grounded in the provided artifacts - NO fabricated information.
        '''

    def _calculate_cv_quality_score(self, cv_content: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """Calculate quality score for generated CV"""
        score = 0.8  # Base score

        # Check if required fields are present
        required_fields = ['professional_summary', 'key_skills', 'experience']
        for field in required_fields:
            if field in cv_content and cv_content[field]:
                score += 0.05

        # Check skill alignment
        job_skills = job_data.get('must_have_skills', [])
        cv_skills = cv_content.get('key_skills', [])
        if job_skills and cv_skills:
            skill_matches = sum(1 for job_skill in job_skills if any(job_skill.lower() in cv_skill.lower() for cv_skill in cv_skills))
            skill_alignment = skill_matches / len(job_skills) if job_skills else 0
            score += skill_alignment * 0.15

        return min(1.0, score)

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response (fallback for non-JSON responses)"""
        # Try to find JSON content in the text
        import re
        json_pattern = r'\{.*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # If no JSON found, return error structure
        return {
            "error": "Could not extract valid JSON from response",
            "raw_response": text[:500]  # First 500 chars for debugging
        }