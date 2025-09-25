"""
DRF API views for LLM services management.
"""

from django.db.models import Avg, Sum, Count, Q, Max
from django.utils import timezone
from datetime import timedelta, date
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from .models import (
    ModelPerformanceMetric,
    EnhancedArtifact,
    ArtifactChunk,
    JobDescriptionEmbedding,
    ModelCostTracking,
    CircuitBreakerState
)
from .serializers import (
    ModelPerformanceMetricSerializer,
    CircuitBreakerStateSerializer,
    ModelCostTrackingSerializer,
    JobDescriptionEmbeddingSerializer,
    EnhancedArtifactSerializer,
    ArtifactChunkSerializer,
    ModelStatsSerializer,
    ModelSelectionRequestSerializer,
    ModelSelectionResponseSerializer,
    SystemHealthSerializer
)
from .services.enhanced_llm_service import EnhancedLLMService
from .services.model_registry import ModelRegistry


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ModelPerformanceMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing model performance metrics.
    """
    serializer_class = ModelPerformanceMetricSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['model_name', 'task_type', 'success', 'selection_strategy']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = ModelPerformanceMetric.objects.select_related('user')

        # Filter by user if not staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        # Date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get performance summary statistics"""
        queryset = self.get_queryset()

        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        today_metrics = queryset.filter(created_at__date=today)
        yesterday_metrics = queryset.filter(created_at__date=yesterday)

        summary_data = {
            'today': {
                'total_requests': today_metrics.count(),
                'success_rate': self._calculate_success_rate(today_metrics),
                'avg_cost': today_metrics.aggregate(avg=Avg('cost_usd'))['avg'] or 0,
                'total_cost': today_metrics.aggregate(sum=Sum('cost_usd'))['sum'] or 0,
            },
            'yesterday': {
                'total_requests': yesterday_metrics.count(),
                'success_rate': self._calculate_success_rate(yesterday_metrics),
                'avg_cost': yesterday_metrics.aggregate(avg=Avg('cost_usd'))['avg'] or 0,
                'total_cost': yesterday_metrics.aggregate(sum=Sum('cost_usd'))['sum'] or 0,
            }
        }

        return Response(summary_data)

    def _calculate_success_rate(self, queryset):
        total = queryset.count()
        if total == 0:
            return 0.0
        successful = queryset.filter(success=True).count()
        return (successful / total) * 100


class CircuitBreakerStateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing circuit breaker states.
    """
    queryset = CircuitBreakerState.objects.all()
    serializer_class = CircuitBreakerStateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'model_name'

    @action(detail=True, methods=['post'])
    def reset(self, request, model_name=None):
        """Reset a circuit breaker"""
        try:
            breaker = self.get_object()
            breaker.record_success()
            return Response({
                'message': f'Circuit breaker for {model_name} has been reset',
                'new_state': breaker.state
            })
        except CircuitBreakerState.DoesNotExist:
            return Response(
                {'error': 'Circuit breaker not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def health_status(self, request):
        """Get overall health status of all models"""
        breakers = self.get_queryset()

        health_data = {
            'total_models': breakers.count(),
            'healthy_models': breakers.filter(state='closed').count(),
            'unhealthy_models': breakers.exclude(state='closed').count(),
            'models_by_state': {
                state_choice[0]: breakers.filter(state=state_choice[0]).count()
                for state_choice in CircuitBreakerState.STATE_CHOICES
            },
            'recent_failures': list(breakers.filter(
                last_failure__gte=timezone.now() - timedelta(hours=24)
            ).values('model_name', 'failure_count', 'last_failure', 'state'))
        }

        return Response(health_data)


class ModelCostTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing cost tracking data.
    """
    serializer_class = ModelCostTrackingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['model_name', 'date']
    ordering = ['-date']

    def get_queryset(self):
        queryset = ModelCostTracking.objects.select_related('user')

        # Filter by user if not staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly cost summary"""
        queryset = self.get_queryset()
        current_month = date.today().replace(day=1)

        monthly_data = queryset.filter(
            date__gte=current_month
        ).values('model_name').annotate(
            total_cost=Sum('total_cost_usd'),
            total_generations=Sum('generation_count'),
            avg_cost_per_generation=Avg('avg_cost_per_generation')
        ).order_by('-total_cost')

        return Response({
            'month': current_month.strftime('%Y-%m'),
            'models': list(monthly_data)
        })


class JobDescriptionEmbeddingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing job description embeddings.
    """
    serializer_class = JobDescriptionEmbeddingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['model_used', 'company_name']
    ordering = ['-last_accessed']

    def get_queryset(self):
        queryset = JobDescriptionEmbedding.objects.select_related('user')

        # Filter by user if not staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    @action(detail=False, methods=['get'])
    def cache_stats(self, request):
        """Get embedding cache statistics"""
        queryset = self.get_queryset()

        stats = {
            'total_embeddings': queryset.count(),
            'unique_companies': queryset.values('company_name').distinct().count(),
            'total_access_count': queryset.aggregate(sum=Sum('access_count'))['sum'] or 0,
            'cache_hit_rate': self._calculate_cache_hit_rate(queryset),
            'most_accessed': list(queryset.order_by('-access_count')[:5].values(
                'role_title', 'company_name', 'access_count'
            )),
            'recent_embeddings': list(queryset.order_by('-created_at')[:5].values(
                'role_title', 'company_name', 'created_at'
            ))
        }

        return Response(stats)

    def _calculate_cache_hit_rate(self, queryset):
        # Simplified cache hit rate calculation
        # In reality, you'd need to track cache misses separately
        total_access = queryset.aggregate(sum=Sum('access_count'))['sum'] or 0
        total_embeddings = queryset.count()

        if total_embeddings == 0:
            return 0.0

        return min(100.0, (total_access / total_embeddings) * 10)


class EnhancedArtifactViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing enhanced artifacts.
    """
    serializer_class = EnhancedArtifactSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['content_type', 'embedding_model', 'processing_strategy']
    ordering = ['-updated_at']

    def get_queryset(self):
        queryset = EnhancedArtifact.objects.select_related('user').prefetch_related('chunks')

        # Filter by user if not staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        """Get chunks for a specific artifact"""
        artifact = self.get_object()
        chunks = ArtifactChunk.objects.filter(artifact=artifact).order_by('chunk_index')
        serializer = ArtifactChunkSerializer(chunks, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def model_stats(request):
    """
    Get aggregated statistics for all models.
    """
    cache_key = f'model_stats_{request.user.id if not request.user.is_staff else "all"}'
    cached_data = cache.get(cache_key)

    if cached_data:
        return Response(cached_data)

    queryset = ModelPerformanceMetric.objects.all()
    if not request.user.is_staff:
        queryset = queryset.filter(user=request.user)

    # Aggregate by model
    model_stats = queryset.values('model_name').annotate(
        total_requests=Count('id'),
        success_count=Count('id', filter=Q(success=True)),
        avg_processing_time=Avg('processing_time_ms'),
        total_cost=Sum('cost_usd'),
        avg_quality_score=Avg('quality_score'),
        last_used=Max('created_at')
    ).order_by('-total_requests')

    # Calculate success rates
    for stat in model_stats:
        stat['success_rate'] = (stat['success_count'] / stat['total_requests']) * 100 if stat['total_requests'] > 0 else 0
        del stat['success_count']  # Remove intermediate field

    serializer = ModelStatsSerializer(model_stats, many=True)

    # Cache for 5 minutes
    cache.set(cache_key, serializer.data, 300)

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def select_model(request):
    """
    Select the best model for a given task.
    """
    serializer = ModelSelectionRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        llm_service = EnhancedLLMService()
        model_registry = ModelRegistry()

        # Get selection parameters
        task_type = serializer.validated_data['task_type']
        complexity_score = serializer.validated_data.get('complexity_score', 0.5)
        user_budget = serializer.validated_data.get('user_budget')
        strategy = serializer.validated_data.get('strategy', 'balanced')

        # Select model
        selected_model, reasoning = llm_service._select_model_for_task(
            task_type=task_type,
            complexity_score=complexity_score,
            user_id=request.user.id,
            strategy=strategy
        )

        # Get model info for cost estimation
        model_info = model_registry.get_model_config(selected_model)
        estimated_cost = model_info.get('input_cost_per_token', 0) * 1000  # Estimate for 1k tokens

        # Get fallback models
        all_models = model_registry.get_models_by_criteria(
            task_type=task_type,
            max_cost_per_token=user_budget if user_budget else float('inf')
        )
        fallback_models = [m for m in all_models if m != selected_model][:3]

        response_data = {
            'selected_model': selected_model,
            'reasoning': reasoning,
            'estimated_cost_usd': estimated_cost,
            'fallback_models': fallback_models
        }

        response_serializer = ModelSelectionResponseSerializer(response_data)
        return Response(response_serializer.data)

    except Exception as e:
        return Response(
            {'error': f'Model selection failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_health(request):
    """
    Get overall system health status.
    """
    cache_key = 'system_health'
    cached_data = cache.get(cache_key)

    if cached_data:
        return Response(cached_data)

    try:
        # Circuit breaker health
        breakers = CircuitBreakerState.objects.all()
        healthy_models = breakers.filter(state='closed').count()
        unhealthy_models = breakers.exclude(state='closed').count()
        circuit_breakers_open = breakers.filter(state='open').count()

        # Today's costs and performance
        today = timezone.now().date()
        today_metrics = ModelPerformanceMetric.objects.filter(created_at__date=today)

        total_cost_today = today_metrics.aggregate(sum=Sum('cost_usd'))['sum'] or 0
        avg_response_time = today_metrics.aggregate(avg=Avg('processing_time_ms'))['avg'] or 0

        # Success rate calculation
        total_requests = today_metrics.count()
        successful_requests = today_metrics.filter(success=True).count()
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 100

        health_data = {
            'healthy_models': healthy_models,
            'unhealthy_models': unhealthy_models,
            'circuit_breakers_open': circuit_breakers_open,
            'total_cost_today': total_cost_today,
            'avg_response_time_ms': avg_response_time,
            'success_rate': success_rate
        }

        serializer = SystemHealthSerializer(health_data)

        # Cache for 1 minute
        cache.set(cache_key, serializer.data, 60)

        return Response(serializer.data)

    except Exception as e:
        return Response(
            {'error': f'Failed to get system health: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_models(request):
    """
    Get list of available models and their configurations.
    """
    try:
        model_registry = ModelRegistry()
        models = model_registry.list_available_models()

        # Add current status from circuit breakers
        breakers = {cb.model_name: cb for cb in CircuitBreakerState.objects.all()}

        for model_name, config in models.items():
            breaker = breakers.get(model_name)
            config['circuit_breaker_status'] = breaker.state if breaker else 'unknown'
            config['is_available'] = breaker.state == 'closed' if breaker else True

        return Response(models)

    except Exception as e:
        return Response(
            {'error': f'Failed to get available models: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )