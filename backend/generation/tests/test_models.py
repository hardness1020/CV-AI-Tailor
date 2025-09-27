"""
Unit tests for generation app models
"""

import uuid
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from generation.models import (
    JobDescription, GeneratedDocument, CVTemplate,
    GenerationFeedback, SkillsTaxonomy
)

User = get_user_model()


class JobDescriptionModelTests(TestCase):
    """Test cases for JobDescription model"""

    def test_job_description_creation(self):
        """Test basic job description creation"""
        job_desc = JobDescription.objects.create(
            content_hash='abc123',
            raw_content='Software Engineer position at TechCorp',
            company_name='TechCorp',
            role_title='Software Engineer',
            parsing_confidence=0.9
        )

        self.assertEqual(job_desc.content_hash, 'abc123')
        self.assertEqual(job_desc.company_name, 'TechCorp')
        self.assertEqual(job_desc.parsing_confidence, 0.9)

    def test_get_or_create_from_content(self):
        """Test get_or_create_from_content method"""
        content = 'Looking for a Python developer'

        # First call should create
        job_desc1, created1 = JobDescription.get_or_create_from_content(
            content, 'TechCorp', 'Python Developer'
        )
        self.assertTrue(created1)
        self.assertEqual(job_desc1.company_name, 'TechCorp')

        # Second call should retrieve existing
        job_desc2, created2 = JobDescription.get_or_create_from_content(
            content, 'TechCorp', 'Python Developer'
        )
        self.assertFalse(created2)
        self.assertEqual(job_desc1.id, job_desc2.id)

    def test_job_description_string_representation(self):
        """Test __str__ method"""
        job_desc = JobDescription.objects.create(
            content_hash='abc123',
            raw_content='Test content',
            company_name='TechCorp',
            role_title='Engineer'
        )
        expected = 'Engineer at TechCorp'
        self.assertEqual(str(job_desc), expected)

        # Test fallback when no title/company
        job_desc2 = JobDescription.objects.create(
            content_hash='def456',
            raw_content='Test content'
        )
        self.assertIn('Job', str(job_desc2))


class GeneratedDocumentModelTests(TestCase):
    """Test cases for GeneratedDocument model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.job_desc = JobDescription.objects.create(
            content_hash='abc123',
            raw_content='Test job description'
        )

    def test_generated_document_creation(self):
        """Test basic generated document creation"""
        expires_at = timezone.now() + timedelta(days=90)

        doc = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            job_description=self.job_desc,
            expires_at=expires_at
        )

        self.assertEqual(doc.user, self.user)
        self.assertEqual(doc.document_type, 'cv')
        self.assertEqual(doc.status, 'processing')  # Default status
        self.assertIsInstance(doc.id, uuid.UUID)

    def test_generated_document_with_content(self):
        """Test generated document with CV content"""
        content = {
            'professional_summary': 'Experienced developer',
            'key_skills': ['Python', 'Django'],
            'experience': [
                {
                    'title': 'Software Engineer',
                    'organization': 'TechCorp',
                    'achievements': ['Built web apps']
                }
            ]
        }

        doc = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123',
            content=content,
            status='completed'
        )

        self.assertEqual(doc.content['professional_summary'], 'Experienced developer')
        self.assertEqual(len(doc.content['key_skills']), 2)
        self.assertEqual(doc.status, 'completed')

    def test_document_ordering(self):
        """Test document ordering by created_at"""
        doc1 = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123'
        )
        doc2 = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='def456'
        )

        docs = GeneratedDocument.objects.all()
        self.assertEqual(docs[0], doc2)  # Most recent first


class CVTemplateModelTests(TestCase):
    """Test cases for CVTemplate model"""

    def test_cv_template_creation(self):
        """Test CV template creation"""
        template = CVTemplate.objects.create(
            name='Modern Professional',
            category='modern',
            description='A modern professional template',
            template_config={'font': 'Arial', 'color': '#000'},
            prompt_template='Generate CV with: {requirements}',
            is_premium=False,
            is_active=True
        )

        self.assertEqual(template.name, 'Modern Professional')
        self.assertEqual(template.category, 'modern')
        self.assertFalse(template.is_premium)
        self.assertTrue(template.is_active)

    def test_template_string_representation(self):
        """Test template __str__ method"""
        template = CVTemplate.objects.create(
            name='Classic',
            category='classic',
            description='Classic template'
        )
        expected = 'Classic (classic)'
        self.assertEqual(str(template), expected)


class GenerationFeedbackModelTests(TestCase):
    """Test cases for GenerationFeedback model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.generation = GeneratedDocument.objects.create(
            user=self.user,
            document_type='cv',
            job_description_hash='abc123'
        )

    def test_feedback_creation(self):
        """Test feedback creation"""
        feedback = GenerationFeedback.objects.create(
            generation=self.generation,
            feedback_type='rating',
            feedback_data={'rating': 8, 'comment': 'Good quality'}
        )

        self.assertEqual(feedback.generation, self.generation)
        self.assertEqual(feedback.feedback_type, 'rating')
        self.assertEqual(feedback.feedback_data['rating'], 8)


class SkillsTaxonomyModelTests(TestCase):
    """Test cases for SkillsTaxonomy model"""

    def test_skills_taxonomy_creation(self):
        """Test skills taxonomy creation"""
        skill = SkillsTaxonomy.objects.create(
            skill_name='Python',
            category='programming',
            aliases=['Python3', 'py'],
            related_skills=['Django', 'Flask'],
            popularity_score=95
        )

        self.assertEqual(skill.skill_name, 'Python')
        self.assertEqual(skill.category, 'programming')
        self.assertEqual(len(skill.aliases), 2)
        self.assertEqual(skill.popularity_score, 95)