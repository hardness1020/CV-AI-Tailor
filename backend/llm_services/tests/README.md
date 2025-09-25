# LLM Services Test Suite

Comprehensive unit tests for the LLM Services Django app, covering models, services, views, tasks, and serializers.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Pytest configuration and fixtures
├── test_models.py       # Model tests
├── test_services.py     # Service class tests
├── test_views.py        # API view tests
├── test_tasks.py        # Celery task tests
├── test_serializers.py  # DRF serializer tests
└── README.md           # This file
```

## Running Tests

### All Tests
```bash
cd backend
uv run pytest llm_services/tests/
```

### Specific Test Files
```bash
uv run pytest llm_services/tests/test_models.py
uv run pytest llm_services/tests/test_services.py
uv run pytest llm_services/tests/test_views.py
uv run pytest llm_services/tests/test_tasks.py
uv run pytest llm_services/tests/test_serializers.py
```

### With Coverage
```bash
uv run pytest llm_services/tests/ --cov=llm_services --cov-report=html
```

### Specific Test Classes or Methods
```bash
uv run pytest llm_services/tests/test_models.py::ModelPerformanceMetricTestCase
uv run pytest llm_services/tests/test_services.py::EnhancedLLMServiceTestCase::test_parse_job_description
```

### Test Markers
```bash
uv run pytest -m unit                    # Run only unit tests
uv run pytest -m integration             # Run only integration tests
uv run pytest -m "not slow"             # Skip slow tests
uv run pytest -m async_test             # Run only async tests
```

## Test Coverage

### Models (test_models.py)
- ✅ `ModelPerformanceMetric` - Creation, validation, string representation
- ✅ `EnhancedArtifact` - Creation, relationships, vector field mocking
- ✅ `ArtifactChunk` - Creation, unique constraints, relationships
- ✅ `JobDescriptionEmbedding` - Creation, unique constraints, access tracking
- ✅ `ModelCostTracking` - Creation, unique constraints, aggregation
- ✅ `CircuitBreakerState` - Creation, state transitions, request validation

### Services (test_services.py)
- ✅ `EnhancedLLMService` - Model selection, job parsing, CV generation
- ✅ `FlexibleEmbeddingService` - Embedding generation, artifact storage, job caching
- ✅ `AdvancedDocumentProcessor` - PDF processing, text chunking, LangChain integration
- ✅ `ModelPerformanceTracker` - Performance recording, statistics, model selection
- ✅ `CircuitBreakerService` - Success/failure recording, request validation
- ✅ `ModelRegistry` - Model configuration, filtering, availability

### Views (test_views.py)
- ✅ `ModelPerformanceMetricViewSet` - CRUD operations, filtering, summaries
- ✅ `CircuitBreakerStateViewSet` - State management, health monitoring
- ✅ `ModelCostTrackingViewSet` - Cost analysis, monthly summaries
- ✅ `JobDescriptionEmbeddingViewSet` - Cache management, statistics
- ✅ `EnhancedArtifactViewSet` - Artifact management, chunk access
- ✅ Custom API views - Model stats, selection, health, available models

### Tasks (test_tasks.py)
- ✅ `generate_cv_task` - End-to-end CV generation workflow
- ✅ `generate_job_embedding_cache` - Job embedding caching
- ✅ `enhance_artifact_with_llm` - Artifact processing with retries
- ✅ `cleanup_expired_generations` - Data cleanup tasks
- ✅ `cleanup_old_performance_metrics` - Performance data cleanup

### Serializers (test_serializers.py)
- ✅ All DRF serializers - Serialization, deserialization, validation
- ✅ Custom serializers - Model stats, selection requests/responses
- ✅ Field validation - Write-only fields, calculated fields, constraints

## Mock Strategy

### External Dependencies Mocked
- 🔧 **OpenAI API** - Chat completions, embeddings, token usage
- 🔧 **Anthropic API** - Claude model interactions
- 🔧 **LangChain** - Document loaders, text splitters, processing
- 🔧 **pgvector** - Vector field operations, similarity search
- 🔧 **Redis Cache** - Caching operations
- 🔧 **File System** - Document file access, uploads

### Fixtures Available
- `user`, `staff_user` - Test user accounts
- `mock_openai_client` - Mocked OpenAI client with responses
- `mock_langchain` - Mocked LangChain components
- `mock_pgvector` - Mocked vector field operations
- `performance_metrics` - Test performance data
- `circuit_breakers` - Test circuit breaker states
- `job_embeddings` - Test embedding data
- `enhanced_artifacts` - Test artifact and chunk data

## Error Testing

### Comprehensive Error Scenarios
- ✅ **API Failures** - Network errors, invalid responses, rate limits
- ✅ **Validation Errors** - Invalid data, constraint violations
- ✅ **Processing Errors** - Document parsing failures, embedding errors
- ✅ **Database Errors** - Constraint violations, connection issues
- ✅ **Authentication Errors** - Unauthorized access, permission denied
- ✅ **Circuit Breaker Logic** - Failure thresholds, timeout handling

## Performance Testing

### Async Operations Tested
- ✅ Job description parsing with LLM calls
- ✅ CV content generation with multiple API calls
- ✅ Embedding generation and storage
- ✅ Document processing with LangChain
- ✅ Bulk operations and cleanup tasks

## Configuration

### Test Settings
- Uses in-memory SQLite database for speed
- Mocks external API calls to avoid costs
- Disables cache for deterministic results
- Uses dummy cache backend
- Sets test API keys to avoid missing key errors

### Environment Variables for Testing
```bash
export DJANGO_SETTINGS_MODULE=cv_tailor.settings
export DATABASE_URL=sqlite://:memory:
export OPENAI_API_KEY=test-key
export ANTHROPIC_API_KEY=test-key
```

## Best Practices Followed

### Test Organization
- ✅ **Arrange-Act-Assert** pattern consistently applied
- ✅ **Single responsibility** - Each test focuses on one behavior
- ✅ **Descriptive names** - Test names clearly describe what's being tested
- ✅ **Proper setup/teardown** - Using fixtures and Django TestCase
- ✅ **Mock isolation** - External dependencies properly mocked

### Coverage Goals
- 🎯 **Models**: 100% line coverage, all methods tested
- 🎯 **Services**: 95%+ coverage, core business logic thoroughly tested
- 🎯 **Views**: 90%+ coverage, all endpoints and error cases tested
- 🎯 **Tasks**: 90%+ coverage, async operations and error handling tested
- 🎯 **Serializers**: 95%+ coverage, validation and field behavior tested

## Running in CI/CD

```yaml
# Example GitHub Actions test job
test-llm-services:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Install uv
      uses: astral-sh/setup-uv@v1
    - name: Run LLM Services Tests
      run: |
        cd backend
        uv run pytest llm_services/tests/ \
          --cov=llm_services \
          --cov-report=xml \
          --junit-xml=test-results.xml
```

## Troubleshooting

### Common Issues
1. **Import Errors** - Ensure all dependencies are installed via `uv sync`
2. **Mock Issues** - Check that external services are properly mocked
3. **Database Issues** - Ensure test database permissions are correct
4. **Async Issues** - Use `@pytest.mark.asyncio` for async tests

### Debug Commands
```bash
# Run with verbose output
uv run pytest llm_services/tests/ -v -s

# Run specific failing test with full traceback
uv run pytest llm_services/tests/test_services.py::test_name -vvv --tb=long

# Run with pdb debugger on failures
uv run pytest llm_services/tests/ --pdb
```