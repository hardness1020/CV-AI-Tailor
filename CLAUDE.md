# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Always create docs for new/edit/fix features before implement code. Follow the rules in @rules/ directory.

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
- **Dependency Management:** uv for Python dependency management (see pyproject.toml)

**Frontend (React):** `/frontend/`
- 
- **Framework:** React 18 with TypeScript and Vite
- **Routing:** React Router DOM
- **Styling:** Tailwind CSS with Radix UI components
- **State Management:** Zustand
- **Forms:** React Hook Form with Zod validation
- **HTTP Client:** Axios

## Visual Development & Testing

### Design System

The project follows S-Tier SaaS design standards inspired by Stripe, Airbnb, and Linear. All UI development must adhere to:

- **Design Principles**: `/docs/design-principles.md` - Comprehensive checklist for world-class UI
- **Component Library**: NextUI with custom Tailwind configuration

### Quick Visual Check

**IMMEDIATELY after implementing any front-end change:**

1. **Identify what changed** - Review the modified components/pages
2. **Navigate to affected pages** - Use `mcp__playwright__browser_navigate` to visit each changed view
3. **Verify design compliance** - Compare against `/docs/design-principles.md`
4. **Validate feature implementation** - Ensure the change fulfills the user's specific request
5. **Check acceptance criteria** - Review any provided context files or requirements
6. **Capture evidence** - Take full page screenshot at desktop viewport (1440px) of each changed view
7. **Check for errors** - Run `mcp__playwright__browser_console_messages` ⚠️

This verification ensures changes meet design standards and user requirements.

### Comprehensive Design Review

For significant UI changes or before merging PRs, use the design review agent:

```bash
# Option 1: Use the slash command
/design-review

# Option 2: Invoke the agent directly
@agent-design-review
```

The design review agent will:

- Test all interactive states and user flows
- Verify responsiveness (desktop/tablet/mobile)
- Check accessibility (WCAG 2.1 AA compliance)
- Validate visual polish and consistency
- Test edge cases and error states
- Provide categorized feedback (Blockers/High/Medium/Nitpicks)

## Python Dependency Management

This project uses **uv** for Python dependency management instead of pip/poetry:

```bash
# Install dependencies
uv sync                                       # Install all dependencies from uv.lock

# Add new dependencies
uv add django-package-name                    # Add to main dependencies
uv add pytest --dev                          # Add to dev dependencies

# Update dependencies
uv lock --upgrade                             # Update lock file
uv sync                                       # Sync updated dependencies

# Run commands with uv
uv run python manage.py <command>             # Run Django management commands
uv run pytest                                # Run tests with pytest
```

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
docker-compose up -d db redis                # Start PostgreSQL
cd backend && python manage.py setup_pgvector --test-vectors
python manage.py migrate_to_postgresql       # Migrate data
```

### Backend (Django)
```bash
cd backend

# Development server
uv run python manage.py runserver 8000       # Start development server
uv run python manage.py shell                # Django shell

# Database management
uv run python manage.py migrate              # Apply database migrations
uv run python manage.py makemigrations       # Create new migrations
uv run python manage.py collectstatic        # Collect static files

# Testing
uv run python manage.py test                 # Run all tests
uv run python manage.py test llm_services    # Run specific app tests
uv run python manage.py test -v 2            # Run with verbose output
uv run python manage.py test --failfast      # Stop on first failure
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

## Testing Strategy
- **Backend:** Django's built-in testing with uv dependency management and pytest configuration
- **Frontend:** Vitest with React Testing Library and jsdom
- **Coverage:** Configured for both frontend and backend
- **Important:** Always drop test database before running tests to avoid conflicts

## Development Workflow and Governance

This project follows a **docs-first development pipeline** with mandatory documentation stages:

### Governance Rules (from /rules/ directory)
- **Always create documentation before implementing code**
- Follow 10-stage docs-first development process
- All major changes require corresponding documentation updates
- Stage gating with human review at each step
- Use conventional commit format: `<type>(scope): subject (#<ID>)`
- Branch naming: `feat/<ID>-<slug>`, `fix/<ID>-<slug>`, `chore/<ID>-<slug>`

### Documentation Structure (from /docs/ directory)
- **PRDs:** `docs/prds/prd-YYYYMMDD.md` - Product requirements
- **Tech Specs:** `docs/specs/spec-YYYYMMDD-<spec>.md` - Technical specifications
- **ADRs:** `docs/adrs/adr-YYYYMMDD-<slug>.md` - Architecture decision records
- **Features:** `docs/features/ft-<ID>-<slug>.md` - Feature specifications
- **Op-Notes:** `docs/op-notes/op-<ID>-<slug>.md` - Operational runbooks

### Pipeline Stages
- Create dated SPEC snapshots when changing contracts, topology, or framework roles
- Each stage requires human review/approval before proceeding
- Generate required documentation files before implementing code