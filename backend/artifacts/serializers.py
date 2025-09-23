from rest_framework import serializers
from .models import Artifact, EvidenceLink, ArtifactProcessingJob, UploadedFile


class EvidenceLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceLink
        fields = ('id', 'url', 'link_type', 'description', 'file_path', 'file_size',
                 'mime_type', 'validation_metadata', 'last_validated', 'is_accessible',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'validation_metadata', 'last_validated', 'is_accessible',
                           'created_at', 'updated_at')


class ArtifactSerializer(serializers.ModelSerializer):
    evidence_links = EvidenceLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Artifact
        fields = ('id', 'title', 'description', 'artifact_type', 'start_date', 'end_date',
                 'technologies', 'collaborators', 'extracted_metadata', 'evidence_links',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'extracted_metadata', 'created_at', 'updated_at')


class ArtifactCreateSerializer(serializers.ModelSerializer):
    evidence_links = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Artifact
        fields = ('title', 'description', 'artifact_type', 'start_date', 'end_date',
                 'technologies', 'collaborators', 'evidence_links')

    def create(self, validated_data):
        evidence_links_data = validated_data.pop('evidence_links', [])
        artifact = Artifact.objects.create(user=self.context['request'].user, **validated_data)

        # Create evidence links
        for link_data in evidence_links_data:
            EvidenceLink.objects.create(artifact=artifact, **link_data)

        return artifact


class ArtifactProcessingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtifactProcessingJob
        fields = ('id', 'artifact', 'status', 'progress_percentage', 'error_message',
                 'metadata_extracted', 'evidence_validation_results', 'created_at', 'completed_at')
        read_only_fields = ('id', 'created_at', 'completed_at')


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ('id', 'file', 'original_filename', 'file_size', 'mime_type',
                 'is_processed', 'processing_error', 'created_at')
        read_only_fields = ('id', 'file_size', 'mime_type', 'is_processed', 'processing_error',
                           'created_at')

    def create(self, validated_data):
        file_obj = validated_data['file']
        validated_data['original_filename'] = file_obj.name
        validated_data['file_size'] = file_obj.size
        validated_data['mime_type'] = getattr(file_obj, 'content_type', 'application/octet-stream')
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BulkArtifactUploadSerializer(serializers.Serializer):
    """Serializer for bulk artifact upload with files and metadata."""

    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True
    )

    metadata = serializers.DictField(required=True)

    def validate_files(self, files):
        """Validate uploaded files."""
        if len(files) > 10:
            raise serializers.ValidationError("Maximum 10 files allowed per upload.")

        for file_obj in files:
            # Check file size (10MB limit)
            if file_obj.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(f"File {file_obj.name} exceeds 10MB size limit.")

            # Check file type
            allowed_types = ['application/pdf', 'application/msword',
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            content_type = getattr(file_obj, 'content_type', '')
            if content_type not in allowed_types:
                raise serializers.ValidationError(f"File {file_obj.name} has unsupported type: {content_type}")

        return files

    def validate_metadata(self, metadata):
        """Validate metadata structure."""
        required_fields = ['title', 'description']
        for field in required_fields:
            if field not in metadata:
                raise serializers.ValidationError(f"Metadata missing required field: {field}")

        # Validate evidence links if provided
        evidence_links = metadata.get('evidence_links', [])
        if evidence_links:
            for link in evidence_links:
                if 'url' not in link:
                    raise serializers.ValidationError("Evidence links must contain 'url' field.")
                if 'type' not in link:
                    raise serializers.ValidationError("Evidence links must contain 'type' field.")

        return metadata