# CV Tailor Backend API

Django REST API backend for CV Tailor - an AI-powered CV and cover letter generator with semantic artifact processing.

## Features

- **User Authentication**: JWT tokens with Google OAuth integration
- **Artifact Processing**: Multi-format document processing (PDF, GitHub repos, web profiles)
- **LLM Integration**: OpenAI/Anthropic APIs for content generation and semantic ranking
- **Vector Search**: PostgreSQL + pgvector for semantic similarity matching
- **Document Processing**: LangChain-powered content extraction and analysis
- **Background Tasks**: Celery workers for async artifact processing
- **Document Export**: PDF/DOCX generation with ReportLab and python-docx
- **Evidence Validation**: Link verification and GitHub repository analysis

## Architecture

- **Database**: PostgreSQL 15+ with pgvector extension for vector similarity search
- **Cache/Broker**: Redis for caching and Celery task queue
- **Document Processing**: LangChain for multi-format content extraction
- **LLM Providers**: Dual-provider strategy (OpenAI primary, Anthropic fallback)
- **Background Tasks**: Celery workers for artifact enhancement and processing

## Quick Start

### Option 1: Docker Development (Recommended)

```bash
# Start PostgreSQL and Redis services
docker-compose up -d db redis

# Install Python dependencies (uv automatically reads pyproject.toml)
uv sync

# Setup database and pgvector
uv run python manage.py migrate
uv run python manage.py setup_pgvector --test-vectors

# Run development server
uv run python manage.py runserver 8000
```

### Option 2: Full Docker Stack

```bash
# Start all services (PostgreSQL, Redis, Django, Celery)
docker-compose up -d

# View logs
docker-compose logs -f backend
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login/` - JWT token login
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/google/` - Google OAuth login

### Artifacts
- `GET /api/v1/artifacts/` - List user artifacts
- `POST /api/v1/artifacts/` - Create new artifact
- `GET /api/v1/artifacts/{id}/` - Retrieve artifact details
- `POST /api/v1/artifacts/{id}/enhance/` - Process artifact with LLM

### Generation
- `POST /api/v1/generate/cv/` - Generate CV from job description
- `GET /api/v1/generation/{id}/status/` - Check generation status
- `GET /api/v1/templates/` - List available CV templates

### Export
- `POST /api/v1/export/pdf/` - Export document as PDF
- `POST /api/v1/export/docx/` - Export document as DOCX

## Project Structure

```
backend/
├── cv_tailor/          # Django project settings
├── accounts/           # User authentication and OAuth
├── artifacts/          # Artifact storage and processing
├── generation/         # LLM-based CV generation
├── export/            # Document export functionality
├── db_init/           # PostgreSQL initialization scripts
├── media/             # Uploaded files
├── requirements.txt   # Python dependencies
├── manage.py          # Django management script
└── README.md          # This file
```