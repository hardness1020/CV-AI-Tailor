# CV Tailor API Integration Documentation

This document provides a comprehensive overview of the API integration between the frontend and backend systems of the CV Tailor application, including all available endpoints, data structures, and integration patterns.

## Overview

The CV Tailor API follows RESTful conventions and is organized around the following core domains:
- **Authentication & User Management**
- **Artifact Management**
- **CV/Cover Letter Generation**
- **Document Export**
- **LLM Services & Analytics**

All API endpoints are prefixed with `/api/v1/` and return JSON responses.

## Authentication System

### Endpoints
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - User authentication
- `POST /api/v1/auth/logout/` - User logout
- `POST /api/v1/auth/token/refresh/` - JWT token refresh
- `GET /api/v1/auth/profile/` - Get user profile
- `PATCH /api/v1/auth/profile/` - Update user profile
- `POST /api/v1/auth/change-password/` - Password change
- `POST /api/v1/auth/password-reset/` - Password reset request

### Google OAuth Integration
- `POST /api/v1/auth/google/` - Google Sign-In authentication
- `POST /api/v1/auth/google/link/` - Link Google account to existing user
- `POST /api/v1/auth/google/unlink/` - Unlink Google account

### Authentication Flow
- JWT tokens are used for API authentication
- Automatic token refresh on 401 responses
- Access tokens expire and are refreshed using refresh tokens
- Google OAuth provides alternative authentication method

## Artifact Management System

### Core Endpoints
- `GET /api/v1/artifacts/` - List user artifacts (with filtering/pagination)
- `POST /api/v1/artifacts/` - Create new artifact
- `GET /api/v1/artifacts/{id}/` - Get specific artifact details
- `PATCH /api/v1/artifacts/{id}/` - Update artifact
- `DELETE /api/v1/artifacts/{id}/` - Delete artifact

### File Upload & Processing
- `POST /api/v1/artifacts/{id}/upload/` - Upload files to existing artifact
- `POST /api/v1/artifacts/upload/` - Bulk upload with metadata
- `GET /api/v1/artifacts/{id}/status/` - Check processing status

### Evidence Management
- `POST /api/v1/artifacts/{id}/evidence-links/` - Add evidence link
- `PUT /api/v1/artifacts/evidence-links/{id}/` - Update evidence link
- `DELETE /api/v1/artifacts/evidence-links/{id}/` - Remove evidence link
- `DELETE /api/v1/artifacts/files/{uuid}/` - Delete uploaded file

### Bulk Operations
- `PATCH /api/v1/artifacts/bulk/` - Bulk update multiple artifacts

### Technology Suggestions
- `GET /api/v1/artifacts/suggestions/` - Get technology/skill suggestions

### Artifact Types
Supported artifact types:
- `project` - Software projects
- `experience` - Work experience
- `education` - Educational background
- `certification` - Professional certifications
- `publication` - Research publications
- `presentation` - Presentations and talks

## Document Generation System

### CV Generation
- `POST /api/v1/generate/cv/` - Generate CV from job description and artifacts
- `GET /api/v1/generate/{generation_id}/` - Get generation status
- `GET /api/v1/generate/{generation_id}/detail/` - Get detailed generation results
- `POST /api/v1/generate/{generation_id}/rate/` - Rate generated document

### Cover Letter Generation
- `POST /api/v1/generate/cover-letter/` - Generate cover letter from job description and artifacts

### Templates & Analytics
- `GET /api/v1/generate/templates/` - List available CV templates
- `GET /api/v1/generate/analytics/` - Get generation analytics
- `GET /api/v1/generate/` - List user's generations

### Generation Request Format
```json
{
  "jobDescription": "string",
  "companyName": "string",
  "roleTitle": "string",
  "labelIds": [1, 2, 3],
  "templateId": 1,
  "customSections": {},
  "generationPreferences": {
    "tone": "professional|technical|creative",
    "length": "concise|detailed",
    "focusAreas": ["backend", "frontend"]
  }
}
```

### Generation Process
1. Job description is processed and stored with content hash
2. Relevant artifacts are selected based on labelIds and semantic matching
3. Asynchronous generation task is started
4. Real-time status updates available via polling
5. Completed documents include metadata about artifacts used and skill matching

## Document Export System

### Export Operations
- `POST /api/v1/export/{generation_id}/` - Export document to PDF/DOCX
- `GET /api/v1/export/{export_id}/status/` - Check export status
- `GET /api/v1/export/{export_id}/download/` - Download exported file
- `GET /api/v1/export/{export_id}/detail/` - Get export job details

### Export Management
- `GET /api/v1/export/` - List user's export jobs
- `GET /api/v1/export/templates/` - List export templates
- `GET /api/v1/export/analytics/` - Get export analytics

### Export Request Format
```json
{
  "format": "pdf|docx",
  "templateId": 1,
  "options": {
    "includeEvidence": true,
    "evidenceFormat": "hyperlinks|footnotes|qr_codes",
    "pageMargins": "narrow|normal|wide",
    "fontSize": 12,
    "colorScheme": "monochrome|accent|full_color"
  },
  "sections": {
    "includeProfessionalSummary": true,
    "includeSkills": true,
    "includeExperience": true,
    "includeProjects": true,
    "includeEducation": true,
    "includeCertifications": true
  },
  "watermark": {
    "text": "Draft",
    "opacity": 0.1
  }
}
```

## LLM Services & System Management

### Model Management
- `GET /api/v1/llm/available-models/` - List available LLM models
- `POST /api/v1/llm/select-model/` - Select active model
- `GET /api/v1/llm/model-stats/` - Get model performance statistics

### System Health & Monitoring
- `GET /api/v1/llm/system-health/` - Overall system health status
- `GET /api/v1/llm/performance-metrics/` - Detailed performance metrics
- `GET /api/v1/llm/circuit-breakers/` - Circuit breaker states for models
- `GET /api/v1/llm/cost-tracking/` - Cost tracking and usage analytics

### Enhanced Data Management
- `GET /api/v1/llm/job-embeddings/` - Job description embeddings for similarity search
- `GET /api/v1/llm/enhanced-artifacts/` - AI-enhanced artifact data

### LLM Service Features
- **Circuit Breaker Pattern**: Automatic failover when models become unavailable
- **Performance Monitoring**: Real-time metrics on response times and success rates
- **Cost Tracking**: Per-request cost monitoring across different models
- **Semantic Search**: Vector embeddings for job-artifact similarity matching
- **Model Switching**: Dynamic model selection based on availability and performance

## Data Models & Types

### User Profile
```json
{
  "id": 1,
  "email": "string",
  "username": "string",
  "first_name": "string",
  "last_name": "string",
  "profile_image": "string|null",
  "phone": "string|null",
  "linkedin_url": "string|null",
  "github_url": "string|null",
  "website_url": "string|null",
  "bio": "string|null",
  "location": "string|null",
  "preferred_cv_template": "number|null",
  "email_notifications": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Artifact Structure
```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "artifact_type": "project|experience|education|certification|publication|presentation",
  "start_date": "date",
  "end_date": "date|null",
  "technologies": ["string"],
  "collaborators": ["string"],
  "evidence_links": [
    {
      "id": 1,
      "url": "string",
      "link_type": "github|live_app|document|website|portfolio|other",
      "description": "string",
      "file_path": "string|null",
      "mime_type": "string|null",
      "is_accessible": "boolean",
      "last_validated": "datetime|null"
    }
  ],
  "labels": [
    {
      "id": 1,
      "name": "string",
      "color": "string",
      "description": "string|null"
    }
  ],
  "status": "active|archived",
  "extracted_metadata": {},
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Generated Document
```json
{
  "id": "uuid",
  "type": "cv|cover_letter",
  "status": "processing|completed|failed",
  "progressPercentage": 0-100,
  "content": {
    "professionalSummary": "string",
    "keySkills": ["string"],
    "experience": [
      {
        "title": "string",
        "organization": "string",
        "duration": "string",
        "achievements": ["string"],
        "technologiesUsed": ["string"],
        "evidenceReferences": ["string"]
      }
    ],
    "projects": [
      {
        "name": "string",
        "description": "string",
        "technologies": ["string"],
        "evidenceUrl": "string",
        "impactMetrics": "string"
      }
    ],
    "education": [...],
    "certifications": [...]
  },
  "metadata": {
    "artifactsUsed": [1, 2, 3],
    "skillMatchScore": 0.85,
    "missingSkills": ["string"],
    "generationTime": 30,
    "modelUsed": "string"
  },
  "createdAt": "datetime",
  "completedAt": "datetime|null",
  "jobDescriptionHash": "string"
}
```

## Error Handling & Status Codes

### HTTP Status Codes
- `200 OK` - Successful GET/PATCH requests
- `201 Created` - Successful POST requests
- `202 Accepted` - Async operation started
- `204 No Content` - Successful DELETE requests
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "error": "string",
  "detail": "string",
  "code": "string|null",
  "fields": {
    "fieldName": ["error message"]
  }
}
```

## Rate Limiting & Performance

### Rate Limits
- **Generation Endpoints**: 10 requests/hour per user
- **Export Endpoints**: 20 requests/hour per user
- **General API**: 1000 requests/hour per user

### Pagination
List endpoints support pagination with:
```json
{
  "count": 100,
  "next": "url|null",
  "previous": "url|null",
  "results": [...]
}
```

### Filtering & Search
- **Artifacts**: Filter by technologies, labels, status, date range
- **Search**: Full-text search across artifact titles and descriptions
- **Ordering**: Configurable sort order (newest, oldest, alphabetical)

## Security Features

### Authentication Security
- JWT tokens with configurable expiration
- Secure refresh token rotation
- Password strength requirements
- Account lockout after failed attempts

### Data Protection
- CSRF protection on state-changing operations
- XSS protection via content sanitization
- SQL injection protection via ORM
- File upload validation and sanitization

### Privacy Features
- User data isolation (artifacts only visible to owner)
- Secure file storage with access controls
- Optional data retention policies
- GDPR compliance features

## Integration Status Summary

### ✅ Fully Integrated
- Authentication & user management
- Artifact CRUD operations
- File upload & processing
- CV generation
- Document export
- LLM services & monitoring
- Analytics endpoints
- Google OAuth

### ✅ Recently Added/Fixed
- Cover letter generation endpoint
- Technology suggestions endpoint path correction
- Google OAuth endpoint path fixes
- LLM services frontend integration
- Analytics endpoints integration
- Artifact type alignment between frontend/backend

### ⚠️ Partial Implementation
- Labels system (types defined but backend endpoints may be missing)
- Real-time WebSocket updates (polling-based currently)

### 🔧 Development Considerations
- All endpoints follow consistent REST patterns
- Comprehensive error handling and validation
- Asynchronous processing for long-running operations
- Scalable architecture supporting multiple LLM providers
- Extensible template system for customization

## API Usage Examples

### Authentication Flow
1. `POST /api/v1/auth/register/` or `POST /api/v1/auth/login/`
2. Store returned access/refresh tokens
3. Include `Authorization: Bearer {access_token}` in subsequent requests
4. Automatically refresh token on 401 responses

### Document Generation Flow
1. `POST /api/v1/artifacts/` - Create artifacts with relevant work experience
2. `POST /api/v1/generate/cv/` - Start CV generation with job description
3. `GET /api/v1/generate/{id}/` - Poll for completion status
4. `POST /api/v1/export/{generation_id}/` - Export to desired format
5. `GET /api/v1/export/{export_id}/download/` - Download final document

This API integration provides a complete system for AI-powered CV and cover letter generation with comprehensive artifact management, real-time processing status, and flexible export options.