"""
DRF serializers for LLM services API endpoints.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import models
from .models import (
    ModelPerformanceMetric,
    EnhancedArtifact,
    ArtifactChunk,
    JobDescriptionEmbedding,
    ModelCostTracking,
    CircuitBreakerState
)

User = get_user_model()


class ModelPerformanceMetricSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ModelPerformanceMetric
        fields = [
            'id', 'model_name', 'task_type', 'processing_time_ms',
            'tokens_used', 'cost_usd', 'quality_score', 'success',
            'complexity_score', 'selection_strategy', 'fallback_used',
            'metadata', 'created_at', 'user_email'
        ]
        read_only_fields = ['id', 'created_at', 'user_email']


class CircuitBreakerStateSerializer(serializers.ModelSerializer):
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    is_healthy = serializers.SerializerMethodField()

    class Meta:
        model = CircuitBreakerState
        fields = [
            'model_name', 'failure_count', 'last_failure', 'state',
            'state_display', 'failure_threshold', 'timeout_duration',
            'created_at', 'updated_at', 'is_healthy'
        ]
        read_only_fields = ['created_at', 'updated_at', 'state_display', 'is_healthy']

    def get_is_healthy(self, obj):
        return obj.state == 'closed'


class ModelCostTrackingSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ModelCostTracking
        fields = [
            'id', 'user_email', 'date', 'model_name', 'total_cost_usd',
            'generation_count', 'avg_cost_per_generation',
            'total_tokens_used', 'avg_tokens_per_generation'
        ]
        read_only_fields = ['id', 'user_email']


class JobDescriptionEmbeddingSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    embedding_vector = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = JobDescriptionEmbedding
        fields = [
            'id', 'job_description_hash', 'company_name', 'role_title',
            'model_used', 'dimensions', 'tokens_used', 'cost_usd',
            'access_count', 'last_accessed', 'created_at', 'user_email',
            'embedding_vector'
        ]
        read_only_fields = [
            'id', 'job_description_hash', 'access_count', 'last_accessed',
            'created_at', 'user_email'
        ]


class EnhancedArtifactSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    total_processing_cost = serializers.SerializerMethodField()
    content_embedding = serializers.JSONField(write_only=True, required=False)
    summary_embedding = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = EnhancedArtifact
        fields = [
            'id', 'user_email', 'original_artifact_id', 'title', 'content_type',
            'embedding_model', 'embedding_dimensions', 'embedding_cost_usd',
            'langchain_version', 'processing_strategy', 'total_chunks',
            'processing_time_ms', 'llm_model_used', 'created_at', 'updated_at',
            'last_embedding_update', 'total_processing_cost', 'content_embedding',
            'summary_embedding'
        ]
        read_only_fields = [
            'id', 'user_email', 'created_at', 'updated_at',
            'last_embedding_update', 'total_processing_cost'
        ]

    def get_total_processing_cost(self, obj):
        chunk_costs = obj.chunks.aggregate(
            total=models.Sum('processing_cost_usd')
        ).get('total', 0) or 0
        return float(obj.embedding_cost_usd) + float(chunk_costs)


class ArtifactChunkSerializer(serializers.ModelSerializer):
    artifact_title = serializers.CharField(source='artifact.title', read_only=True)
    embedding_vector = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = ArtifactChunk
        fields = [
            'id', 'artifact_title', 'chunk_index', 'content', 'metadata',
            'content_hash', 'model_used', 'tokens_used', 'processing_cost_usd',
            'created_at', 'embedding_vector'
        ]
        read_only_fields = [
            'id', 'artifact_title', 'content_hash', 'created_at'
        ]


class ModelStatsSerializer(serializers.Serializer):
    """Aggregated model statistics"""
    model_name = serializers.CharField()
    total_requests = serializers.IntegerField()
    success_rate = serializers.FloatField()
    avg_processing_time_ms = serializers.FloatField()
    total_cost_usd = serializers.DecimalField(max_digits=10, decimal_places=6)
    avg_quality_score = serializers.FloatField(allow_null=True)
    last_used = serializers.DateTimeField()


class ModelSelectionRequestSerializer(serializers.Serializer):
    """Request serializer for model selection endpoint"""
    task_type = serializers.ChoiceField(choices=[
        'job_parsing', 'cv_generation', 'embedding', 'similarity_search'
    ])
    complexity_score = serializers.FloatField(min_value=0.0, max_value=1.0, required=False)
    user_budget = serializers.DecimalField(max_digits=10, decimal_places=6, required=False)
    strategy = serializers.ChoiceField(
        choices=['cost_optimized', 'balanced', 'performance_first'],
        required=False
    )


class ModelSelectionResponseSerializer(serializers.Serializer):
    """Response serializer for model selection endpoint"""
    selected_model = serializers.CharField()
    reasoning = serializers.CharField()
    estimated_cost_usd = serializers.DecimalField(max_digits=10, decimal_places=6)
    fallback_models = serializers.ListField(child=serializers.CharField())


class SystemHealthSerializer(serializers.Serializer):
    """Overall system health status"""
    healthy_models = serializers.IntegerField()
    unhealthy_models = serializers.IntegerField()
    circuit_breakers_open = serializers.IntegerField()
    total_cost_today = serializers.DecimalField(max_digits=10, decimal_places=6)
    avg_response_time_ms = serializers.FloatField()
    success_rate = serializers.FloatField()