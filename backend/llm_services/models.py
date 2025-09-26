"""
Models for enhanced LLM services with pgvector support.
Implements ft-llm-002-embedding-storage.md
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

try:
    from pgvector.django import VectorField
    HAS_PGVECTOR = True
except ImportError:
    # Fallback for development without pgvector
    HAS_PGVECTOR = False
    VectorField = lambda dimensions: ArrayField(models.FloatField(), size=dimensions, default=list)

User = get_user_model()


class ModelPerformanceMetric(models.Model):
    """Track performance metrics for different AI models"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=100, db_index=True)
    task_type = models.CharField(max_length=50, choices=[
        ('job_parsing', 'Job Description Parsing'),
        ('cv_generation', 'CV Content Generation'),
        ('embedding', 'Embedding Generation'),
        ('similarity_search', 'Similarity Search'),
    ])

    # Performance metrics
    processing_time_ms = models.IntegerField()
    tokens_used = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6)
    quality_score = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('1.0'))]
    )
    success = models.BooleanField(default=True)

    # Context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    complexity_score = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('1.0'))]
    )
    selection_strategy = models.CharField(max_length=50, default='balanced')
    fallback_used = models.BooleanField(default=False)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'model_performance_metrics'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_name', 'task_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['success']),
        ]

    def __str__(self):
        return f"{self.model_name} - {self.task_type} - {self.created_at}"


class EnhancedArtifact(models.Model):
    """Enhanced artifact model with embedding support"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enhanced_artifacts')

    # Original artifact reference
    original_artifact_id = models.IntegerField(null=True, blank=True)

    # Basic info
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=50, choices=[
        ('pdf', 'PDF Document'),
        ('github', 'GitHub Repository'),
        ('linkedin', 'LinkedIn Profile'),
        ('web_profile', 'Web Profile'),
        ('markdown', 'Markdown Document'),
        ('text', 'Plain Text'),
    ])

    # Content
    raw_content = models.TextField()
    processed_content = models.JSONField(default=dict)  # Structured achievements, skills

    # Embeddings (configurable dimensions)
    content_embedding = VectorField(dimensions=1536) if HAS_PGVECTOR else ArrayField(models.FloatField(), size=1536, default=list)
    summary_embedding = VectorField(dimensions=1536) if HAS_PGVECTOR else ArrayField(models.FloatField(), size=1536, default=list)

    # Embedding metadata
    embedding_model = models.CharField(max_length=50, default='text-embedding-3-small')
    embedding_dimensions = models.IntegerField(default=1536)
    embedding_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)

    # Processing metadata
    langchain_version = models.CharField(max_length=20, default='0.2.0')
    processing_strategy = models.CharField(max_length=50, default='adaptive')
    total_chunks = models.IntegerField(default=0)
    processing_time_ms = models.IntegerField(default=0)
    llm_model_used = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_embedding_update = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'enhanced_artifacts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'content_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['embedding_model']),
        ]

    def find_similar(self, query_embedding, limit=10):
        """Find similar artifacts using vector similarity"""
        if not HAS_PGVECTOR:
            return EnhancedArtifact.objects.none()

        return EnhancedArtifact.objects.filter(
            user=self.user
        ).annotate(
            similarity=models.F('content_embedding').cosine_distance(query_embedding)
        ).order_by('similarity')[:limit]

    def __str__(self):
        return f"{self.title} ({self.content_type})"


class ArtifactChunk(models.Model):
    """Individual chunks of processed artifacts with embeddings"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artifact = models.ForeignKey(
        EnhancedArtifact, on_delete=models.CASCADE, related_name='chunks'
    )

    # Chunk info
    chunk_index = models.IntegerField()
    content = models.TextField()
    metadata = models.JSONField(default=dict)

    # Embedding
    embedding_vector = VectorField(dimensions=1536) if HAS_PGVECTOR else ArrayField(models.FloatField(), size=1536, default=list)
    content_hash = models.CharField(max_length=64)

    # Processing info
    model_used = models.CharField(max_length=50, default='text-embedding-3-small')
    tokens_used = models.IntegerField(default=0)
    processing_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0.0)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'artifact_chunks'
        ordering = ['artifact', 'chunk_index']
        unique_together = ['artifact', 'chunk_index']
        indexes = [
            models.Index(fields=['artifact', 'chunk_index']),
            models.Index(fields=['content_hash']),
        ]

    def __str__(self):
        return f"{self.artifact.title} - Chunk {self.chunk_index}"


class JobDescriptionEmbedding(models.Model):
    """Cache embeddings for job descriptions to avoid regeneration"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Job description info
    job_description_hash = models.CharField(max_length=64, unique=True)
    company_name = models.CharField(max_length=200, blank=True)
    role_title = models.CharField(max_length=200, blank=True)

    # Embedding
    embedding_vector = VectorField(dimensions=1536) if HAS_PGVECTOR else ArrayField(models.FloatField(), size=1536, default=list)

    # Processing info
    model_used = models.CharField(max_length=50, default='text-embedding-3-small')
    dimensions = models.IntegerField(default=1536)
    tokens_used = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0.0)

    # Usage tracking
    access_count = models.IntegerField(default=1)
    last_accessed = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'job_embeddings'
        ordering = ['-last_accessed']
        indexes = [
            models.Index(fields=['job_description_hash']),
            models.Index(fields=['user', 'last_accessed']),
            models.Index(fields=['created_at']),
        ]

    def update_access(self):
        """Update access tracking"""
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])

    def __str__(self):
        return f"Job Embedding: {self.role_title} at {self.company_name}"


class ModelCostTracking(models.Model):
    """Track daily cost usage by user and model"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    model_name = models.CharField(max_length=100)

    # Aggregated costs
    total_cost_usd = models.DecimalField(max_digits=10, decimal_places=6)
    generation_count = models.IntegerField()
    avg_cost_per_generation = models.DecimalField(max_digits=10, decimal_places=6)

    # Token usage
    total_tokens_used = models.BigIntegerField(default=0)
    avg_tokens_per_generation = models.IntegerField(default=0)

    class Meta:
        db_table = 'model_cost_tracking'
        ordering = ['-date', 'model_name']
        unique_together = ['user', 'date', 'model_name']
        indexes = [
            models.Index(fields=['date', 'model_name']),
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.model_name} - {self.date}"


class CircuitBreakerState(models.Model):
    """Track circuit breaker state for each model"""

    model_name = models.CharField(max_length=100, primary_key=True)
    failure_count = models.IntegerField(default=0)
    last_failure = models.DateTimeField(null=True, blank=True)
    state = models.CharField(max_length=20, choices=[
        ('closed', 'Closed'),      # Normal operation
        ('open', 'Open'),          # Circuit broken, using fallback
        ('half_open', 'Half Open'), # Testing if service recovered
    ], default='closed')

    # Configuration
    failure_threshold = models.IntegerField(default=5)
    timeout_duration = models.IntegerField(default=30)  # seconds

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'circuit_breaker_states'
        ordering = ['model_name']

    def record_failure(self):
        """Record a failure and update state if needed"""
        self.failure_count += 1
        self.last_failure = timezone.now()

        if self.failure_count >= self.failure_threshold:
            self.state = 'open'

        self.save()

    def record_success(self):
        """Record a success and reset failure count"""
        self.failure_count = 0
        self.state = 'closed'
        self.last_failure = None
        self.save()

    def should_attempt_request(self):
        """Check if we should attempt a request to this model"""
        if self.state == 'closed':
            return True
        elif self.state == 'open':
            # Check if timeout has passed
            if self.last_failure and \
               (timezone.now() - self.last_failure).seconds >= self.timeout_duration:
                self.state = 'half_open'
                self.save()
                return True
            return False
        elif self.state == 'half_open':
            return True

        return False

    def __str__(self):
        return f"{self.model_name} - {self.state} ({self.failure_count} failures)"