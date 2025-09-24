# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CV Tailor** is a full-stack application that auto-generates tailored CVs and cover letters from uploaded work artifacts using LLM processing. Built with Django REST API backend and React frontend.

## Architecture

**Backend (Django):** `/workspace/backend/`
- **Framework:** Django 4.2+ with Django REST Framework
- **Database:** SQLite (development) with models for accounts, artifacts, generation, export
- **LLM Integration:** OpenAI/Anthropic APIs for content generation
- **Authentication:** JWT tokens with Google OAuth via django-allauth
- **Background Tasks:** Celery with Redis broker
- **Document Processing:** PDF/DOCX generation with ReportLab and python-docx

**Frontend (React):** `/workspace/frontend/`
- **Framework:** React 18 with TypeScript and Vite
- **Routing:** React Router DOM
- **Styling:** Tailwind CSS with Radix UI components
- **State Management:** Zustand
- **Forms:** React Hook Form with Zod validation
- **HTTP Client:** Axios

## Development Commands

### Backend (Django)
```bash
cd backend
uv run python manage.py runserver 8000    # Start development server
uv run python manage.py test              # Run tests
uv run python manage.py migrate           # Apply database migrations
uv run python manage.py makemigrations    # Create new migrations
uv run python manage.py shell             # Django shell
uv run python manage.py collectstatic     # Collect static files
uv sync                                    # Install/sync dependencies
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
Both servers run in development:
- **Backend:** Django dev server on http://localhost:8000
- **Frontend:** Vite dev server on http://localhost:3000
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
SECRET_KEY=<django-secret-key>
DEBUG=True
OPENAI_API_KEY=<openai-api-key>
ANTHROPIC_API_KEY=<anthropic-api-key>
GOOGLE_CLIENT_ID=<google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<google-oauth-client-secret>
CELERY_BROKER_URL=redis://localhost:6379/0
```

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