from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
# from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import transaction
from .models import Artifact, ArtifactProcessingJob, UploadedFile, EvidenceLink
from .serializers import (
    ArtifactSerializer, ArtifactCreateSerializer, ArtifactUpdateSerializer,
    ArtifactProcessingJobSerializer, UploadedFileSerializer, BulkArtifactUploadSerializer,
    EvidenceLinkCreateSerializer, EvidenceLinkUpdateSerializer, BulkArtifactUpdateSerializer
)
from .tasks import process_artifact_upload
import uuid


class ArtifactListCreateView(generics.ListCreateAPIView):
    """List user's artifacts or create a new one."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Artifact.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ArtifactCreateSerializer
        return ArtifactSerializer

    # @method_decorator(ratelimit(key='user', rate='50/h', method='POST'))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ArtifactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific artifact."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Artifact.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ArtifactUpdateSerializer
        return ArtifactSerializer


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
# @ratelimit(key='user', rate='20/h', method='POST')
def bulk_upload_artifacts(request):
    """
    Handle bulk artifact upload with files and metadata.
    Implements Feature 001 - Artifact Upload System.
    """
    serializer = BulkArtifactUploadSerializer(data=request.data, context={'request': request})

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            # Get validated data
            files = serializer.validated_data.get('files', [])
            metadata = serializer.validated_data['metadata']

            # Create the artifact
            artifact_data = {
                'title': metadata['title'],
                'description': metadata['description'],
                'artifact_type': metadata.get('artifact_type', 'project'),
                'start_date': metadata.get('start_date'),
                'end_date': metadata.get('end_date'),
                'technologies': metadata.get('technologies', []),
                'collaborators': metadata.get('collaborators', [])
            }

            artifact = Artifact.objects.create(user=request.user, **artifact_data)

            # Handle uploaded files
            uploaded_files = []
            for file_obj in files:
                uploaded_file = UploadedFile.objects.create(
                    user=request.user,
                    file=file_obj,
                    original_filename=file_obj.name,
                    file_size=file_obj.size,
                    mime_type=getattr(file_obj, 'content_type', 'application/octet-stream')
                )
                uploaded_files.append(uploaded_file)

                # Create evidence link for the file
                EvidenceLink.objects.create(
                    artifact=artifact,
                    url=f"/media/{uploaded_file.file.name}",
                    link_type='document',
                    description=f"Uploaded file: {uploaded_file.original_filename}",
                    file_path=uploaded_file.file.name,
                    file_size=uploaded_file.file_size,
                    mime_type=uploaded_file.mime_type
                )

            # Handle evidence links from metadata
            evidence_links = metadata.get('evidence_links', [])
            for link_data in evidence_links:
                EvidenceLink.objects.create(
                    artifact=artifact,
                    url=link_data['url'],
                    link_type=link_data.get('type', 'other'),
                    description=link_data.get('description', '')
                )

            # Create processing job
            processing_job = ArtifactProcessingJob.objects.create(
                artifact=artifact,
                status='pending'
            )

            # Start async processing
            process_artifact_upload.delay(artifact.id, processing_job.id)

            return Response({
                'artifact_id': artifact.id,
                'status': 'processing',
                'task_id': str(processing_job.id),
                'estimated_completion': timezone.now().isoformat(),
                'uploaded_files_count': len(uploaded_files),
                'evidence_links_count': len(evidence_links)
            }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        return Response({
            'error': 'Failed to process upload',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def artifact_processing_status(request, artifact_id):
    """
    Get processing status for an artifact.
    Implements the status checking from Feature 001.
    """
    try:
        artifact = Artifact.objects.get(id=artifact_id, user=request.user)
        processing_job = artifact.processing_jobs.order_by('-created_at').first()

        if not processing_job:
            return Response({
                'error': 'No processing job found for this artifact'
            }, status=status.HTTP_404_NOT_FOUND)

        # Count evidence links
        total_evidence_count = artifact.evidence_links.count()
        processed_evidence_count = artifact.evidence_links.filter(
            last_validated__isnull=False
        ).count()

        return Response({
            'artifact_id': artifact_id,
            'status': processing_job.status,
            'progress_percentage': processing_job.progress_percentage,
            'error_message': processing_job.error_message,
            'processed_evidence_count': processed_evidence_count,
            'total_evidence_count': total_evidence_count,
            'created_at': processing_job.created_at,
            'completed_at': processing_job.completed_at
        })

    except Artifact.DoesNotExist:
        return Response({
            'error': 'Artifact not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_artifact_files(request, artifact_id):
    """
    Upload files to a specific artifact.
    """
    try:
        artifact = Artifact.objects.get(id=artifact_id, user=request.user)
    except Artifact.DoesNotExist:
        return Response({'error': 'Artifact not found'}, status=status.HTTP_404_NOT_FOUND)

    files = request.FILES.getlist('files')
    if not files:
        return Response({'error': 'No files provided'}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_files = []
    for file in files:
        serializer = UploadedFileSerializer(data={'file': file}, context={'request': request})
        if serializer.is_valid():
            uploaded_file = serializer.save()
            uploaded_files.append({
                'file_id': uploaded_file.id,
                'filename': uploaded_file.original_filename,
                'size': uploaded_file.file_size,
                'mime_type': uploaded_file.mime_type
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({'uploaded_files': uploaded_files}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser])
# @ratelimit(key='user', rate='100/h', method='POST')
def upload_file(request):
    """
    Simple file upload endpoint for individual files.
    """
    serializer = UploadedFileSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        uploaded_file = serializer.save()
        return Response({
            'file_id': uploaded_file.id,
            'filename': uploaded_file.original_filename,
            'size': uploaded_file.file_size,
            'mime_type': uploaded_file.mime_type,
            'url': uploaded_file.file.url if uploaded_file.file else None
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def artifact_suggestions(request):
    """
    Get technology suggestions based on common skills taxonomy.
    """
    # Common technology suggestions
    technology_suggestions = [
        'Python', 'JavaScript', 'TypeScript', 'React', 'Node.js', 'Django',
        'Flask', 'FastAPI', 'Vue.js', 'Angular', 'HTML', 'CSS', 'SASS',
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Docker', 'Kubernetes',
        'AWS', 'Azure', 'GCP', 'Git', 'Jenkins', 'GitHub Actions',
        'Machine Learning', 'Data Science', 'TensorFlow', 'PyTorch',
        'REST API', 'GraphQL', 'Microservices', 'Agile', 'Scrum'
    ]

    # Filter based on query parameter
    query = request.GET.get('q', '').lower()
    if query:
        filtered_suggestions = [
            tech for tech in technology_suggestions
            if query in tech.lower()
        ]
        return Response({
            'suggestions': filtered_suggestions[:10]
        })

    return Response({
        'suggestions': technology_suggestions[:20]
    })