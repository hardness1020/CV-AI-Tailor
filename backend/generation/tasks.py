"""
Celery tasks for CV generation.
"""

import logging
from celery import shared_task
from django.utils import timezone
from django.apps import apps
from .llm_service import LLMService

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

        # Parse job description if not already parsed
        llm_service = LLMService()
        if not job_desc.parsed_data:
            logger.info(f"Parsing job description for generation {generation_id}")
            parsing_result = llm_service.parse_job_description(
                job_desc.raw_content,
                job_desc.company_name,
                job_desc.role_title
            )

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

        # Rank artifacts by relevance to job
        job_requirements = job_desc.parsed_data.get('must_have_skills', []) + \
                          job_desc.parsed_data.get('nice_to_have_skills', [])

        ranked_artifacts = llm_service.rank_artifacts_by_relevance(
            artifacts_data,
            job_requirements
        )

        generation.progress_percentage = 70
        generation.save()

        # Generate CV content
        logger.info(f"Generating CV content for generation {generation_id}")
        cv_result = llm_service.generate_cv_content(
            job_desc.parsed_data,
            ranked_artifacts,
            generation.generation_preferences
        )

        if 'error' in cv_result:
            generation.status = 'failed'
            generation.error_message = f"Failed to generate CV: {cv_result['error']}"
            generation.save()
            return

        # Store the generated content
        generation.content = cv_result.get('content', {})
        generation.metadata = {
            'model_used': cv_result.get('model_used'),
            'generation_time_ms': cv_result.get('generation_time_ms'),
            'token_usage': cv_result.get('token_usage'),
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
        generation.model_version = cv_result.get('model_used', 'unknown')
        generation.generation_time_ms = cv_result.get('generation_time_ms')

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
def cleanup_expired_generations():
    """Cleanup expired generated documents."""
    GeneratedDocument = apps.get_model('generation', 'GeneratedDocument')

    expired_count = GeneratedDocument.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()

    logger.info(f"Cleaned up {expired_count[0]} expired generated documents")
    return expired_count[0]