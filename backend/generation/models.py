import uuid
import hashlib
from django.db import models
from django.contrib.auth import get_user_model
# from django.contrib.postgres.fields import ArrayField

User = get_user_model()


class JobDescription(models.Model):
    """Cache for parsed job descriptions."""

    id = models.AutoField(primary_key=True)
    content_hash = models.CharField(max_length=64, unique=True)
    raw_content = models.TextField()
    parsed_data = models.JSONField(default=dict, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    role_title = models.CharField(max_length=255, blank=True)
    parsing_confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get_or_create_from_content(cls, content, company_name="", role_title=""):
        """Get or create job description from content hash."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        job_desc, created = cls.objects.get_or_create(
            content_hash=content_hash,
            defaults={
                'raw_content': content,
                'company_name': company_name,
                'role_title': role_title
            }
        )
        return job_desc, created

    def __str__(self):
        return f"{self.role_title} at {self.company_name}" if self.role_title and self.company_name else f"Job {self.id}"


class GeneratedDocument(models.Model):
    """Generated CV/Cover Letter documents."""

    DOCUMENT_TYPES = [
        ('cv', 'CV/Resume'),
        ('cover_letter', 'Cover Letter'),
    ]

    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='cv')
    job_description_hash = models.CharField(max_length=64)
    job_description = models.ForeignKey(JobDescription, on_delete=models.SET_NULL, null=True, blank=True)

    # Generation configuration
    label_ids = models.JSONField(default=list, blank=True)
    template_id = models.IntegerField(default=1)
    custom_sections = models.JSONField(default=dict, blank=True)
    generation_preferences = models.JSONField(default=dict, blank=True)

    # Generated content
    content = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    progress_percentage = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    # Processing info
    artifacts_used = models.JSONField(default=list, blank=True)
    model_version = models.CharField(max_length=50, blank=True)
    generation_time_ms = models.IntegerField(null=True, blank=True)

    # User feedback
    user_rating = models.IntegerField(null=True, blank=True)  # 1-10
    user_feedback = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_document_type_display()} for {self.user.email} - {self.status}"


class GenerationFeedback(models.Model):
    """Track user feedback on generated documents."""

    FEEDBACK_TYPES = [
        ('rating', 'Rating'),
        ('edit', 'Content Edit'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
    ]

    id = models.AutoField(primary_key=True)
    generation = models.ForeignKey(GeneratedDocument, on_delete=models.CASCADE, related_name='feedback')
    feedback_type = models.CharField(max_length=50, choices=FEEDBACK_TYPES)
    feedback_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.feedback_type} for {self.generation.id}"


class CVTemplate(models.Model):
    """CV template definitions."""

    TEMPLATE_CATEGORIES = [
        ('modern', 'Modern'),
        ('classic', 'Classic'),
        ('technical', 'Technical'),
        ('creative', 'Creative'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=TEMPLATE_CATEGORIES)
    description = models.TextField()
    preview_image_url = models.URLField(blank=True)
    template_config = models.JSONField(default=dict)
    prompt_template = models.TextField()
    is_premium = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category})"


class SkillsTaxonomy(models.Model):
    """Skills taxonomy for normalization and suggestions."""

    id = models.AutoField(primary_key=True)
    skill_name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)  # programming, framework, tool, etc.
    aliases = models.JSONField(default=list, blank=True)
    related_skills = models.JSONField(default=list, blank=True)
    popularity_score = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.skill_name

    class Meta:
        verbose_name_plural = "Skills taxonomy"