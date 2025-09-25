"""
Django admin interface for LLM services.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ModelPerformanceMetric,
    EnhancedArtifact,
    ArtifactChunk,
    JobDescriptionEmbedding,
    ModelCostTracking,
    CircuitBreakerState
)


@admin.register(ModelPerformanceMetric)
class ModelPerformanceMetricAdmin(admin.ModelAdmin):
    list_display = [
        'model_name', 'task_type', 'processing_time_ms', 'cost_usd',
        'quality_score', 'success', 'created_at'
    ]
    list_filter = [
        'model_name', 'task_type', 'success', 'selection_strategy',
        'fallback_used', 'created_at'
    ]
    search_fields = ['model_name', 'user__email']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'model_name', 'task_type', 'user')
        }),
        ('Performance Metrics', {
            'fields': ('processing_time_ms', 'tokens_used', 'cost_usd', 'quality_score', 'success')
        }),
        ('Context', {
            'fields': ('complexity_score', 'selection_strategy', 'fallback_used')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(EnhancedArtifact)
class EnhancedArtifactAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'content_type', 'user', 'total_chunks',
        'embedding_model', 'created_at'
    ]
    list_filter = [
        'content_type', 'embedding_model', 'processing_strategy',
        'created_at', 'last_embedding_update'
    ]
    search_fields = ['title', 'user__email', 'raw_content']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_embedding_update']
    raw_id_fields = ['user']

    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'title', 'content_type', 'original_artifact_id')
        }),
        ('Content', {
            'fields': ('raw_content', 'processed_content'),
            'classes': ('collapse',)
        }),
        ('Embeddings', {
            'fields': ('embedding_model', 'embedding_dimensions', 'embedding_cost_usd')
        }),
        ('Processing', {
            'fields': ('langchain_version', 'processing_strategy', 'total_chunks',
                      'processing_time_ms', 'llm_model_used')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_embedding_update')
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


class ArtifactChunkInline(admin.TabularInline):
    model = ArtifactChunk
    extra = 0
    readonly_fields = ['id', 'content_hash', 'created_at']
    fields = ['chunk_index', 'content', 'model_used', 'tokens_used', 'processing_cost_usd']


@admin.register(ArtifactChunk)
class ArtifactChunkAdmin(admin.ModelAdmin):
    list_display = [
        'artifact_title', 'chunk_index', 'model_used',
        'tokens_used', 'processing_cost_usd', 'created_at'
    ]
    list_filter = ['model_used', 'created_at']
    search_fields = ['artifact__title', 'content']
    readonly_fields = ['id', 'content_hash', 'created_at']
    raw_id_fields = ['artifact']

    def artifact_title(self, obj):
        return obj.artifact.title
    artifact_title.short_description = 'Artifact Title'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('artifact')


@admin.register(JobDescriptionEmbedding)
class JobDescriptionEmbeddingAdmin(admin.ModelAdmin):
    list_display = [
        'role_title', 'company_name', 'user', 'model_used',
        'access_count', 'cost_usd', 'created_at'
    ]
    list_filter = ['model_used', 'dimensions', 'created_at', 'last_accessed']
    search_fields = ['role_title', 'company_name', 'user__email']
    readonly_fields = ['id', 'job_description_hash', 'created_at', 'last_accessed']
    raw_id_fields = ['user']

    fieldsets = (
        ('Job Info', {
            'fields': ('id', 'user', 'role_title', 'company_name')
        }),
        ('Embedding', {
            'fields': ('job_description_hash', 'model_used', 'dimensions', 'cost_usd')
        }),
        ('Usage', {
            'fields': ('access_count', 'last_accessed', 'created_at')
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ModelCostTracking)
class ModelCostTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'model_name', 'generation_count',
        'total_cost_usd', 'avg_cost_per_generation'
    ]
    list_filter = ['date', 'model_name']
    search_fields = ['user__email', 'model_name']
    date_hierarchy = 'date'
    ordering = ['-date']

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'date', 'model_name')
        }),
        ('Costs', {
            'fields': ('total_cost_usd', 'generation_count', 'avg_cost_per_generation')
        }),
        ('Tokens', {
            'fields': ('total_tokens_used', 'avg_tokens_per_generation')
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(CircuitBreakerState)
class CircuitBreakerStateAdmin(admin.ModelAdmin):
    list_display = [
        'model_name', 'state_display', 'failure_count',
        'failure_threshold', 'last_failure', 'updated_at'
    ]
    list_filter = ['state', 'created_at', 'updated_at']
    search_fields = ['model_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['model_name']

    fieldsets = (
        ('Model Info', {
            'fields': ('model_name', 'state')
        }),
        ('Failure Tracking', {
            'fields': ('failure_count', 'failure_threshold', 'last_failure')
        }),
        ('Configuration', {
            'fields': ('timeout_duration',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

    def state_display(self, obj):
        colors = {
            'closed': 'green',
            'open': 'red',
            'half_open': 'orange'
        }
        color = colors.get(obj.state, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_state_display()
        )
    state_display.short_description = 'State'

    actions = ['reset_circuit_breakers']

    def reset_circuit_breakers(self, request, queryset):
        """Reset selected circuit breakers"""
        count = 0
        for breaker in queryset:
            breaker.record_success()
            count += 1

        self.message_user(
            request,
            f'Successfully reset {count} circuit breaker(s).'
        )
    reset_circuit_breakers.short_description = 'Reset selected circuit breakers'


# Custom admin views for analytics
class LLMServicesAdminSite(admin.AdminSite):
    site_header = "LLM Services Administration"
    site_title = "LLM Services Admin"
    index_title = "LLM Services Management"

# Register the custom admin site
llm_admin_site = LLMServicesAdminSite(name='llm_admin')