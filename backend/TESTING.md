# Backend Testing Guide

This document provides comprehensive information about testing in the CV Tailor Django backend application.

## Quick Start - Running Tests

### Fix for Persistent Test Database Issue

If you encounter the error "database 'test_cv_tailor' already exists", this happens when previous test runs were interrupted and didn't clean up properly. **Add --keepdb config when testing**

## Test Organization Structure

```
backend/
├── accounts/
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                # Common fixtures and setup
│       ├── test_models.py             # User model tests
│       ├── test_auth_api.py           # Authentication API tests
│       ├── test_profile_api.py        # User profile API tests
│       ├── test_auth_integration.py   # Integration tests
│       └── test_google_oauth.py       # Google OAuth tests
├── artifacts/
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                # Common fixtures and setup
│       ├── test_models.py             # Artifact, EvidenceLink model tests
│       ├── test_api.py                # CRUD API tests
│       └── test_editing.py            # Artifact editing tests
├── generation/
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                # Common fixtures and setup
│       ├── test_models.py             # Generation models tests
│       ├── test_api.py                # CV generation API tests
│       └── test_tasks.py              # Generation task tests
├── export/
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                # Common fixtures and setup
│       ├── test_models.py             # Export models tests
│       ├── test_api.py                # Export API tests
│       └── test_tasks.py              # Export task tests
└── llm_services/
    └── tests/                         # Comprehensive test suite
        ├── __init__.py
        ├── conftest.py                # Shared fixtures and utilities
        ├── test_models.py             # Circuit breaker and LLM model tests
        ├── test_services.py           # LLM service integration tests
        ├── test_serializers.py        # API serializer tests
        ├── test_views.py              # API endpoint tests
        ├── test_tasks.py              # Background task tests
        ├── test_real_api_config.py    # Real API configuration tests
        ├── test_real_circuit_breaker.py # Real API circuit breaker tests
        ├── test_real_llm_integration.py # Basic LLM API integration tests
        ├── test_real_pipeline_integration.py # End-to-end pipeline tests
        ├── run_real_api_tests.py      # Real API test runner with cost controls
        └── README.md                  # Detailed testing documentation
```

## Test Categories and Naming Conventions

### 1. Model Tests (`test_models.py`)
- Test model creation, validation, and behavior
- Test custom model methods and properties
- Test model relationships and cascading deletes
- Test model string representations
- **Naming pattern**: `{ModelName}ModelTests`

### 2. API Tests (`test_api.py`, `test_*_api.py`)
- Test CRUD operations via API endpoints
- Test request/response formats
- Test authentication and authorization
- Test input validation and error handling
- **Naming pattern**: `{Feature}APITests`

### 3. Task Tests (`test_tasks.py`)
- Test Celery background tasks
- Test task failure handling and retries
- Test task result processing
- **Naming pattern**: `{TaskName}TaskTests`

### 4. Integration Tests (`test_*_integration.py`)
- Test complete workflows across multiple components
- Test complex business logic flows
- Test external service integrations
- **Naming pattern**: `{Feature}IntegrationTests`

### 5. Service Tests (`test_services.py`, `test_*_service.py`)
- Test business logic services
- Test external API integrations
- Test service-level error handling
- **Naming pattern**: `{ServiceName}ServiceTests`

## Running Tests

### Run All Tests
```bash
cd backend
uv run python manage.py test
```

### Run Tests by App
```bash
# Test specific app
uv run python manage.py test accounts
uv run python manage.py test artifacts
uv run python manage.py test generation
uv run python manage.py test export
uv run python manage.py test llm_services
```

### Run Tests by Module
```bash
# Test specific module within an app
uv run python manage.py test accounts.tests.test_models
uv run python manage.py test artifacts.tests.test_api
uv run python manage.py test generation.tests.test_tasks
```

### Run Specific Test Classes or Methods
```bash
# Run specific test class
uv run python manage.py test accounts.tests.test_models.UserModelTests

# Run specific test method
uv run python manage.py test accounts.tests.test_auth_api.AuthenticationAPITests.test_user_login
```

## Test Configuration

### Django Test Settings
The application uses Django's default test runner with the following key configurations:

- **Database**: PostgreSQL with pgvector extension for vector operations (see Database Configuration below)
- **Authentication**: JWT tokens for API authentication tests
- **Media Files**: Temporary directories for file upload tests
- **Celery**: Synchronous execution in tests (CELERY_TASK_ALWAYS_EAGER=True)

## Database Configuration

### PostgreSQL with pgvector Extension

The application uses PostgreSQL with the pgvector extension for vector similarity operations. This requires special consideration during test database setup.

#### Problem: pgvector Extension in Test Database

**Issue**: When running tests, Django creates a fresh test database that doesn't automatically include PostgreSQL extensions. This causes failures like:

```
django.db.utils.ProgrammingError: type "vector" does not exist
LINE 1: ...ssed_content" jsonb NOT NULL, "content_embedding" vector(153...
```

**Solution**: Create a migration to enable the pgvector extension before any models that use `VectorField` are created.

## Test Execution Order

Tests are organized by logical execution order within each app:

1. **Model Tests** - Foundation layer
2. **Service Tests** - Business logic layer
3. **API Tests** - Interface layer
4. **Task Tests** - Background processing
5. **Integration Tests** - End-to-end workflows

## Documentation and Maintenance

### Test Documentation Standards
- Each test class should have a descriptive docstring
- Complex test methods should include comments
- Test data should be self-documenting

### Regular Maintenance
- Review and update test fixtures regularly
- Remove deprecated tests
- Ensure tests remain fast and reliable
- Update mocks when external APIs change


## Real LLM API Integration Testing

For testing actual API integrations with OpenAI and Anthropic services, the `llm_services` app includes a comprehensive real API testing framework.

### ⚠️ Important Warnings

**These tests use real API tokens and incur actual costs.** Always:
- Set strict budget limits
- Run in test environments only
- Monitor token usage
- Use minimal test data
- Never run in production


## Test Execution Results (Latest Run - 2025-09-25 - ALL TESTS PASSING! 🎉)

### Summary After Latest Test Run

| App | Total Tests | Passed | Failed | Status |
|-----|------------|---------|---------|--------|
| **accounts** | 63 | 63 | 0 | ✅ PERFECT |
| **artifacts** | 38 | 38 | 0 | ✅ PERFECT |
| **generation** | 27 | 27 | 0 | ✅ PERFECT |
| **export** | 23 | 23 | 0 | ✅ PERFECT |
| **llm_services** | 127 | 127 | 0 | ✅ PERFECT |
| **TOTAL** | **278** | **278** | **0** | **🎉 100% PASS RATE!** |

### Test Execution Details
- **Execution Time**: 108.629 seconds
- **Test Database**: Using PostgreSQL with pgvector extension
- **Notable Features Tested**:
  - JWT authentication and Google OAuth integration
  - Artifact CRUD operations and bulk uploads
  - CV/Cover letter generation pipeline
  - Export functionality with multiple formats
  - LLM service integrations with circuit breakers
  - Document processing with embedding generation
  - Background task processing with Celery
  - Performance tracking and metrics collection

## Development Database Setup

### Test Accounts (Created: 2025-09-26)

For development and testing purposes, the following accounts have been created:

#### Superuser Account
- Credentials are stored in the `.env` file for security
- **Privileges**: Can access Django Admin, full API access, web application

**Login Instructions**:

1. **Django Admin** (Session-based):
   - URL: `http://localhost:8000/admin/`
   - Use: **Username** + Password (see `.env` file)

2. **Frontend App** (JWT-based):
   - Use Email + Password (see `.env` file)
   - Login via API: `POST /api/v1/auth/login/` with email/password JSON

**Important Notes**:
- ✅ **Superuser CAN login to frontend app** - use the email address, not username
- The app uses custom User model with `USERNAME_FIELD = 'email'`
- Both Django Admin and frontend app login work correctly
- Frontend requires email address for authentication, not username

**Security Note**: These are development-only accounts. Never use these credentials in production environments.

### Database Reset Instructions

If you need to reset the database:
```bash
# Delete existing database (if SQLite)
rm -f db.sqlite3

# Or reset PostgreSQL database
docker-compose down
docker-compose up -d db

# Run migrations
uv run python manage.py migrate

# Create superuser (credentials from .env)
echo "from django.contrib.auth import get_user_model; import os; User = get_user_model(); User.objects.create_superuser(os.getenv('DJANGO_SUPERUSER_USERNAME'), os.getenv('DJANGO_SUPERUSER_EMAIL'), os.getenv('DJANGO_SUPERUSER_PASSWORD'))" | uv run python manage.py shell
```
