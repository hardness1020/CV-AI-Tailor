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

# Setup environment
cp .env.example .env

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

## Database Migration

### New Installation
For new installations, the system uses PostgreSQL by default with pgvector extension.

### Migrating from SQLite
If you have existing SQLite data:

```bash
# Manual migration steps:
cp .env.example .env                              # Configure PostgreSQL
docker-compose up -d db redis                     # Start services
uv run python manage.py setup_pgvector --test-vectors
uv run python manage.py migrate_to_postgresql     # Migrate data
uv run python manage.py migrate_to_postgresql --verify-only  # Verify
```

## Development Commands

### Database Management
```bash
# Apply migrations
uv run python manage.py migrate

# Create new migrations
uv run python manage.py makemigrations

# Setup pgvector extension
uv run python manage.py setup_pgvector --test-vectors

# Migrate from SQLite to PostgreSQL
uv run python manage.py migrate_to_postgresql
uv run python manage.py migrate_to_postgresql --dry-run
uv run python manage.py migrate_to_postgresql --verify-only
```

### Development Server
```bash
# Run development server
uv run python manage.py runserver 8000

# Run with specific settings
uv run python manage.py runserver --settings=cv_tailor.settings

# Django shell
uv run python manage.py shell

# Collect static files
uv run python manage.py collectstatic
```

### Testing
```bash
# Run all tests
uv run python manage.py test

# Run specific app tests
uv run python manage.py test artifacts
uv run python manage.py test generation

# Run with coverage
uv run coverage run --source='.' manage.py test
uv run coverage report
```

### Background Tasks
```bash
# Start Celery worker
uv run celery -A cv_tailor worker -l info

# Start Celery beat scheduler
uv run celery -A cv_tailor beat -l info

# Monitor Celery tasks
uv run celery -A cv_tailor flower
```

## Environment Configuration

### Required Variables
```env
# Database Configuration
DB_ENGINE=postgresql                    # 'postgresql' or 'sqlite'
DB_NAME=cv_tailor
DB_USER=cv_tailor_user
DB_PASSWORD=cv_tailor_dev_password
DB_HOST=localhost
DB_PORT=5432

# LLM APIs
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Background Tasks
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Optional
GITHUB_TOKEN=your-github-token          # For repository analysis
```

### Database Options
- **PostgreSQL** (Recommended): Full features with vector search
- **SQLite** (Fallback): Limited functionality, development only

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

## Development Workflow

1. **Start Services**: `docker-compose up -d db redis`
2. **Install Dependencies**: `uv sync`
3. **Configure Environment**: `cp .env.example .env`
4. **Setup Database**: `uv run python manage.py migrate`
5. **Setup pgvector**: `uv run python manage.py setup_pgvector --test-vectors`
6. **Run Server**: `uv run python manage.py runserver 8000`
7. **Start Worker**: `uv run celery -A cv_tailor worker -l info`

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose logs db

# Test connection
docker exec -it cv_tailor_db psql -U cv_tailor_user -d cv_tailor

# Restart services
docker-compose restart db
```

### pgvector Issues
```bash
# Verify pgvector installation
uv run python manage.py setup_pgvector --test-vectors

# Check extension in database
docker exec -it cv_tailor_db psql -U cv_tailor_user -d cv_tailor -c "\dx"
```

### Migration Issues
```bash
# Check migration status
uv run python manage.py showmigrations

# Reset migrations (development only)
uv run python manage.py migrate --fake-initial

# Verify data integrity
uv run python manage.py migrate_to_postgresql --verify-only
```

## Production Deployment

For production deployment, ensure:
- Use strong database passwords
- Set `DEBUG=False`
- Configure proper CORS settings
- Use HTTPS for all endpoints
- Set up database backups
- Configure proper logging
- Use production WSGI server (gunicorn included)

## Contributing

1. Follow Django best practices
2. Write tests for new features
3. Update documentation
4. Use conventional commits
5. Ensure migrations are reversible