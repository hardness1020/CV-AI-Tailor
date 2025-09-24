# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CV Tailor** is a full-stack application that auto-generates tailored CVs and cover letters from uploaded work artifacts using LLM processing. Built with Django REST API backend and React frontend.

## Architecture

**Backend (Django):** `/backend/`
- **Framework:** Django 4.2+ with Django REST Framework
- **Database:** PostgreSQL 15+ with pgvector extension for vector similarity search
- **LLM Integration:** OpenAI/Anthropic APIs for content generation and semantic ranking
- **Document Processing:** LangChain for multi-format processing (PDF, GitHub, web)
- **Vector Search:** pgvector for artifact-job semantic similarity matching
- **Authentication:** JWT tokens with Google OAuth via django-allauth
- **Background Tasks:** Celery with Redis broker
- **Document Generation:** PDF/DOCX generation with ReportLab and python-docx

**Frontend (React):** `/frontend/`
- **Framework:** React 18 with TypeScript and Vite
- **Routing:** React Router DOM
- **Styling:** Tailwind CSS with Radix UI components
- **State Management:** Zustand
- **Forms:** React Hook Form with Zod validation
- **HTTP Client:** Axios

## Development Commands

### Docker Development Environment
```bash
# Start all services (PostgreSQL, Redis, Backend, Celery)
docker-compose up -d

# Start specific services
docker-compose up -d db redis               # Database and cache only
docker-compose up backend celery             # Application services

# View service logs
docker-compose logs -f backend
docker-compose logs -f db

# Stop all services
docker-compose down
```

### Database Migration (SQLite → PostgreSQL)
```bash
# One-time setup for PostgreSQL migration
cp backend/.env.example backend/.env         # Configure environment
python test_migration.py                     # Automated migration test
# OR manual steps:
docker-compose up -d db redis                # Start PostgreSQL
cd backend && python manage.py setup_pgvector --test-vectors
python manage.py migrate_to_postgresql       # Migrate data
```

### Backend (Django)
```bash
cd backend
python manage.py runserver 8000              # Start development server
python manage.py test                        # Run tests
python manage.py migrate                     # Apply database migrations
python manage.py makemigrations              # Create new migrations
python manage.py shell                       # Django shell
python manage.py collectstatic               # Collect static files

# Database-specific commands
python manage.py setup_pgvector --test-vectors    # Setup vector database
python manage.py migrate_to_postgresql            # Migrate from SQLite
python manage.py migrate_to_postgresql --dry-run  # Test migration
```

### Frontend (React)
```bash
cd frontend
npm run dev         # Start development server (port 3000)
npm run build       # Build for production
npm run typecheck   # Run TypeScript type checking
npm run lint        # Run ESLint
npm run test        # Run Vitest tests
npm run test:ui     # Run tests with UI
npm install         # Install dependencies
```

### Development Workflow Commands
Full Docker development stack:
- **PostgreSQL:** Database server on localhost:5432 with pgvector extension
- **Redis:** Cache/broker server on localhost:6379
- **Backend:** Django dev server on http://localhost:8000
- **Frontend:** Vite dev server on http://localhost:3000 (when started separately)
- **Celery:** Background task worker for artifact processing
- **CORS:** Frontend allowed origins configured in Django settings

## Key Application Components

### Backend API Structure
- `/api/v1/auth/` - Authentication endpoints (login, register, OAuth)
- `/api/v1/artifacts/` - Work artifact management (upload, categorize)
- `/api/v1/generate/` - CV/cover letter generation via LLM
- `/api/v1/export/` - Document export (PDF/DOCX)

### Django Apps
- **accounts:** Custom user model with Google OAuth integration
- **artifacts:** Work artifact storage and metadata management
- **generation:** LLM-based CV/cover letter generation logic
- **export:** Document generation and formatting

### Frontend Architecture
- **Components:** Reusable UI components using Radix primitives
- **Layout:** Shared layout with protected routes
- **Utils:** Common utilities (cn for className merging, formatters)
- **State:** Zustand stores for application state

## Environment Configuration

### Required Environment Variables (Backend)
```
# Django Core
SECRET_KEY=<django-secret-key>
DEBUG=True

# Database Configuration (choose one)
DB_ENGINE=postgresql                    # or 'sqlite' for development fallback
DB_NAME=cv_tailor                       # PostgreSQL database name
DB_USER=cv_tailor_user                  # PostgreSQL username
DB_PASSWORD=cv_tailor_dev_password      # PostgreSQL password
DB_HOST=localhost                       # PostgreSQL host
DB_PORT=5432                           # PostgreSQL port

# LLM Integration
OPENAI_API_KEY=<openai-api-key>
ANTHROPIC_API_KEY=<anthropic-api-key>

# OAuth
GOOGLE_CLIENT_ID=<google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<google-oauth-client-secret>

# Background Tasks
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Optional: GitHub integration for repository analysis
GITHUB_TOKEN=<github-token>
```

### Database Options
- **PostgreSQL (Recommended)**: Full-featured with pgvector for semantic search
- **SQLite (Fallback)**: Simple development setup, limited features

## Testing Strategy
- **Backend:** Django's built-in testing with pytest integration
- **Frontend:** Vitest with React Testing Library and jsdom
- **Coverage:** Configured for both frontend and backend

## Documentation-First Development

This repository implements a **10-stage docs-first development pipeline** with mandatory documentation in `/docs/`:

### Documentation Structure
- **PRDs:** `docs/prds/prd-YYYYMMDD.md` - Product requirements
- **Tech Specs:** `docs/specs/spec-YYYYMMDD-<spec>.md` - Technical specifications
- **ADRs:** `docs/adrs/adr-YYYYMMDD-<slug>.md` - Architecture decision records
- **Features:** `docs/features/ft-<ID>-<slug>.md` - Feature specifications

### Governance Rules
- All major changes require corresponding documentation updates
- Follow conventional commit format: `<type>(scope): subject (#<ID>)`
- Branch naming: `feat/<ID>-<slug>`, `fix/<ID>-<slug>`, `chore/<ID>-<slug>`
- Create dated SPEC snapshots when changing contracts, topology, or framework roles

## Docker Networking and Container Names

**Important:** The application uses RFC-compliant container names with hyphens instead of underscores:
- **Backend container**: `cv-tailor-backend` (not `cv_tailor_backend`)
- **Frontend proxy**: Vite proxy configured to connect to `cv-tailor-backend:8000` when `DOCKER_ENV=true`
- **Django ALLOWED_HOSTS**: Includes `cv-tailor-backend` for container-to-container communication

When making networking changes, ensure hostnames follow RFC 1034/1035 standards (use hyphens, not underscores).

## Test User Account

For testing login functionality:
- **Email**: `test@example.com`
- **Password**: `testpassword`
- User is automatically created during development setup

## Troubleshooting Common Issues

### Login Issues
- Ensure all containers are running: `docker-compose ps`
- Check frontend proxy configuration in `frontend/vite.config.ts`
- Verify backend is accessible: `curl http://localhost:8000/api/v1/auth/login/`
- Check container logs: `docker-compose logs backend frontend`

### Database Migration Issues
- Use automated migration test: `python test_migration.py`
- Check PostgreSQL connection: `docker-compose exec db psql -U cv_tailor_user -d cv_tailor`
- Verify pgvector extension: `python manage.py setup_pgvector --test-vectors`

### Container Networking Issues
- Restart all services: `docker-compose down && docker-compose up -d`
- Check container IP addresses: `docker inspect cv-tailor-backend | grep IPAddress`
- Verify CORS configuration in `backend/cv_tailor/settings.py`