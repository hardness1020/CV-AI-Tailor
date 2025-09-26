from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
# from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta
from .models import GeneratedDocument, JobDescription, CVTemplate, GenerationFeedback
from .serializers import (
    CVGenerationRequestSerializer, GeneratedDocumentSerializer,
    GeneratedDocumentDetailSerializer, CVTemplateSerializer,
    GenerationFeedbackSerializer, DocumentRatingSerializer
)
from .tasks import generate_cv_task


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
# @ratelimit(key='user', rate='10/h', method='POST')
def generate_cv(request):
    """
    Generate CV based on job description and user artifacts.
    Implements Feature 002 - CV Generation System.
    """
    serializer = CVGenerationRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        data = serializer.validated_data

        # Get or create job description
        job_desc, created = JobDescription.get_or_create_from_content(
            data['job_description'],
            data.get('company_name', ''),
            data.get('role_title', '')
        )

        # Set expiration (90 days from now)
        expires_at = timezone.now() + timedelta(days=90)

        # Create generation document
        generation = GeneratedDocument.objects.create(
            user=request.user,
            document_type='cv',
            job_description_hash=job_desc.content_hash,
            job_description=job_desc,
            label_ids=data.get('label_ids', []),
            template_id=data.get('template_id', 1),
            custom_sections=data.get('custom_sections', {}),
            generation_preferences=data.get('generation_preferences', {}),
            expires_at=expires_at
        )

        # Start async generation
        generate_cv_task.delay(str(generation.id))

        return Response({
            'generation_id': str(generation.id),
            'status': 'processing',
            'estimated_completion_time': timezone.now() + timedelta(seconds=30),
            'job_description_hash': job_desc.content_hash
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        return Response({
            'error': 'Failed to initiate CV generation',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
# @ratelimit(key='user', rate='10/h', method='POST')
def generate_cover_letter(request):
    """
    Generate cover letter based on job description and user artifacts.
    Similar to CV generation but for cover letters.
    """
    serializer = CVGenerationRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        data = serializer.validated_data

        # Get or create job description
        job_desc, created = JobDescription.get_or_create_from_content(
            data['job_description'],
            data.get('company_name', ''),
            data.get('role_title', '')
        )

        # Set expiration (90 days from now)
        expires_at = timezone.now() + timedelta(days=90)

        # Create generation document for cover letter
        generation = GeneratedDocument.objects.create(
            user=request.user,
            document_type='cover_letter',
            job_description_hash=job_desc.content_hash,
            job_description=job_desc,
            label_ids=data.get('label_ids', []),
            template_id=data.get('template_id', 1),
            custom_sections=data.get('custom_sections', {}),
            generation_preferences=data.get('generation_preferences', {}),
            expires_at=expires_at
        )

        # Start async generation (same task handles both types)
        generate_cv_task.delay(str(generation.id))

        return Response({
            'generation_id': str(generation.id),
            'status': 'processing',
            'estimated_completion_time': timezone.now() + timedelta(seconds=30),
            'job_description_hash': job_desc.content_hash
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        return Response({
            'error': 'Failed to initiate cover letter generation',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def generation_status(request, generation_id):
    """
    Get generation status and content when completed.
    """
    try:
        generation = GeneratedDocument.objects.get(
            id=generation_id,
            user=request.user
        )

        if generation.status == 'completed':
            serializer = GeneratedDocumentDetailSerializer(generation)
        else:
            serializer = GeneratedDocumentSerializer(generation)

        return Response(serializer.data)

    except GeneratedDocument.DoesNotExist:
        return Response({
            'error': 'Generation not found'
        }, status=status.HTTP_404_NOT_FOUND)


class UserGenerationsListView(generics.ListAPIView):
    """List user's generated documents."""

    serializer_class = GeneratedDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GeneratedDocument.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class GenerationDetailView(generics.RetrieveDestroyAPIView):
    """Retrieve or delete a specific generation."""

    serializer_class = GeneratedDocumentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GeneratedDocument.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def rate_generation(request, generation_id):
    """
    Rate a generated document and provide feedback.
    """
    try:
        generation = GeneratedDocument.objects.get(
            id=generation_id,
            user=request.user
        )

        serializer = DocumentRatingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Update generation rating
        generation.user_rating = serializer.validated_data['rating']
        generation.user_feedback = serializer.validated_data.get('feedback', '')
        generation.save()

        # Create feedback record
        GenerationFeedback.objects.create(
            generation=generation,
            feedback_type='rating',
            feedback_data={
                'rating': serializer.validated_data['rating'],
                'feedback': serializer.validated_data.get('feedback', '')
            }
        )

        return Response({
            'message': 'Rating submitted successfully',
            'rating': generation.user_rating
        })

    except GeneratedDocument.DoesNotExist:
        return Response({
            'error': 'Generation not found'
        }, status=status.HTTP_404_NOT_FOUND)


class CVTemplateListView(generics.ListAPIView):
    """List available CV templates."""

    serializer_class = CVTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CVTemplate.objects.filter(is_active=True)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def generation_analytics(request):
    """
    Get analytics for user's generations.
    """
    user_generations = GeneratedDocument.objects.filter(user=request.user)

    analytics = {
        'total_generations': user_generations.count(),
        'completed_generations': user_generations.filter(status='completed').count(),
        'failed_generations': user_generations.filter(status='failed').count(),
        'average_rating': 0,
        'most_used_template': None,
        'generation_history': []
    }

    # Calculate average rating
    rated_generations = user_generations.filter(user_rating__isnull=False)
    if rated_generations.exists():
        total_rating = sum(g.user_rating for g in rated_generations)
        analytics['average_rating'] = round(total_rating / rated_generations.count(), 1)

    # Most used template
    template_usage = {}
    for gen in user_generations:
        template_id = gen.template_id
        template_usage[template_id] = template_usage.get(template_id, 0) + 1

    if template_usage:
        most_used_template_id = max(template_usage, key=template_usage.get)
        try:
            template = CVTemplate.objects.get(id=most_used_template_id)
            analytics['most_used_template'] = template.name
        except CVTemplate.DoesNotExist:
            pass

    # Recent generation history (last 10)
    recent_generations = user_generations.order_by('-created_at')[:10]
    analytics['generation_history'] = [
        {
            'id': str(gen.id),
            'status': gen.status,
            'created_at': gen.created_at,
            'rating': gen.user_rating
        }
        for gen in recent_generations
    ]

    return Response(analytics)