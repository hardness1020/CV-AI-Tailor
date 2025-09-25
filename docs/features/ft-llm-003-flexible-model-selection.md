# Feature — LLM-003 Flexible Model Selection & Configuration System

**Feature ID:** ft-llm-003
**Title:** Intelligent Model Selection with Latest AI Models
**Status:** Pending - Documentation Complete
**Priority:** P1 (Core Enhancement)
**Owner:** Backend Team
**Target Date:** 2024-10-15
**Sprint:** LLM Enhancement Sprint 2

## Overview

Replace the current hardcoded LLM service with a flexible, intelligent model selection system that supports the latest AI models (GPT-4o, Claude Sonnet 4, Claude Opus 4.1) with environment-based configuration, automatic cost optimization, performance tracking, and seamless model switching.

## Links

- **ADR**: [adr-20240924-llm-provider-selection.md](../adrs/adr-20240924-llm-provider-selection.md)
- **Related Features**: [ft-llm-001-content-extraction.md](./ft-llm-001-content-extraction.md), [ft-llm-002-embedding-storage.md](./ft-llm-002-embedding-storage.md)

## Current State Analysis

### Existing Implementation Issues
- **Hardcoded Models**: Uses outdated `gpt-3.5-turbo`, `gpt-4`, `claude-3-haiku-20240307`
- **No Cost Optimization**: No model selection based on task complexity or budget
- **Limited Fallback**: Simple provider fallback without intelligent model selection
- **No Performance Tracking**: No metrics on model performance, cost, or quality
- **No Embedding Service**: Missing semantic similarity capabilities for artifact ranking

### Current Code Structure
```python
# Current hardcoded approach in generation/llm_service.py
class LLMService:
    def parse_job_description(self):
        # Hardcoded: gpt-3.5-turbo → claude-3-haiku-20240307

    def generate_cv_content(self):
        # Hardcoded: gpt-4 → claude-3-sonnet-20240229
```

## New Architecture Design

### 1. Flexible Model Configuration System

```python
# New intelligent model selection architecture
class FlexibleLLMService:
    def __init__(self):
        self.model_registry = ModelRegistry()
        self.performance_tracker = ModelPerformanceTracker()
        self.cost_optimizer = CostOptimizer()
        self.circuit_breaker = CircuitBreaker()

    def select_optimal_model(self, task_type: str, content_complexity: int,
                           user_preferences: dict) -> ModelConfig:
        """Intelligently select best model based on multiple factors"""

# Model Registry with latest models (2025)
MODEL_REGISTRY = {
    "chat_models": {
        "gpt-4o": {
            "provider": "openai",
            "cost_input": 0.0025,   # $2.50 per MTok
            "cost_output": 0.01,    # $10 per MTok
            "context_window": 128000,
            "strengths": ["speed", "cost_efficiency", "structured_output"],
            "best_for": ["general", "fast_processing"]
        },
        "gpt-4o-mini": {
            "provider": "openai",
            "cost_input": 0.00015,  # $0.15 per MTok
            "cost_output": 0.0006,  # $0.60 per MTok
            "context_window": 128000,
            "strengths": ["ultra_cheap", "ultra_fast"],
            "best_for": ["simple_tasks", "high_volume"]
        },
        "claude-sonnet-4-20250514": {
            "provider": "anthropic",
            "cost_input": 0.003,    # $3 per MTok
            "cost_output": 0.015,   # $15 per MTok
            "context_window": 200000,
            "strengths": ["reasoning", "analysis", "long_context"],
            "best_for": ["complex_analysis", "detailed_generation"]
        },
        "claude-opus-4-1-20250805": {
            "provider": "anthropic",
            "cost_input": 0.015,    # $15 per MTok
            "cost_output": 0.075,   # $75 per MTok
            "context_window": 200000,
            "strengths": ["complex_reasoning", "creativity", "accuracy"],
            "best_for": ["premium_quality", "complex_reasoning"]
        }
    },
    "embedding_models": {
        "text-embedding-3-small": {
            "provider": "openai",
            "cost": 0.00002,        # $0.02 per MTok
            "dimensions": 1536,
            "best_for": ["cost_optimized", "high_volume"]
        },
        "text-embedding-3-large": {
            "provider": "openai",
            "cost": 0.00013,        # $0.13 per MTok
            "dimensions": 3072,
            "best_for": ["quality_optimized", "semantic_analysis"]
        }
    }
}
```

### 2. Environment-Based Configuration

```python
# settings.py - Environment-driven model selection
# Model Selection Strategy
MODEL_SELECTION_STRATEGY = config('MODEL_SELECTION_STRATEGY', default='balanced')

# Strategy Configurations
MODEL_STRATEGIES = {
    'cost_optimized': {
        'job_parsing_model': 'gpt-4o-mini',
        'cv_generation_model': 'gpt-4o',
        'embedding_model': 'text-embedding-3-small',
        'max_cost_per_generation': 0.05,  # $0.05 per CV
        'fallback_model': 'gpt-4o-mini'
    },
    'balanced': {
        'job_parsing_model': 'gpt-4o',
        'cv_generation_model': 'gpt-4o',
        'embedding_model': 'text-embedding-3-small',
        'max_cost_per_generation': 0.15,  # $0.15 per CV
        'fallback_model': 'claude-sonnet-4-20250514'
    },
    'quality_optimized': {
        'job_parsing_model': 'claude-sonnet-4-20250514',
        'cv_generation_model': 'claude-opus-4-1-20250805',
        'embedding_model': 'text-embedding-3-large',
        'max_cost_per_generation': 0.50,  # $0.50 per CV
        'fallback_model': 'claude-sonnet-4-20250514'
    },
    'experimental': {
        'job_parsing_model': 'claude-opus-4-1-20250805',
        'cv_generation_model': 'claude-opus-4-1-20250805',
        'embedding_model': 'text-embedding-3-large',
        'max_cost_per_generation': 1.00,  # $1.00 per CV
        'fallback_model': 'gpt-4o'
    }
}

# Provider API Keys
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY', default='')

# Model Performance Tracking
TRACK_MODEL_PERFORMANCE = config('TRACK_MODEL_PERFORMANCE', default=True, cast=bool)
MODEL_PERFORMANCE_LOG_LEVEL = config('MODEL_PERFORMANCE_LOG_LEVEL', default='INFO')
```

### 3. Intelligent Model Selection Logic

```python
class IntelligentModelSelector:
    def __init__(self):
        self.strategy = settings.MODEL_STRATEGIES[settings.MODEL_SELECTION_STRATEGY]

    def select_model_for_task(self, task_type: str, context: dict) -> str:
        """Select optimal model based on task complexity and requirements"""

        if task_type == "job_parsing":
            return self._select_parsing_model(context)
        elif task_type == "cv_generation":
            return self._select_generation_model(context)
        elif task_type == "embedding":
            return self._select_embedding_model(context)

    def _select_parsing_model(self, context: dict) -> str:
        """Select model for job description parsing"""
        job_length = len(context.get('job_description', '').split())

        # For long job descriptions, use higher capability models
        if job_length > 1000:
            return 'claude-sonnet-4-20250514'  # Better long context
        elif job_length < 200:
            return 'gpt-4o-mini'  # Cost efficient for simple jobs
        else:
            return self.strategy['job_parsing_model']  # Default strategy

    def _select_generation_model(self, context: dict) -> str:
        """Select model for CV content generation"""
        artifact_count = len(context.get('artifacts', []))
        complexity_score = self._calculate_complexity_score(context)

        # High complexity or many artifacts = premium model
        if complexity_score > 0.8 or artifact_count > 10:
            if settings.MODEL_SELECTION_STRATEGY in ['quality_optimized', 'experimental']:
                return 'claude-opus-4-1-20250805'
            else:
                return 'claude-sonnet-4-20250514'

        # Medium complexity = balanced model
        elif complexity_score > 0.5:
            return 'gpt-4o'

        # Low complexity = cost efficient model
        else:
            return 'gpt-4o-mini'

    def _select_embedding_model(self, context: dict) -> str:
        """Select embedding model based on use case"""
        use_case = context.get('use_case', 'similarity')

        if use_case in ['semantic_analysis', 'complex_matching']:
            return 'text-embedding-3-large'  # Higher quality
        else:
            return 'text-embedding-3-small'  # Cost efficient

    def _calculate_complexity_score(self, context: dict) -> float:
        """Calculate task complexity (0-1)"""
        score = 0.0

        # Job description complexity
        job_desc = context.get('job_description', '')
        if len(job_desc.split()) > 500:
            score += 0.3

        # Number of artifacts
        artifact_count = len(context.get('artifacts', []))
        score += min(0.4, artifact_count * 0.05)

        # Special requirements
        if context.get('requires_creative_writing', False):
            score += 0.3

        return min(1.0, score)
```

### 4. Enhanced LLM Service with Model Selection

```python
class EnhancedLLMService:
    def __init__(self):
        self.model_selector = IntelligentModelSelector()
        self.performance_tracker = ModelPerformanceTracker()
        self.cost_tracker = CostTracker()
        self.circuit_breaker = CircuitBreaker()

    async def parse_job_description(self, job_description: str,
                                  company_name: str = "",
                                  role_title: str = "") -> Dict[str, Any]:
        """Enhanced job parsing with intelligent model selection"""

        context = {
            'job_description': job_description,
            'company_name': company_name,
            'role_title': role_title
        }

        selected_model = self.model_selector.select_model_for_task('job_parsing', context)
        start_time = time.time()

        try:
            # Use LiteLLM for unified API
            response = await completion(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You are a job description parser. Return only valid JSON."},
                    {"role": "user", "content": self._build_parsing_prompt(context)}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            processing_time = time.time() - start_time
            result = json.loads(response.choices[0].message.content)

            # Track performance
            self.performance_tracker.record_task(
                model=selected_model,
                task_type='job_parsing',
                processing_time_ms=processing_time * 1000,
                tokens_used=response.usage.total_tokens,
                success=True,
                quality_score=result.get('confidence_score', 0.5)
            )

            # Track cost
            cost = self.cost_tracker.calculate_cost(
                model=selected_model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens
            )

            return {
                **result,
                'processing_metadata': {
                    'model_used': selected_model,
                    'processing_time_ms': processing_time * 1000,
                    'tokens_used': response.usage.total_tokens,
                    'cost_usd': cost,
                    'selection_reason': self.model_selector.get_selection_reason(selected_model, context)
                }
            }

        except Exception as e:
            # Circuit breaker and fallback logic
            self.circuit_breaker.record_failure(selected_model)

            if self.circuit_breaker.should_use_fallback(selected_model):
                fallback_model = self.strategy['fallback_model']
                return await self._retry_with_fallback(fallback_model, context, 'job_parsing')

            raise

    async def generate_cv_content(self, job_data: Dict[str, Any],
                                artifacts: List[Dict[str, Any]],
                                preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhanced CV generation with intelligent model selection"""

        context = {
            'job_description': job_data.get('raw_job_description', ''),
            'artifacts': artifacts,
            'preferences': preferences or {},
            'requires_creative_writing': preferences.get('tone') == 'creative' if preferences else False
        }

        selected_model = self.model_selector.select_model_for_task('cv_generation', context)
        start_time = time.time()

        try:
            prompt = self._build_cv_generation_prompt(job_data, artifacts, preferences)

            response = await completion(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You are a professional CV writer. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2500
            )

            processing_time = time.time() - start_time
            result = json.loads(response.choices[0].message.content)

            # Calculate quality metrics
            quality_score = self._calculate_cv_quality_score(result, job_data)

            # Track performance
            self.performance_tracker.record_task(
                model=selected_model,
                task_type='cv_generation',
                processing_time_ms=processing_time * 1000,
                tokens_used=response.usage.total_tokens,
                success=True,
                quality_score=quality_score
            )

            cost = self.cost_tracker.calculate_cost(
                model=selected_model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens
            )

            return {
                'content': result,
                'processing_metadata': {
                    'model_used': selected_model,
                    'processing_time_ms': processing_time * 1000,
                    'tokens_used': response.usage.total_tokens,
                    'cost_usd': cost,
                    'quality_score': quality_score,
                    'selection_reason': self.model_selector.get_selection_reason(selected_model, context),
                    'complexity_score': self.model_selector._calculate_complexity_score(context)
                }
            }

        except Exception as e:
            self.circuit_breaker.record_failure(selected_model)

            if self.circuit_breaker.should_use_fallback(selected_model):
                fallback_model = self.strategy['fallback_model']
                return await self._retry_with_fallback(fallback_model, context, 'cv_generation')

            raise
```

### 5. Embedding Service with Model Selection

```python
class FlexibleEmbeddingService:
    def __init__(self):
        self.model_selector = IntelligentModelSelector()
        self.cost_tracker = CostTracker()

    async def generate_embeddings(self, texts: List[str],
                                use_case: str = 'similarity') -> List[Dict[str, Any]]:
        """Generate embeddings with intelligent model selection"""

        context = {'use_case': use_case, 'text_count': len(texts)}
        selected_model = self.model_selector.select_model_for_task('embedding', context)

        try:
            response = await embedding(
                model=selected_model,
                input=texts
            )

            results = []
            total_cost = self.cost_tracker.calculate_embedding_cost(
                model=selected_model,
                tokens=response.usage.total_tokens
            )

            for i, embedding_data in enumerate(response.data):
                results.append({
                    'embedding': embedding_data.embedding,
                    'model_used': selected_model,
                    'dimensions': len(embedding_data.embedding),
                    'text_index': i,
                    'cost_share_usd': total_cost / len(texts)
                })

            return results

        except Exception as e:
            logger.error(f"Embedding generation failed with {selected_model}: {e}")
            raise
```

## Implementation Plan

### Phase 1: Model Registry & Configuration (Week 1)
1. **Environment Configuration**
   - Add new model strategy settings to `settings.py`
   - Create model registry with latest models and pricing
   - Set up environment variable configuration

2. **Base Classes**
   - Create `ModelRegistry` class
   - Implement `IntelligentModelSelector`
   - Build `ModelPerformanceTracker` foundation

### Phase 2: Enhanced LLM Service (Week 2)
3. **LiteLLM Integration**
   - Install and configure LiteLLM for unified API
   - Replace direct OpenAI/Anthropic calls
   - Implement circuit breaker pattern

4. **Enhanced Services**
   - Create new `EnhancedLLMService`
   - Implement `FlexibleEmbeddingService`
   - Add intelligent model selection logic

### Phase 3: Performance & Cost Tracking (Week 3)
5. **Monitoring Systems**
   - Implement cost tracking across all models
   - Add performance metrics collection
   - Create quality scoring system

6. **Optimization Features**
   - Add automatic model selection based on performance
   - Implement cost budget controls
   - Create fallback and retry mechanisms

### Phase 4: Integration & Migration (Week 4)
7. **API Updates**
   - Update existing endpoints to use new service
   - Add model selection info to API responses
   - Implement model performance endpoints

8. **Migration Strategy**
   - Gradual rollout with feature flags
   - A/B testing between old and new systems
   - Performance comparison and optimization

## API Changes

### Enhanced Generation Response
```typescript
// Updated CV generation response
{
  "content": { /* CV content */ },
  "processing_metadata": {
    "model_used": "gpt-4o",
    "processing_time_ms": 1200,
    "tokens_used": 1500,
    "cost_usd": 0.0375,
    "quality_score": 0.87,
    "selection_reason": "balanced_strategy_general_complexity",
    "complexity_score": 0.6,
    "fallback_used": false
  }
}
```

### New Model Performance Endpoint
```typescript
GET /api/v1/models/performance/
Response: {
  "model_performance": {
    "gpt-4o": {
      "avg_processing_time_ms": 1200,
      "avg_cost_per_generation": 0.035,
      "avg_quality_score": 0.89,
      "success_rate": 0.98,
      "total_generations": 1250
    },
    "claude-sonnet-4-20250514": {
      "avg_processing_time_ms": 1800,
      "avg_cost_per_generation": 0.085,
      "avg_quality_score": 0.92,
      "success_rate": 0.97,
      "total_generations": 450
    }
  },
  "recommendations": {
    "cost_leader": "gpt-4o-mini",
    "quality_leader": "claude-opus-4-1-20250805",
    "balanced_choice": "gpt-4o"
  }
}
```

### Model Selection Settings Endpoint
```typescript
GET /api/v1/models/settings/
Response: {
  "current_strategy": "balanced",
  "available_strategies": ["cost_optimized", "balanced", "quality_optimized", "experimental"],
  "available_models": {
    "chat": ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-20250514", "claude-opus-4-1-20250805"],
    "embedding": ["text-embedding-3-small", "text-embedding-3-large"]
  }
}

PUT /api/v1/models/settings/
Request: {
  "strategy": "quality_optimized"
}
```

## Database Schema Updates

```sql
-- Model performance tracking
CREATE TABLE model_performance_metrics (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    processing_time_ms INTEGER NOT NULL,
    tokens_used INTEGER NOT NULL,
    cost_usd DECIMAL(10,6) NOT NULL,
    quality_score DECIMAL(3,2),
    success BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add model metadata to existing tables
ALTER TABLE generation_generateddocument
ADD COLUMN model_selection_strategy VARCHAR(50),
ADD COLUMN model_metadata JSONB DEFAULT '{}',
ADD COLUMN total_cost_usd DECIMAL(10,6) DEFAULT 0.0;

-- Cost tracking and budgets
CREATE TABLE model_cost_tracking (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    date DATE NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    total_cost_usd DECIMAL(10,6) NOT NULL,
    generation_count INTEGER NOT NULL,
    avg_cost_per_generation DECIMAL(10,6) NOT NULL
);
```

## Cost Analysis & Budgeting

### Model Cost Comparison (1000 CV Generations)
| Strategy | Primary Model | Avg Tokens | Cost per 1000 | Quality Score |
|----------|---------------|------------|---------------|---------------|
| Cost Optimized | gpt-4o-mini | 1500 | $2.25 | 0.82 |
| Balanced | gpt-4o | 1800 | $45.00 | 0.89 |
| Quality Optimized | claude-opus-4-1 | 2000 | $180.00 | 0.94 |
| Experimental | claude-opus-4-1 | 2200 | $198.00 | 0.96 |

### Budget Controls
```python
# settings.py budget configuration
MODEL_BUDGETS = {
    'daily_budget_usd': 50.0,
    'monthly_budget_usd': 1000.0,
    'max_cost_per_user_daily': 5.0,
    'cost_alert_threshold': 0.8  # Alert at 80% of budget
}
```

## Testing Strategy

### Unit Tests
- Model selection logic with various complexity scores
- Cost calculation accuracy across all models
- Circuit breaker functionality
- Performance tracking metrics

### Integration Tests
- End-to-end CV generation with different strategies
- Model fallback scenarios
- API response format validation
- Cost budget enforcement

### Performance Tests
- Model response time comparison
- Concurrent request handling
- Memory usage under load
- Cost tracking accuracy

### A/B Testing Plan
- 25% of users on cost_optimized strategy
- 50% of users on balanced strategy
- 20% of users on quality_optimized strategy
- 5% of users on experimental strategy

## Monitoring & Alerting

### Key Metrics
- **Model Performance**: Response time, success rate, quality scores
- **Cost Tracking**: Daily/monthly spend, cost per generation, budget utilization
- **User Experience**: Generation success rate, user satisfaction scores
- **System Health**: API rate limits, circuit breaker states, error rates

### Alerting Thresholds
- Model response time > 5 seconds p95
- Model failure rate > 5%
- Daily cost budget > 80% utilized
- Quality score drops below 0.8 for any strategy

## Success Metrics

### Performance Goals
- **Response Time**: <2s p95 for balanced strategy, <1s for cost_optimized
- **Quality Score**: >0.85 for balanced, >0.90 for quality_optimized
- **Cost Efficiency**: 30% cost reduction vs current hardcoded approach
- **Reliability**: 99%+ success rate across all strategies

### Business Impact
- **User Satisfaction**: 90%+ users satisfied with CV quality
- **Cost Control**: Stay within monthly LLM budget
- **Feature Adoption**: 80%+ users actively use model selection
- **Quality Improvement**: 25% improvement in CV relevance scores

## Future Enhancements

### Planned Improvements
- **Fine-tuned Models**: Custom models trained on CV generation data
- **Multi-modal Capabilities**: Integration with image and document analysis
- **Real-time Optimization**: Dynamic model selection based on live performance
- **Enterprise Features**: Team budgets, model governance, audit trails

### Experimental Features
- **Model Ensembles**: Combine multiple models for higher quality
- **Custom Prompts**: User-defined prompts for specialized use cases
- **Integration APIs**: Third-party model providers beyond OpenAI/Anthropic
- **Advanced Analytics**: ML-driven model selection optimization