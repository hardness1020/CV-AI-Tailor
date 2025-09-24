"""
Celery tasks for artifact processing.
"""

import os
import requests
import logging
from celery import shared_task
from django.core.files.storage import default_storage
from django.utils import timezone
from PyPDF2 import PdfReader
from .models import Artifact, ArtifactProcessingJob, EvidenceLink
import json

logger = logging.getLogger(__name__)


@shared_task
def process_artifact_upload(artifact_id, processing_job_id):
    """
    Process uploaded artifact: extract metadata, validate links, etc.
    """
    try:
        artifact = Artifact.objects.get(id=artifact_id)
        processing_job = ArtifactProcessingJob.objects.get(id=processing_job_id)

        # Update status
        processing_job.status = 'processing'
        processing_job.progress_percentage = 10
        processing_job.save()

        # Extract metadata from any PDF files
        extracted_metadata = {}
        for evidence_link in artifact.evidence_links.all():
            if evidence_link.file_path and evidence_link.mime_type == 'application/pdf':
                try:
                    pdf_metadata = extract_pdf_metadata(evidence_link.file_path)
                    extracted_metadata.update(pdf_metadata)
                    processing_job.progress_percentage = 30
                    processing_job.save()
                except Exception as e:
                    logger.error(f"Error extracting PDF metadata: {e}")

        # Validate evidence links
        validation_results = {}
        evidence_links = artifact.evidence_links.all()
        total_links = len(evidence_links)

        for i, evidence_link in enumerate(evidence_links):
            try:
                validation_result = validate_evidence_link(evidence_link)
                validation_results[evidence_link.id] = validation_result

                # Update progress
                progress = 30 + int((i + 1) / total_links * 50)
                processing_job.progress_percentage = progress
                processing_job.save()

            except Exception as e:
                logger.error(f"Error validating evidence link {evidence_link.id}: {e}")
                validation_results[evidence_link.id] = {
                    'status': 'error',
                    'error': str(e)
                }

        # Analyze GitHub repositories if any
        github_metadata = {}
        for evidence_link in evidence_links:
            if evidence_link.link_type == 'github' and 'github.com' in evidence_link.url:
                try:
                    repo_metadata = analyze_github_repository(evidence_link.url)
                    github_metadata[evidence_link.id] = repo_metadata
                except Exception as e:
                    logger.error(f"Error analyzing GitHub repo: {e}")

        # Update artifact with extracted metadata
        artifact.extracted_metadata = {
            'pdf_metadata': extracted_metadata,
            'github_metadata': github_metadata,
            'processing_timestamp': timezone.now().isoformat()
        }
        artifact.save()

        # Complete processing
        processing_job.status = 'completed'
        processing_job.progress_percentage = 100
        processing_job.metadata_extracted = extracted_metadata
        processing_job.evidence_validation_results = validation_results
        processing_job.completed_at = timezone.now()
        processing_job.save()

        logger.info(f"Successfully processed artifact {artifact_id}")

    except Exception as e:
        logger.error(f"Error processing artifact {artifact_id}: {e}")
        try:
            processing_job = ArtifactProcessingJob.objects.get(id=processing_job_id)
            processing_job.status = 'failed'
            processing_job.error_message = str(e)
            processing_job.save()
        except:
            pass


def extract_pdf_metadata(file_path):
    """Extract metadata from PDF file."""
    try:
        if default_storage.exists(file_path):
            with default_storage.open(file_path, 'rb') as file:
                reader = PdfReader(file)
                metadata = reader.metadata

                extracted = {
                    'title': metadata.get('/Title', ''),
                    'author': metadata.get('/Author', ''),
                    'subject': metadata.get('/Subject', ''),
                    'creator': metadata.get('/Creator', ''),
                    'producer': metadata.get('/Producer', ''),
                    'creation_date': str(metadata.get('/CreationDate', '')),
                    'modification_date': str(metadata.get('/ModDate', '')),
                    'page_count': len(reader.pages)
                }

                # Extract text from first page for analysis
                if reader.pages:
                    first_page_text = reader.pages[0].extract_text()
                    extracted['first_page_text'] = first_page_text[:1000]  # First 1000 chars

                return extracted
    except Exception as e:
        logger.error(f"Error extracting PDF metadata from {file_path}: {e}")
    return {}


def validate_evidence_link(evidence_link):
    """Validate that an evidence link is accessible."""
    try:
        response = requests.head(evidence_link.url, timeout=10, allow_redirects=True)
        is_accessible = response.status_code == 200

        # Update evidence link
        evidence_link.is_accessible = is_accessible
        evidence_link.last_validated = timezone.now()
        evidence_link.validation_metadata = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'final_url': response.url
        }
        evidence_link.save()

        return {
            'status': 'success' if is_accessible else 'failed',
            'status_code': response.status_code,
            'accessible': is_accessible
        }

    except requests.RequestException as e:
        evidence_link.is_accessible = False
        evidence_link.last_validated = timezone.now()
        evidence_link.validation_metadata = {
            'error': str(e)
        }
        evidence_link.save()

        return {
            'status': 'error',
            'error': str(e),
            'accessible': False
        }


def analyze_github_repository(github_url):
    """Analyze GitHub repository and extract metadata."""
    try:
        # Parse GitHub URL
        parts = github_url.strip('/').split('/')
        if len(parts) >= 2:
            owner = parts[-2]
            repo = parts[-1]

            # GitHub API call (requires token for higher rate limits)
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {}

            # Add GitHub token if available
            github_token = os.environ.get('GITHUB_TOKEN')
            if github_token:
                headers['Authorization'] = f"token {github_token}"

            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                repo_data = response.json()

                # Get languages
                languages_url = repo_data.get('languages_url')
                languages = {}
                if languages_url:
                    lang_response = requests.get(languages_url, headers=headers, timeout=10)
                    if lang_response.status_code == 200:
                        languages = lang_response.json()

                # Get recent commits
                commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
                commits = []
                commits_response = requests.get(f"{commits_url}?per_page=5", headers=headers, timeout=10)
                if commits_response.status_code == 200:
                    commits_data = commits_response.json()
                    commits = [
                        {
                            'sha': commit['sha'][:7],
                            'message': commit['commit']['message'],
                            'date': commit['commit']['author']['date'],
                            'author': commit['commit']['author']['name']
                        }
                        for commit in commits_data
                    ]

                return {
                    'name': repo_data.get('name'),
                    'description': repo_data.get('description'),
                    'language': repo_data.get('language'),
                    'languages': languages,
                    'stars': repo_data.get('stargazers_count', 0),
                    'forks': repo_data.get('forks_count', 0),
                    'created_at': repo_data.get('created_at'),
                    'updated_at': repo_data.get('updated_at'),
                    'topics': repo_data.get('topics', []),
                    'recent_commits': commits,
                    'default_branch': repo_data.get('default_branch'),
                    'size': repo_data.get('size'),
                    'open_issues': repo_data.get('open_issues_count', 0)
                }

    except Exception as e:
        logger.error(f"Error analyzing GitHub repository {github_url}: {e}")
        return {'error': str(e)}


@shared_task
def cleanup_old_uploaded_files():
    """Cleanup uploaded files older than 24 hours."""
    from datetime import timedelta
    from .models import UploadedFile

    cutoff_time = timezone.now() - timedelta(hours=24)
    old_files = UploadedFile.objects.filter(created_at__lt=cutoff_time)

    deleted_count = 0
    for uploaded_file in old_files:
        try:
            # Delete file from storage
            if uploaded_file.file:
                default_storage.delete(uploaded_file.file.name)

            # Delete database record
            uploaded_file.delete()
            deleted_count += 1

        except Exception as e:
            logger.error(f"Error deleting old file {uploaded_file.id}: {e}")

    logger.info(f"Cleaned up {deleted_count} old uploaded files")
    return deleted_count