from rest_framework import serializers
from .models import GeneratedDocument, JobDescription, GenerationFeedback, CVTemplate


class CVGenerationRequestSerializer(serializers.Serializer):
    """Serializer for CV generation requests."""

    job_description = serializers.CharField()
    company_name = serializers.CharField(max_length=255, required=False)
    role_title = serializers.CharField(max_length=255, required=False)
    label_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    template_id = serializers.IntegerField(default=1)
    custom_sections = serializers.DictField(required=False, default=dict)
    generation_preferences = serializers.DictField(required=False, default=dict)

    def validate_generation_preferences(self, value):
        """Validate generation preferences structure."""
        allowed_tones = ['professional', 'technical', 'creative']
        allowed_lengths = ['concise', 'detailed']

        if 'tone' in value and value['tone'] not in allowed_tones:
            raise serializers.ValidationError(f"Tone must be one of: {allowed_tones}")

        if 'length' in value and value['length'] not in allowed_lengths:
            raise serializers.ValidationError(f"Length must be one of: {allowed_lengths}")

        return value

    def validate_custom_sections(self, value):
        """Validate custom sections structure."""
        allowed_sections = [
            'include_publications',
            'include_certifications',
            'include_volunteer'
        ]

        for key in value.keys():
            if key not in allowed_sections:
                raise serializers.ValidationError(f"Unknown section: {key}")

        return value


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    """Serializer for generated documents."""

    class Meta:
        model = GeneratedDocument
        fields = ('id', 'document_type', 'status', 'progress_percentage', 'content',
                 'metadata', 'error_message', 'user_rating', 'user_feedback',
                 'created_at', 'completed_at')
        read_only_fields = ('id', 'created_at')


class GeneratedDocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for generated documents with full content."""

    class Meta:
        model = GeneratedDocument
        fields = ('id', 'document_type', 'job_description_hash', 'label_ids',
                 'template_id', 'custom_sections', 'generation_preferences',
                 'content', 'metadata', 'status', 'progress_percentage',
                 'error_message', 'artifacts_used', 'model_version',
                 'generation_time_ms', 'user_rating', 'user_feedback',
                 'created_at', 'completed_at', 'expires_at')
        read_only_fields = ('id', 'job_description_hash', 'artifacts_used',
                           'model_version', 'generation_time_ms', 'created_at',
                           'completed_at', 'expires_at')


class JobDescriptionSerializer(serializers.ModelSerializer):
    """Serializer for job descriptions."""

    class Meta:
        model = JobDescription
        fields = ('id', 'content_hash', 'raw_content', 'parsed_data',
                 'company_name', 'role_title', 'parsing_confidence', 'created_at')
        read_only_fields = ('id', 'content_hash', 'parsed_data', 'parsing_confidence',
                           'created_at')


class GenerationFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for generation feedback."""

    class Meta:
        model = GenerationFeedback
        fields = ('id', 'generation', 'feedback_type', 'feedback_data', 'created_at')
        read_only_fields = ('id', 'created_at')


class CVTemplateSerializer(serializers.ModelSerializer):
    """Serializer for CV templates."""

    class Meta:
        model = CVTemplate
        fields = ('id', 'name', 'category', 'description', 'preview_image_url',
                 'template_config', 'is_premium', 'is_active')
        read_only_fields = ('id', 'template_config')


class DocumentRatingSerializer(serializers.Serializer):
    """Serializer for rating generated documents."""

    rating = serializers.IntegerField(min_value=1, max_value=10)
    feedback = serializers.CharField(required=False, allow_blank=True)

    def validate_rating(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Rating must be between 1 and 10")
        return value