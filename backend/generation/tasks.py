"""
Enhanced Celery tasks for CV generation with new LLM services.
Integrates ft-llm-001, ft-llm-002, and ft-llm-003 implementations.
"""

import logging
import asyncio
from celery import shared_task
from django.utils import timezone
from django.apps import apps
from django.conf import settings
from llm_services.services.enhanced_llm_service import EnhancedLLMService
from llm_services.services.embedding_service import FlexibleEmbeddingService
from llm_services.services.document_processor import AdvancedDocumentProcessor

logger = logging.getLogger(__name__)


@shared_task
def generate_cv_task(generation_id):
    """
    Generate CV content using LLM service.
    Implements Feature 002 - CV Generation System.
    """
    try:
        # Import models here to avoid circular imports
        GeneratedDocument = apps.get_model('generation', 'GeneratedDocument')
        JobDescription = apps.get_model('generation', 'JobDescription')
        Artifact = apps.get_model('artifacts', 'Artifact')

        generation = GeneratedDocument.objects.get(id=generation_id)
        generation.status = 'processing'
        generation.progress_percentage = 10
        generation.save()

        # Get or parse job description
        if generation.job_description:
            job_desc = generation.job_description
        else:
            # This shouldn't happen, but handle gracefully
            logger.warning(f"No job description found for generation {generation_id}")
            generation.status = 'failed'
            generation.error_message = 'No job description provided'
            generation.save()
            return

        # Parse job description using enhanced LLM service
        llm_service = EnhancedLLMService()
        if not job_desc.parsed_data:
            logger.info(f"Parsing job description for generation {generation_id} with enhanced service")
            parsing_result = asyncio.run(llm_service.parse_job_description(
                job_desc.raw_content,
                job_desc.company_name,
                job_desc.role_title,
                generation.user.id
            ))

            if 'error' in parsing_result:
                generation.status = 'failed'
                generation.error_message = f"Failed to parse job description: {parsing_result['error']}"
                generation.save()
                return

            job_desc.parsed_data = parsing_result
            job_desc.parsing_confidence = parsing_result.get('confidence_score', 0.5)
            job_desc.save()

        generation.progress_percentage = 30
        generation.save()

        # Get user artifacts
        user_artifacts = Artifact.objects.filter(user=generation.user)

        # Filter by label_ids if specified
        if generation.label_ids:
            # Note: This assumes artifacts have a label relationship
            # For now, we'll use all artifacts
            pass

        # Convert artifacts to dict format for LLM
        artifacts_data = []
        for artifact in user_artifacts:
            artifact_dict = {
                'id': artifact.id,
                'title': artifact.title,
                'description': artifact.description,
                'artifact_type': artifact.artifact_type,
                'start_date': str(artifact.start_date) if artifact.start_date else None,
                'end_date': str(artifact.end_date) if artifact.end_date else None,
                'technologies': artifact.technologies,
                'collaborators': artifact.collaborators,
                'evidence_links': [
                    {
                        'url': link.url,
                        'type': link.link_type,
                        'description': link.description
                    }
                    for link in artifact.evidence_links.all()
                ],
                'extracted_metadata': artifact.extracted_metadata
            }
            artifacts_data.append(artifact_dict)

        generation.progress_percentage = 50
        generation.save()

        # Enhanced artifact ranking with semantic similarity
        job_requirements = job_desc.parsed_data.get('must_have_skills', []) + \
                          job_desc.parsed_data.get('nice_to_have_skills', [])

        ranked_artifacts = asyncio.run(llm_service.rank_artifacts_by_relevance(
            artifacts_data,
            job_requirements,
            generation.user.id
        ))

        generation.progress_percentage = 70
        generation.save()

        # Generate CV content with enhanced service
        logger.info(f"Generating CV content for generation {generation_id} with enhanced service")
        cv_result = asyncio.run(llm_service.generate_cv_content(
            job_desc.parsed_data,
            ranked_artifacts,
            generation.generation_preferences,
            generation.user.id
        ))

        if 'error' in cv_result:
            generation.status = 'failed'
            generation.error_message = f"Failed to generate CV: {cv_result['error']}"
            generation.save()
            return

        # Store the generated content with enhanced metadata
        generation.content = cv_result.get('content', {})
        processing_metadata = cv_result.get('processing_metadata', {})

        generation.metadata = {
            'model_used': processing_metadata.get('model_used'),
            'generation_time_ms': processing_metadata.get('processing_time_ms'),
            'token_usage': processing_metadata.get('tokens_used'),
            'cost_usd': processing_metadata.get('cost_usd'),
            'quality_score': processing_metadata.get('quality_score'),
            'selection_reason': processing_metadata.get('selection_reason'),
            'complexity_score': processing_metadata.get('complexity_score'),
            'fallback_used': processing_metadata.get('fallback_used', False),
            'artifacts_used': [a['id'] for a in ranked_artifacts[:5]],  # Top 5 used
            'skill_match_score': calculate_skill_match_score(
                generation.content.get('key_skills', []),
                job_requirements
            ),
            'missing_skills': find_missing_skills(
                generation.content.get('key_skills', []),
                job_desc.parsed_data.get('must_have_skills', [])
            )
        }

        generation.artifacts_used = generation.metadata['artifacts_used']
        generation.model_version = processing_metadata.get('model_used', 'unknown')
        generation.generation_time_ms = processing_metadata.get('processing_time_ms')
        generation.model_selection_strategy = getattr(settings, 'MODEL_SELECTION_STRATEGY', 'balanced')
        generation.total_cost_usd = processing_metadata.get('cost_usd', 0.0)

        # Complete generation
        generation.status = 'completed'
        generation.progress_percentage = 100
        generation.completed_at = timezone.now()
        generation.save()

        logger.info(f"Successfully generated CV for generation {generation_id}")

    except Exception as e:
        logger.error(f"Error generating CV for {generation_id}: {e}")
        try:
            generation = GeneratedDocument.objects.get(id=generation_id)
            generation.status = 'failed'
            generation.error_message = str(e)
            generation.save()
        except:
            pass


def calculate_skill_match_score(user_skills, job_requirements):
    """Calculate how well user skills match job requirements (0-10)."""
    if not user_skills or not job_requirements:
        return 0

    # Normalize skills to lowercase for comparison
    user_skills_lower = [skill.lower() for skill in user_skills]
    job_requirements_lower = [req.lower() for req in job_requirements]

    matches = 0
    for req in job_requirements_lower:
        for user_skill in user_skills_lower:
            if req in user_skill or user_skill in req:
                matches += 1
                break

    # Calculate score (0-10)
    match_ratio = matches / len(job_requirements_lower)
    return min(10, int(match_ratio * 10))


def find_missing_skills(user_skills, required_skills):
    """Find required skills that are missing from user skills."""
    if not user_skills or not required_skills:
        return required_skills

    user_skills_lower = [skill.lower() for skill in user_skills]
    missing = []

    for req_skill in required_skills:
        req_skill_lower = req_skill.lower()
        found = False

        for user_skill in user_skills_lower:
            if req_skill_lower in user_skill or user_skill in req_skill_lower:
                found = True
                break

        if not found:
            missing.append(req_skill)

    return missing


@shared_task
def generate_job_embedding_cache(job_description: str, company_name: str = "", role_title: str = "", user_id: int = None):
    """Pre-generate and cache job description embedding for faster CV generation."""
    try:
        embedding_service = FlexibleEmbeddingService()

        result = asyncio.run(embedding_service.generate_and_cache_job_embedding(
            job_description=job_description,
            company_name=company_name,
            role_title=role_title,
            user_id=user_id
        ))

        logger.info(f"Generated job embedding cache: {result.get('job_hash', 'unknown')[:8]}...")
        return result

    except Exception as e:
        logger.error(f"Job embedding cache generation failed: {e}")
        return {'error': str(e)}


@shared_task(bind=True, max_retries=3)
def enhance_artifact_with_llm(self, artifact_id: int):
    """
    Enhanced artifact processing with LangChain and embeddings.
    Implements ft-llm-001-content-extraction.md and ft-llm-002-embedding-storage.md
    """
    try:
        Artifact = apps.get_model('artifacts', 'Artifact')
        artifact = Artifact.objects.get(id=artifact_id)

        logger.info(f"Starting enhanced processing for artifact {artifact_id}: {artifact.title}")

        # Initialize services
        doc_processor = AdvancedDocumentProcessor()
        embedding_service = FlexibleEmbeddingService()

        # Step 1: Process document with LangChain
        # Check for evidence links with files or uploaded files
        evidence_with_file = artifact.evidence_links.filter(
            file_path__isnull=False
        ).exclude(file_path='').first()

        if evidence_with_file:
            # Process file from evidence link
            processing_result = asyncio.run(doc_processor.process_document(
                content=evidence_with_file.file_path,
                content_type=artifact.artifact_type,
                metadata={
                    'title': artifact.title,
                    'description': artifact.description,
                    'artifact_id': artifact_id,
                    'user_id': artifact.user.id
                },
                user_id=artifact.user.id
            ))
        else:
            # Process text content
            processing_result = asyncio.run(doc_processor.process_document(
                content=artifact.description or artifact.title,
                content_type='text',
                metadata={
                    'title': artifact.title,
                    'artifact_id': artifact_id,
                    'user_id': artifact.user.id
                },
                user_id=artifact.user.id
            ))

        if not processing_result.get('success', False):
            error_detail = processing_result.get('error', 'Unknown processing error')
            logger.error(f"Document processing failed for artifact {artifact_id}: {error_detail}")
            raise Exception(f"Document processing failed: {error_detail}")

        # Step 2: Generate and store embeddings
        chunks = processing_result.get('chunks', [])
        main_content = artifact.description or artifact.title
        if chunks:
            # Use first chunk as main content if available
            main_content = chunks[0].get('content', main_content)

        embedding_result = asyncio.run(embedding_service.store_artifact_embeddings(
            artifact_id=str(artifact.id),
            content=main_content,
            chunks=chunks,
            user_id=artifact.user.id
        ))

        # Step 3: Update artifact with enhanced data
        artifact.extracted_metadata = {
            'langchain_processing': processing_result.get('processing_metadata', {}),
            'embedding_result': {
                'total_cost_usd': embedding_result.get('total_cost_usd', 0.0),
                'chunks_processed': embedding_result.get('chunks_processed', 0),
                'model_used': embedding_result.get('main_embedding', {}).get('model_used')
            },
            'enhanced_chunks': len(chunks),
            'processing_timestamp': timezone.now().isoformat()
        }

        # Extract skills and achievements from processed chunks
        extracted_skills = set()
        extracted_achievements = []

        for chunk in chunks:
            enhanced_data = chunk.get('enhanced_data', {})
            if isinstance(enhanced_data, dict):
                # Extract skills
                skills = enhanced_data.get('must_have_skills', []) + enhanced_data.get('nice_to_have_skills', [])
                extracted_skills.update(skills)

                # Extract achievements
                if 'key_responsibilities' in enhanced_data:
                    extracted_achievements.extend(enhanced_data['key_responsibilities'])

        # Update artifact fields
        if extracted_skills:
            artifact.technologies = list(extracted_skills)[:20]  # Limit to 20 skills
        if extracted_achievements:
            artifact.achievements = '\n'.join(extracted_achievements[:10])  # Limit to 10 achievements

        artifact.save()

        logger.info(f"Successfully enhanced artifact {artifact_id} with {len(chunks)} chunks and embeddings")
        return {
            'artifact_id': artifact_id,
            'chunks_processed': len(chunks),
            'embedding_cost': embedding_result.get('total_cost_usd', 0.0),
            'skills_extracted': len(extracted_skills),
            'achievements_extracted': len(extracted_achievements)
        }

    except Exception as e:
        logger.error(f"Artifact processing failed for {artifact_id}: {e}", exc_info=True)

        # Skip retries in test environment
        import sys
        is_testing = 'test' in sys.argv or hasattr(sys, '_called_from_test')

        # Retry with exponential backoff (skip in testing)
        if not is_testing and self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        # Final failure - update artifact with error info
        try:
            artifact = Artifact.objects.get(id=artifact_id)
            artifact.extracted_metadata = {
                'processing_error': str(e),
                'processing_timestamp': timezone.now().isoformat(),
                'retry_count': self.request.retries
            }
            artifact.save()
        except Exception as save_error:
            logger.error(f"Failed to save error metadata for artifact {artifact_id}: {save_error}")

        return {'error': str(e), 'artifact_id': artifact_id}


@shared_task
def cleanup_expired_generations():
    """Cleanup expired generated documents."""
    GeneratedDocument = apps.get_model('generation', 'GeneratedDocument')

    expired_count = GeneratedDocument.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()

    logger.info(f"Cleaned up {expired_count[0]} expired generated documents")
    return expired_count[0]


@shared_task
def cleanup_old_performance_metrics():
    """Cleanup old performance metrics and embeddings."""
    from llm_services.services.performance_tracker import ModelPerformanceTracker
    from llm_services.services.embedding_service import FlexibleEmbeddingService

    performance_tracker = ModelPerformanceTracker()
    embedding_service = FlexibleEmbeddingService()

    # Cleanup old performance metrics (keep 30 days)
    metrics_cleaned = performance_tracker.cleanup_old_metrics(days_to_keep=30)

    # Cleanup old job embeddings (keep 90 days)
    embeddings_cleaned = embedding_service.cleanup_old_embeddings(days_to_keep=90)

    logger.info(f"Cleaned up {metrics_cleaned} old performance metrics and {embeddings_cleaned} old embeddings")
    return {
        'metrics_cleaned': metrics_cleaned,
        'embeddings_cleaned': embeddings_cleaned
    }