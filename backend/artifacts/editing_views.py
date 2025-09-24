from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from .models import Artifact, EvidenceLink, UploadedFile
from .serializers import (
    EvidenceLinkCreateSerializer, EvidenceLinkUpdateSerializer,
    BulkArtifactUpdateSerializer
)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_evidence_link(request, artifact_id):
    """
    Add a new evidence link to an artifact.
    """
    try:
        artifact = Artifact.objects.get(id=artifact_id, user=request.user)
    except Artifact.DoesNotExist:
        return Response({'error': 'Artifact not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = EvidenceLinkCreateSerializer(data=request.data)
    if serializer.is_valid():
        evidence_link = serializer.save(artifact=artifact)
        return Response({
            'id': evidence_link.id,
            'url': evidence_link.url,
            'link_type': evidence_link.link_type,
            'description': evidence_link.description,
            'created_at': evidence_link.created_at
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def evidence_link_detail(request, link_id):
    """
    Update or delete a specific evidence link.
    """
    try:
        evidence_link = EvidenceLink.objects.select_related('artifact').get(
            id=link_id,
            artifact__user=request.user
        )
    except EvidenceLink.DoesNotExist:
        return Response({'error': 'Evidence link not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = EvidenceLinkUpdateSerializer(evidence_link, data=request.data)
        if serializer.is_valid():
            evidence_link = serializer.save()
            return Response({
                'id': evidence_link.id,
                'url': evidence_link.url,
                'link_type': evidence_link.link_type,
                'description': evidence_link.description,
                'updated_at': evidence_link.updated_at
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        evidence_link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_artifact_file(request, file_id):
    """
    Delete a file associated with an artifact.
    """
    try:
        # Find and delete the uploaded file
        uploaded_file = UploadedFile.objects.get(id=file_id, user=request.user)

        # Find associated evidence link
        evidence_link = EvidenceLink.objects.filter(
            file_path__contains=str(file_id),
            artifact__user=request.user
        ).first()

        # Delete the physical file
        if uploaded_file.file:
            uploaded_file.file.delete(save=False)

        # Delete the database record
        uploaded_file.delete()

        # Delete the associated evidence link if it exists
        if evidence_link:
            evidence_link.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    except UploadedFile.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'Failed to delete file',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def bulk_update_artifacts(request):
    """
    Bulk update multiple artifacts.
    """
    serializer = BulkArtifactUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    artifact_ids = serializer.validated_data['artifact_ids']
    action = serializer.validated_data['action']
    values = serializer.validated_data['values']

    # Verify user owns all artifacts
    user_artifacts = Artifact.objects.filter(
        id__in=artifact_ids,
        user=request.user
    ).values_list('id', flat=True)

    if len(user_artifacts) != len(artifact_ids):
        return Response({
            'error': 'Some artifacts not found or not owned by user'
        }, status=status.HTTP_400_BAD_REQUEST)

    results = []

    for artifact_id in artifact_ids:
        try:
            with transaction.atomic():
                artifact = Artifact.objects.select_for_update().get(
                    id=artifact_id,
                    user=request.user
                )

                if action == 'add_technologies':
                    current_technologies = set(artifact.technologies or [])
                    new_technologies = set(values['technologies'])
                    artifact.technologies = list(current_technologies | new_technologies)

                elif action == 'remove_technologies':
                    current_technologies = set(artifact.technologies or [])
                    remove_technologies = set(values['technologies'])
                    artifact.technologies = list(current_technologies - remove_technologies)

                elif action == 'update_type':
                    artifact.artifact_type = values['artifact_type']

                elif action == 'add_collaborators':
                    current_collaborators = set(artifact.collaborators or [])
                    new_collaborators = set(values['collaborators'])
                    artifact.collaborators = list(current_collaborators | new_collaborators)

                elif action == 'remove_collaborators':
                    current_collaborators = set(artifact.collaborators or [])
                    remove_collaborators = set(values['collaborators'])
                    artifact.collaborators = list(current_collaborators - remove_collaborators)

                artifact.save()

                results.append({
                    'id': artifact_id,
                    'status': 'success',
                    'updated_fields': [action]
                })

        except Exception as e:
            results.append({
                'id': artifact_id,
                'status': 'error',
                'message': str(e)
            })

    return Response({
        'results': results,
        'total_processed': len(results),
        'successful': len([r for r in results if r['status'] == 'success']),
        'failed': len([r for r in results if r['status'] == 'error'])
    })