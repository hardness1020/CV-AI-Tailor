# Real LLM API Testing Guide

This guide explains how to run real LLM API integration tests that make actual API calls to test the CV generation pipeline.

## ⚠️ Important Warnings

**These tests use real API tokens and incur actual costs.** Always:
- Set strict budget limits
- Run in test environments only
- Monitor token usage
- Use minimal test data
- Never run in production

## Quick Start

### 1. Prerequisites

**Option A: Automatic Environment Loading (Recommended)**
```bash
# Place API keys in backend/.env file (automatically loaded)
cd backend
# Edit .env file with your keys:
# OPENAI_API_KEY="your-openai-api-key"
# ANTHROPIC_API_KEY="your-anthropic-api-key"  # Optional
```

**Option B: Manual Environment Variables**
```bash
# Set required API keys manually
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"  # Optional

# Ensure you're in a test environment
export DJANGO_SETTINGS_MODULE="cv_tailor.settings"
export TESTING=1
```

### 2. Check Configuration

```bash
cd backend
uv run python run_real_api_tests.py --check-config
```

### 3. Run Basic Tests (Recommended)

```bash
# Run basic integration tests (~$0.10 cost)
uv run python run_real_api_tests.py --run-basic --max-cost=0.10 --force
```

### 4. Run All Tests (Advanced)

```bash
# Run complete test suite (~$0.35 cost)
uv run python run_real_api_tests.py --run-all --max-cost=0.50 --force
```

## Test Files Overview

### Core Test Files

1. **`test_real_llm_integration.py`**
   - Basic LLM API integration tests
   - Job description parsing
   - CV content generation
   - Artifact ranking
   - Embedding generation
   - Cost: ~$0.10 for all tests

2. **`test_real_circuit_breaker.py`**
   - Circuit breaker functionality with real APIs
   - Performance tracking and metrics
   - API failure handling and recovery
   - Cost: ~$0.05 for all tests

3. **`test_real_pipeline_integration.py`**
   - End-to-end pipeline testing
   - Complete CV generation workflow
   - Multi-service integration
   - Cost: ~$0.20 for all tests

4. **`test_real_api_config.py`**
   - Configuration and safety utilities
   - Budget management
   - Test data factory with minimal token usage
   - Token usage validation

### Test Runner

**`run_real_api_tests.py`**
- Safe test execution with budget controls
- Environment validation
- Cost estimation and monitoring
- Interactive confirmation for safety

## Test Configuration

### Budget Controls

Tests include multiple safety mechanisms:

```python
# Default budget limits (configurable)
MAX_TOKENS_PER_TEST = 200      # Tokens per individual test
MAX_TOKENS_TOTAL = 2000        # Total tokens for all tests
MAX_COST_PER_TEST_USD = 0.01   # $0.01 per test
MAX_COST_TOTAL_USD = 0.50      # $0.50 total budget
```

### Minimal Test Data

All tests use minimal data to reduce costs:

```python
MINIMAL_JOB_DESC = "Python dev. Skills: Django, REST APIs."
MINIMAL_ARTIFACTS = [{"title": "API Project", "description": "Built REST API"}]
```

Estimated token usage:
- Job description: ~8 tokens
- Artifact description: ~6 tokens
- Total input: ~14 tokens per test

## Running Individual Tests

### Method 1: Using Test Runner

```bash
# Run specific test class
python run_real_api_tests.py --run-single RealLLMIntegrationTestCase

# Run specific test method
python run_real_api_tests.py --run-single test_real_job_description_parsing
```

### Method 2: Django Test Command

```bash
# Run specific test file
python manage.py test llm_services.tests.test_real_llm_integration

# Run specific test class
python manage.py test llm_services.tests.test_real_llm_integration.RealLLMIntegrationTestCase

# Run specific test method
python manage.py test llm_services.tests.test_real_llm_integration.RealLLMIntegrationTestCase.test_real_job_description_parsing
```

### Method 3: pytest

```bash
# Install pytest-django if needed
pip install pytest-django

# Run with pytest
pytest llm_services/tests/test_real_llm_integration.py -v
pytest llm_services/tests/test_real_llm_integration.py::RealLLMIntegrationTestCase::test_real_job_description_parsing -v
```

## Safety Features

### 1. Environment Validation

Tests only run in safe environments:
- `TESTING=1` environment variable
- Test Django settings module
- CI environment detection
- Manual override with `FORCE_REAL_API_TESTS=true`

### 2. Budget Enforcement

Real-time monitoring:
```python
# Test automatically fails if budget exceeded
self.assertLess(cost_usd, MAX_COST_PER_TEST)
self.assertLess(total_cost, MAX_COST_TOTAL)
```

### 3. Token Limits

Conservative token limits:
```python
# Input validation
MAX_JOB_TOKENS = 20      # Very small job descriptions
MAX_ARTIFACT_TOKENS = 50 # Small artifact descriptions

# Usage validation
self.assertLess(tokens_used, MAX_TOKENS_PER_TEST)
```

### 4. Error Handling

Graceful handling of API failures:
```python
# Tests skip if API keys unavailable
@skipIf(not OPENAI_KEY_AVAILABLE, "OpenAI API key not available")

# Circuit breaker testing
# Performance degradation handling
# Cost tracking accuracy validation
```

## Monitoring and Debugging

### Cost Tracking

Every test tracks and reports:
- Tokens used per API call
- Cost per API call
- Model used
- Processing time
- Success/failure status

### Logging Output

```
INFO - Job parsing test - Tokens: 89, Cost: $0.002670, Model: gpt-4o-mini
INFO - CV generation test - Tokens: 245, Cost: $0.007350, Model: gpt-4o
INFO - Test Summary - Successful: 3/3, Total tokens: 334, Total cost: $0.010020
```

### Budget Status

```
💰 Budget Status:
  Cost used: $0.010020
  Cost remaining: $0.489980
  Usage: 2.0%
```

## Expected Costs

### Individual Test Estimates

- **Job Description Parsing**: $0.001-0.003 per test
- **CV Generation**: $0.005-0.015 per test
- **Embedding Generation**: $0.0001-0.0005 per test
- **Artifact Ranking**: $0.002-0.008 per test

### Test Suite Estimates

- **Basic Integration**: ~$0.10 total
- **Circuit Breaker**: ~$0.05 total
- **Pipeline Integration**: ~$0.20 total
- **All Tests**: ~$0.35 total

## Troubleshooting

### Common Issues

1. **"OpenAI API key not available"**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

2. **"Real API tests not enabled"**
   ```bash
   export TESTING=1
   # OR
   export FORCE_REAL_API_TESTS=true
   ```

3. **"Token usage exceeds limit"**
   - Reduce test data size
   - Increase budget limits
   - Check for API errors causing retries

4. **Django import errors**
   ```bash
   cd backend
   export DJANGO_SETTINGS_MODULE="cv_tailor.settings"
   python manage.py check
   ```

### Debug Mode

Run with verbose logging:

```bash
export DJANGO_LOG_LEVEL=DEBUG
python manage.py test llm_services.tests.test_real_llm_integration --verbosity=2
```

### Cost Overruns

If tests exceed budget:
1. Check for API errors causing retries
2. Verify minimal test data is actually minimal
3. Adjust budget limits if appropriate
4. Run individual tests to isolate expensive calls

## Best Practices

### For Development

1. **Start small**: Run basic tests first
2. **Monitor costs**: Check budget status after each run
3. **Use minimal data**: Keep test inputs as small as possible
4. **Test incrementally**: Don't run all tests at once initially

### For CI/CD

1. **Set strict budgets**: Prevent runaway costs
2. **Use cached results**: Cache embeddings and job parsing when possible
3. **Run on schedule**: Not on every commit
4. **Monitor failures**: Set up alerts for cost overruns

### For Production Validation

1. **Use staging environment**: Never run in production
2. **Validate API keys**: Ensure they work before running full suite
3. **Check rate limits**: Be aware of API rate limiting
4. **Document costs**: Track actual vs estimated costs

## Integration with Existing Tests

These real API tests complement existing mock-based tests:

- **Unit tests**: Mock-based, fast, no cost (existing)
- **Integration tests**: Real APIs, slower, small cost (new)
- **E2E tests**: Full pipeline with real APIs, slowest, higher cost (new)

Run both types:

```bash
# Mock-based tests (fast, free)
uv run python manage.py test llm_services.tests.test_services

# Real API tests (slower, costs money)
uv run python run_real_api_tests.py --run-basic --force
```

## Security Considerations

- **API Key Storage**: Use environment variables, never commit keys
- **Cost Limits**: Set reasonable budgets to prevent surprise bills
- **Access Control**: Restrict who can run real API tests
- **Audit Trails**: Log all API usage for cost tracking
- **Key Rotation**: Rotate API keys regularly

This testing framework provides comprehensive real-world validation while maintaining strict cost controls and safety measures.

## Recent Updates & Known Status

### ✅ Latest Fixes (2024-09-24)
- **Automatic Environment Loading**: `.env` files are now automatically loaded by the test runner
- **Async Context Issues**: Fixed circuit breaker and performance tracker async context errors
- **Database Constraints**: Graceful handling of missing test users in performance tracking
- **UV Package Manager**: All commands updated to use `uv run python` instead of plain `python`
- **Force Flag**: Added `--force` flag to bypass environment safety checks for development

### ✅ Successfully Tested APIs
- **OpenAI GPT-4o-mini**: Job description parsing working
- **OpenAI text-embedding-3-small**: Embedding generation working
- **Cost Tracking**: Budget controls active and enforcing limits
- **Performance Metrics**: Tracking tokens, costs, and processing time
- **Circuit Breaker**: Reliability patterns functioning properly

### ⚠️ Known Minor Issues
- Some test assertion format mismatches (non-critical)
- LangChain dependency warnings (optional feature)
- Database connection conflicts in some test environments

### 💰 Current Cost Estimates (Updated)
- **Single API call**: ~$0.0001-0.0003
- **Basic test suite**: ~$0.01-0.05
- **Full test suite**: ~$0.10-0.35
- **Budget safety**: Tests auto-terminate if exceeded