# CV Auto-Tailor Backend API

Django REST API backend for the CV & Cover-Letter Auto-Tailor application.

## Features

- User authentication and management
- Artifact upload and processing
- AI-powered CV generation
- Document export (PDF/DOCX)
- Evidence link validation
- Multi-provider LLM integration

## Development Setup

```bash
# Install dependencies
uv sync

# Run development server
uv run python manage.py runserver

# Run tests
uv run pytest

# Run migrations
uv run python manage.py migrate
```

## API Documentation

API documentation is available at `/api/docs/` when running the development server.