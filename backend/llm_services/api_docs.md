# LLM Services API Documentation

This document describes the API endpoints for managing LLM services, including model performance tracking, circuit breaker status, cost monitoring, and embedding management.

## Base URL
All endpoints are prefixed with `/api/v1/llm/`

## Authentication
All endpoints require JWT authentication. Include the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### Model Performance Metrics

#### `GET /performance-metrics/`
Get paginated list of model performance metrics.

**Query Parameters:**
- `model_name` (string): Filter by specific model
- `task_type` (string): Filter by task type (job_parsing, cv_generation, embedding, similarity_search)
- `success` (boolean): Filter by success status
- `selection_strategy` (string): Filter by selection strategy
- `date_from` (string): Filter from date (YYYY-MM-DD)
- `date_to` (string): Filter to date (YYYY-MM-DD)
- `page` (integer): Page number
- `page_size` (integer): Items per page (max 100)

**Response:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/llm/performance-metrics/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid-here",
      "model_name": "gpt-4o",
      "task_type": "cv_generation",
      "processing_time_ms": 1250,
      "tokens_used": 850,
      "cost_usd": "0.008500",
      "quality_score": "0.85",
      "success": true,
      "complexity_score": "0.60",
      "selection_strategy": "balanced",
      "fallback_used": false,
      "metadata": {},
      "created_at": "2025-01-15T10:30:00Z",
      "user_email": "user@example.com"
    }
  ]
}
```

#### `GET /performance-metrics/summary/`
Get performance summary for today and yesterday.

**Response:**
```json
{
  "today": {
    "total_requests": 25,
    "success_rate": 96.0,
    "avg_cost": 0.008,
    "total_cost": 0.2
  },
  "yesterday": {
    "total_requests": 18,
    "success_rate": 94.4,
    "avg_cost": 0.009,
    "total_cost": 0.162
  }
}
```

### Circuit Breaker Management

#### `GET /circuit-breakers/`
Get all circuit breaker states.

**Response:**
```json
[
  {
    "model_name": "gpt-4o",
    "failure_count": 0,
    "last_failure": null,
    "state": "closed",
    "state_display": "Closed",
    "failure_threshold": 5,
    "timeout_duration": 30,
    "created_at": "2025-01-15T08:00:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "is_healthy": true
  }
]
```

#### `POST /circuit-breakers/{model_name}/reset/`
Reset a specific circuit breaker.

**Response:**
```json
{
  "message": "Circuit breaker for gpt-4o has been reset",
  "new_state": "closed"
}
```

#### `GET /circuit-breakers/health_status/`
Get overall health status of all models.

**Response:**
```json
{
  "total_models": 6,
  "healthy_models": 5,
  "unhealthy_models": 1,
  "models_by_state": {
    "closed": 5,
    "open": 1,
    "half_open": 0
  },
  "recent_failures": [
    {
      "model_name": "claude-opus-4.1",
      "failure_count": 3,
      "last_failure": "2025-01-15T09:45:00Z",
      "state": "open"
    }
  ]
}
```

### Cost Tracking

#### `GET /cost-tracking/`
Get paginated cost tracking data.

**Query Parameters:**
- `model_name` (string): Filter by model
- `date` (string): Filter by date (YYYY-MM-DD)
- `page` (integer): Page number
- `page_size` (integer): Items per page

**Response:**
```json
{
  "count": 30,
  "results": [
    {
      "id": 1,
      "user_email": "user@example.com",
      "date": "2025-01-15",
      "model_name": "gpt-4o",
      "total_cost_usd": "0.125000",
      "generation_count": 15,
      "avg_cost_per_generation": "0.008333",
      "total_tokens_used": 12500,
      "avg_tokens_per_generation": 833
    }
  ]
}
```

#### `GET /cost-tracking/monthly_summary/`
Get monthly cost summary by model.

**Response:**
```json
{
  "month": "2025-01",
  "models": [
    {
      "model_name": "gpt-4o",
      "total_cost": 2.5,
      "total_generations": 300,
      "avg_cost_per_generation": 0.0083
    }
  ]
}
```

### Job Embeddings

#### `GET /job-embeddings/`
Get paginated job description embeddings.

#### `GET /job-embeddings/cache_stats/`
Get embedding cache statistics.

**Response:**
```json
{
  "total_embeddings": 150,
  "unique_companies": 45,
  "total_access_count": 890,
  "cache_hit_rate": 85.5,
  "most_accessed": [
    {
      "role_title": "Senior Software Engineer",
      "company_name": "Tech Corp",
      "access_count": 25
    }
  ],
  "recent_embeddings": [
    {
      "role_title": "Data Scientist",
      "company_name": "AI Startup",
      "created_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

### Enhanced Artifacts

#### `GET /enhanced-artifacts/`
Get paginated enhanced artifacts with processing metadata.

#### `GET /enhanced-artifacts/{id}/chunks/`
Get all chunks for a specific artifact.

**Response:**
```json
[
  {
    "id": "uuid-here",
    "artifact_title": "My Resume",
    "chunk_index": 0,
    "content": "Experienced software engineer...",
    "metadata": {"section": "experience"},
    "content_hash": "abc123...",
    "model_used": "text-embedding-3-small",
    "tokens_used": 150,
    "processing_cost_usd": "0.000015",
    "created_at": "2025-01-15T09:00:00Z"
  }
]
```

### Model Management

#### `GET /model-stats/`
Get aggregated statistics for all models.

**Response:**
```json
[
  {
    "model_name": "gpt-4o",
    "total_requests": 150,
    "success_rate": 96.0,
    "avg_processing_time_ms": 1250.5,
    "total_cost_usd": "1.275000",
    "avg_quality_score": 0.85,
    "last_used": "2025-01-15T10:30:00Z"
  }
]
```

#### `POST /select-model/`
Select the best model for a given task.

**Request Body:**
```json
{
  "task_type": "cv_generation",
  "complexity_score": 0.7,
  "user_budget": 0.05,
  "strategy": "balanced"
}
```

**Response:**
```json
{
  "selected_model": "gpt-4o",
  "reasoning": "Selected GPT-4o for balanced performance and cost for complex CV generation task",
  "estimated_cost_usd": "0.025000",
  "fallback_models": ["gpt-4o-mini", "claude-sonnet-4"]
}
```

#### `GET /system-health/`
Get overall system health status.

**Response:**
```json
{
  "healthy_models": 5,
  "unhealthy_models": 1,
  "circuit_breakers_open": 1,
  "total_cost_today": "0.45",
  "avg_response_time_ms": 1150.2,
  "success_rate": 95.5
}
```

#### `GET /available-models/`
Get list of all available models and their configurations.

**Response:**
```json
{
  "gpt-4o": {
    "provider": "openai",
    "context_window": 128000,
    "output_tokens": 16384,
    "input_cost_per_token": 0.0000025,
    "output_cost_per_token": 0.00001,
    "capabilities": ["text_generation", "analysis"],
    "circuit_breaker_status": "closed",
    "is_available": true
  }
}
```

## Task Types
- `job_parsing`: Parsing job descriptions
- `cv_generation`: Generating CV content
- `embedding`: Creating text embeddings
- `similarity_search`: Semantic similarity operations

## Selection Strategies
- `cost_optimized`: Prioritize lowest cost models
- `balanced`: Balance cost and performance
- `performance_first`: Prioritize highest quality models

## Error Responses

All endpoints return standard HTTP status codes:
- `400`: Bad Request - Invalid parameters
- `401`: Unauthorized - Missing or invalid authentication
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource doesn't exist
- `500`: Internal Server Error - Server error

Error response format:
```json
{
  "error": "Description of the error",
  "details": "Additional error details if available"
}
```

## Rate Limiting
API endpoints are subject to rate limiting. Check the response headers:
- `X-RateLimit-Limit`: Request limit per time window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Pagination
Most list endpoints support pagination with these parameters:
- `page`: Page number (starts at 1)
- `page_size`: Items per page (default: 20, max: 100)

Response includes pagination metadata:
- `count`: Total number of items
- `next`: URL for next page (null if last page)
- `previous`: URL for previous page (null if first page)