import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
# from django.contrib.postgres.fields import ArrayField

User = get_user_model()


class Artifact(models.Model):
    """Main artifact model representing user's work artifacts."""

    ARTIFACT_TYPES = [
        ('project', 'Project'),
        ('publication', 'Publication'),
        ('presentation', 'Presentation'),
        ('certification', 'Certification'),
        ('experience', 'Work Experience'),
        ('education', 'Education'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artifacts')
    title = models.CharField(max_length=255)
    description = models.TextField()
    artifact_type = models.CharField(max_length=20, choices=ARTIFACT_TYPES, default='project')

    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Skills and metadata
    technologies = models.JSONField(default=list, blank=True)
    collaborators = models.JSONField(default=list, blank=True)

    # Auto-extracted metadata
    extracted_metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.user.email})"


class EvidenceLink(models.Model):
    """Evidence links associated with artifacts."""

    LINK_TYPES = [
        ('github', 'GitHub Repository'),
        ('live_app', 'Live Application'),
        ('document', 'Document/PDF'),
        ('website', 'Website'),
        ('portfolio', 'Portfolio'),
        ('other', 'Other'),
    ]

    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE, related_name='evidence_links')
    url = models.URLField(validators=[URLValidator()])
    link_type = models.CharField(max_length=20, choices=LINK_TYPES)
    description = models.CharField(max_length=255, blank=True)

    # File-specific fields (for uploaded files)
    file_path = models.TextField(blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)

    # Validation metadata
    validation_metadata = models.JSONField(default=dict, blank=True)
    last_validated = models.DateTimeField(null=True, blank=True)
    is_accessible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.description or self.url} ({self.artifact.title})"


class ArtifactProcessingJob(models.Model):
    """Track artifact processing status for async operations."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE, related_name='processing_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    # Processing results
    metadata_extracted = models.JSONField(default=dict, blank=True)
    evidence_validation_results = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Processing {self.artifact.title} - {self.status}"


class UploadedFile(models.Model):
    """Temporary storage for uploaded files during processing."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    mime_type = models.CharField(max_length=100)

    # Processing status
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Auto-cleanup after 24 hours
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.original_filename} ({self.user.email})"