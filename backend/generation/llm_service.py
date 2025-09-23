"""
LLM service for CV generation using OpenAI and Anthropic APIs.
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional
from django.conf import settings
import openai
import anthropic
from jinja2 import Template

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM providers."""

    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None

        # Initialize OpenAI
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        # Initialize Anthropic
        if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(
                api_key=settings.ANTHROPIC_API_KEY
            )

    def parse_job_description(self, job_description: str, company_name: str = "", role_title: str = "") -> Dict[str, Any]:
        """Parse job description and extract structured information."""

        prompt = f"""
        Parse this job description and extract structured information:

        Company: {company_name}
        Role: {role_title}
        Job Description:
        {job_description}

        Extract the following information and return as JSON:
        1. role_title: The job title/position
        2. seniority_level: junior, mid, senior, lead, principal, etc.
        3. company_info: company name, industry, size if mentioned
        4. must_have_skills: List of required skills and technologies
        5. nice_to_have_skills: List of preferred skills
        6. key_responsibilities: Top 5 main responsibilities
        7. company_values: Keywords related to company culture/values
        8. experience_requirements: Years of experience, education requirements
        9. confidence_score: Your confidence in the extraction (0-1)

        Return only valid JSON, no additional text.
        """

        try:
            # Try OpenAI first
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a job description parser. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                content = response.choices[0].message.content
                return json.loads(content)

            # Fallback to Anthropic
            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                content = response.content[0].text
                return json.loads(content)

            else:
                logger.error("No LLM API keys configured")
                return {"error": "No LLM service available"}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {"error": "Failed to parse job description"}
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return {"error": str(e)}

    def generate_cv_content(self, job_data: Dict[str, Any], artifacts: List[Dict[str, Any]],
                           preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate CV content based on job requirements and user artifacts."""

        if preferences is None:
            preferences = {}

        # Build the prompt using Jinja2 template
        template_str = """
You are a professional CV writer specializing in creating targeted, ATS-optimized resumes.

Job Requirements:
Company: {{ job_data.company_info.name if job_data.company_info else 'Not specified' }}
Role: {{ job_data.role_title }}
Seniority: {{ job_data.seniority_level }}
Key Requirements: {{ job_data.must_have_skills | join(", ") }}
Nice-to-Have: {{ job_data.nice_to_have_skills | join(", ") }}
Key Responsibilities: {{ job_data.key_responsibilities | join("; ") }}
Company Values: {{ job_data.company_values | join(", ") }}

User Background (Top 5 Most Relevant Artifacts):
{% for artifact in artifacts[:5] %}
Artifact {{ loop.index }}:
- Title: {{ artifact.title }}
- Type: {{ artifact.artifact_type }}
- Description: {{ artifact.description }}
- Technologies: {{ artifact.technologies | join(", ") }}
- Duration: {{ artifact.start_date }} to {{ artifact.end_date or "Present" }}
- Impact/Achievements: {{ artifact.achievements or "Not specified" }}
- Evidence Links: {{ artifact.evidence_links | length }} supporting materials
- Relevance Score: {{ artifact.relevance_score or "N/A" }}/10

{% endfor %}

Generation Preferences:
- Tone: {{ preferences.tone or "professional" }}
- Length: {{ preferences.length or "balanced" }}
- Focus Areas: {{ preferences.focus_areas | join(", ") if preferences.focus_areas else "general" }}

Generate a professional CV with the following structure. Return as JSON:

{
  "professional_summary": "2-3 sentence summary highlighting most relevant experience",
  "key_skills": ["skill1", "skill2", ...],
  "experience": [
    {
      "title": "Job title",
      "organization": "Company/Organization name",
      "duration": "Start - End date",
      "achievements": ["Achievement 1 with metrics", "Achievement 2", ...],
      "technologies_used": ["tech1", "tech2", ...],
      "evidence_references": ["link1", "link2", ...]
    }
  ],
  "projects": [
    {
      "name": "Project name",
      "description": "Brief description",
      "technologies": ["tech1", "tech2", ...],
      "evidence_url": "link_to_evidence",
      "impact_metrics": "Quantified impact if available"
    }
  ],
  "education": [
    {
      "degree": "Degree name",
      "institution": "School name",
      "year": "Graduation year",
      "details": "Relevant coursework or achievements"
    }
  ],
  "certifications": [
    {
      "name": "Certification name",
      "issuer": "Issuing organization",
      "date": "Date obtained",
      "credential_id": "ID if available"
    }
  ]
}

Requirements:
1. Professional summary should be 2-3 sentences max
2. Key skills should prioritize job requirements while staying authentic
3. Use active voice and strong action verbs
4. Include specific metrics and impacts where available
5. Tailor language to match job requirements
6. NO fabricated information - all content must be grounded in user artifacts
7. Maximum 2 pages worth of content

Return only valid JSON, no additional text.
        """

        template = Template(template_str)
        prompt = template.render(
            job_data=job_data,
            artifacts=artifacts,
            preferences=preferences
        )

        try:
            start_time = time.time()

            # Try GPT-4 for higher quality
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a professional CV writer. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                content = response.choices[0].message.content
                generation_time = int((time.time() - start_time) * 1000)

                parsed_content = json.loads(content)
                return {
                    "content": parsed_content,
                    "model_used": "gpt-4",
                    "generation_time_ms": generation_time,
                    "token_usage": response.usage.total_tokens if hasattr(response, 'usage') else None
                }

            # Fallback to Claude
            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                content = response.content[0].text
                generation_time = int((time.time() - start_time) * 1000)

                parsed_content = json.loads(content)
                return {
                    "content": parsed_content,
                    "model_used": "claude-3-sonnet",
                    "generation_time_ms": generation_time,
                    "token_usage": response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else None
                }

            else:
                return {"error": "No LLM service available"}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse CV generation response as JSON: {e}")
            return {"error": "Failed to generate valid CV content"}
        except Exception as e:
            logger.error(f"LLM API error during CV generation: {e}")
            return {"error": str(e)}

    def rank_artifacts_by_relevance(self, artifacts: List[Dict[str, Any]],
                                  job_requirements: List[str]) -> List[Dict[str, Any]]:
        """Rank artifacts by relevance to job requirements using semantic similarity."""

        if not artifacts or not job_requirements:
            return artifacts

        # Simple keyword-based relevance scoring for now
        # In production, this could use embedding similarity
        job_keywords = set()
        for req in job_requirements:
            job_keywords.update(req.lower().split())

        for artifact in artifacts:
            relevance_score = 0

            # Check title
            title_words = set(artifact.get('title', '').lower().split())
            relevance_score += len(title_words.intersection(job_keywords)) * 2

            # Check description
            desc_words = set(artifact.get('description', '').lower().split())
            relevance_score += len(desc_words.intersection(job_keywords))

            # Check technologies
            tech_words = set()
            for tech in artifact.get('technologies', []):
                tech_words.update(tech.lower().split())
            relevance_score += len(tech_words.intersection(job_keywords)) * 3

            # Normalize score (0-10)
            max_possible_score = len(job_keywords) * 6  # 2+1+3 from above
            artifact['relevance_score'] = min(10, int((relevance_score / max_possible_score) * 10)) if max_possible_score > 0 else 0

        # Sort by relevance score
        return sorted(artifacts, key=lambda x: x.get('relevance_score', 0), reverse=True)