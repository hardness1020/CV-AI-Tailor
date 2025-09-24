# Tech Spec — Enhanced LLM Artifact Processing System

**Version**: v1.0.0
**File:** docs/specs/spec-20240924-llm-artifacts.md
**Status:** Draft
**PRD:** N/A (Technical Enhancement)
**Contract Versions:** API v1.4  •  Schema v1.2  •  LLM Pipeline v2.0

## Overview & Goals

Enhance CV Tailor's artifact processing system to intelligently extract, analyze, and rank multi-format user artifacts (PDFs, GitHub repos, profile links) using LLM-powered content analysis for superior CV generation quality.

**Key Objectives:**
- Unified content extraction from multi-format artifacts
- Semantic relevance ranking using embeddings
- LLM-powered content summarization and achievement extraction
- 3-stage LLM pipeline replacing simple keyword matching

## Architecture (Detailed)

### Topology (frameworks)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Artifact      │    │   Content       │    │   LLM Service   │
│   Upload        │───▶│   Extractor     │───▶│   Pipeline      │
│   (Django)      │    │   (LangChain)   │    │   (OpenAI/      │
│                 │    │                 │    │   Anthropic)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Storage  │    │   Artifact      │    │   Vector Store  │
│   (Django)      │    │   Processing    │    │   (Redis/      │
│                 │    │   Jobs (Celery) │    │   Future)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Inventory

| Component | Framework/Runtime | Purpose | Interfaces (in/out) | Depends On | Scale/HA | Owner |
|-----------|-------------------|---------|-------------------|------------|----------|-------|
| Content Extractor | LangChain Python | Multi-format document processing | In: Files/URLs; Out: Structured content | LangChain, PyPDF2 | Queue-based scaling | BE |
| LLM Pipeline | OpenAI/Anthropic APIs | Content analysis, summarization, ranking | In: Raw content; Out: Processed summaries | External LLM APIs | API rate limits | BE |
| Artifact Processor | Celery Python | Async content processing orchestration | In: Processing jobs; Out: Enriched artifacts | Redis, LLM Service | Worker autoscaling | BE |
| Embedding Service | OpenAI Embeddings | Semantic similarity calculation | In: Text; Out: Vector embeddings | OpenAI API | External | BE |
| Vector Storage | PostgreSQL + pgvector | Embedding storage and similarity search | In: Vectors; Out: Similarity results | PostgreSQL | Primary + replica | BE |
| Enhanced Generator | Django/Python | Improved CV generation | In: Job + Enriched artifacts; Out: Tailored CV | LLM Service, Vector DB | Stateless scaling | BE |

## Interfaces & Data Contracts

### Enhanced Artifact Model
```python
class Artifact(models.Model):
    # Existing fields...

    # New LLM-enhanced fields
    content_summary = models.TextField(blank=True)  # LLM-generated summary
    extracted_achievements = models.JSONField(default=list)  # Quantified achievements
    skill_embeddings = models.JSONField(default=dict)  # Cached embeddings
    content_quality_score = models.FloatField(default=0.0)  # LLM-assessed quality
    last_llm_processed = models.DateTimeField(null=True, blank=True)
```

### New Processing Pipeline API
```
POST /api/v1/artifacts/{id}/enhance/
Body: {"force_reprocess": false}
Response: {"processing_job_id": "uuid", "estimated_completion": "timestamp"}

GET /api/v1/artifacts/{id}/enhanced-content/
Response: {
    "content_summary": "LLM summary",
    "achievements": ["achievement1", ...],
    "technologies_extracted": ["tech1", ...],
    "quality_score": 8.5,
    "relevance_to_jobs": [{"job_hash": "hash", "score": 0.85}, ...]
}
```

## Data & Storage

### New Tables
```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enhanced artifact content storage with vector embeddings
CREATE TABLE artifact_content_cache (
    id SERIAL PRIMARY KEY,
    artifact_id INTEGER REFERENCES artifacts_artifact(id),
    content_type VARCHAR(50),  -- 'pdf', 'github', 'web'
    raw_content TEXT,
    processed_content JSONB,
    content_embedding VECTOR(1536),  -- OpenAI embeddings
    processing_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create vector similarity index
CREATE INDEX artifact_content_embedding_idx ON artifact_content_cache
USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 100);

-- Job description embeddings for similarity matching
CREATE TABLE job_description_embeddings (
    id SERIAL PRIMARY KEY,
    job_description_id INTEGER REFERENCES generation_jobdescription(id),
    content_hash VARCHAR(64),
    requirements_embedding VECTOR(1536),
    responsibilities_embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for job embeddings
CREATE INDEX job_requirements_embedding_idx ON job_description_embeddings
USING ivfflat (requirements_embedding vector_cosine_ops) WITH (lists = 100);

-- LLM processing audit log
CREATE TABLE llm_processing_log (
    id SERIAL PRIMARY KEY,
    artifact_id INTEGER REFERENCES artifacts_artifact(id),
    processing_stage VARCHAR(50),  -- 'extract', 'summarize', 'rank'
    llm_provider VARCHAR(20),  -- 'openai', 'anthropic'
    token_usage INTEGER,
    processing_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Migration Strategy

**Prerequisites**:
- **Database Migration**: SQLite → PostgreSQL (see ADR: `adr-20240924-sqlite-to-postgresql-migration.md`)
- This migration must be completed before vector functionality can be implemented

**Vector Enhancement Migrations**:
- `20241001_install_pgvector.sql` - Install pgvector extension
- `20241001_add_llm_fields.sql` - Add new fields to existing tables
- `20241001_create_content_cache.sql` - Create content cache and embedding tables
- `20241001_create_vector_indexes.sql` - Create vector similarity indexes
- Backward compatible: old artifacts continue working with enhanced processing opt-in

**Migration Sequence**:
1. **Phase 0**: SQLite to PostgreSQL migration (all existing data)
2. **Phase 1**: Add vector support infrastructure
3. **Phase 2**: Enable enhanced processing features

## Reliability & SLIs/SLOs

### SLIs
- **Content Processing Latency**: p95 < 30s for PDF extraction
- **LLM API Success Rate**: > 98% for content summarization
- **Embedding Generation**: p95 < 5s per artifact
- **End-to-End Enhancement**: p95 < 60s from upload to enhanced content

### SLOs
- **Processing Availability**: 99.5% (excluding external LLM downtime)
- **Content Quality**: > 85% user satisfaction with summaries
- **Cost Efficiency**: < $0.50 LLM cost per artifact processing

### Reliability Patterns
- Circuit breakers on LLM APIs (5 failures → 30s circuit open)
- Exponential backoff for rate-limited APIs
- Graceful degradation: fall back to keyword matching if LLM fails
- Content caching to avoid reprocessing

## Security & Privacy

### Data Protection
- **Content Sanitization**: Remove PII from artifact content before LLM processing
- **API Key Management**: Rotate LLM provider keys via environment variables
- **Audit Logging**: Log all LLM interactions with artifact IDs (no content)
- **Rate Limiting**: User-based limits to prevent API abuse

### Privacy Considerations
- User consent for LLM processing of uploaded documents
- Option to exclude specific artifacts from LLM enhancement
- Automatic expiry of cached content summaries (90 days)

## Evaluation Plan

### LLM Performance Metrics
- **Content Extraction Accuracy**: Manual review of 100 sample extractions
- **Relevance Ranking Quality**: A/B test enhanced vs. keyword ranking
- **Summary Quality**: Human evaluation on 5-point scale (target: >4.0)
- **Achievement Extraction**: Precision/Recall on manually labeled dataset

### Test Datasets
- **Golden Set v1**: 50 artifacts across different types (PDF, GitHub, web)
- **Relevance Test Set**: 20 job descriptions × 10 artifacts each
- **Performance Baselines**: Current keyword matching system metrics

### Success Thresholds
- Content extraction: 90% accuracy vs. manual review
- Relevance ranking: 15% improvement in user satisfaction
- Processing latency: <60s p95 for complete enhancement

## Rollout & Ops Impact

### Rollout Strategy
**Phase 0** (Weeks 1-2): Database Infrastructure Migration
1. **Week 1**: SQLite → PostgreSQL migration in development
2. **Week 2**: Production PostgreSQL deployment and data migration

**Phase 1** (Week 3): Content extraction for new uploads only
**Phase 2** (Week 4): LLM summarization with user opt-in
**Phase 3** (Week 5): Enhanced relevance ranking in CV generation
**Phase 4** (Week 6): Batch processing of existing artifacts (user-initiated)

### Feature Flags
- `feature.llm_content_extraction` - Enable LangChain document processing
- `feature.llm_summarization` - Enable LLM-powered content summaries
- `feature.semantic_ranking` - Enable embedding-based relevance ranking
- `feature.batch_enhancement` - Enable bulk artifact enhancement

### Monitoring & Dashboards
- **LLM API Usage**: Token consumption, rate limits, error rates
- **Processing Queue**: Celery task backlog, processing times
- **Content Quality**: User feedback on enhanced summaries
- **Cost Tracking**: LLM API spend per user, per artifact type

## Risks & Rollback

### Primary Risks
1. **LLM API Costs**: Unexpected token usage spikes → implement daily spend limits
2. **Processing Latency**: LLM calls slower than expected → async processing + caching
3. **Content Quality**: LLM summaries inaccurate → human feedback loop + model tuning
4. **External Dependencies**: OpenAI/Anthropic outages → graceful fallback to existing system

### Rollback Plan
- Instant: Disable feature flags to revert to keyword matching
- Content: Cached summaries preserve functionality during API issues
- Database: New fields nullable, can be ignored by existing code
- Full rollback: Migration to drop new tables if needed (data export available)

### Monitoring Alerts
- LLM API error rate > 5% → escalate to on-call
- Processing queue depth > 100 items → autoscale workers
- Cost per artifact > $0.75 → throttle processing and alert

## Open Questions

1. **Database Migration Timeline**: Should we complete PostgreSQL migration before starting any LLM features, or can we do them in parallel?
2. **Model Selection**: Should we fine-tune smaller models vs. using large general-purpose models?
3. **Content Retention**: How long should we cache LLM-processed content vs. reprocessing?
4. **Internationalization**: How do we handle non-English artifacts in LLM processing?

## Changelog

- 2024-09-24: Draft v1.0.0; initial architecture design; LangChain integration plan
- 2024-09-24: Added security considerations and privacy controls
- 2024-09-24: Defined evaluation metrics and rollout phases
- 2024-09-24: Updated to PostgreSQL + pgvector for embedding storage; enhanced schema design
- 2024-09-24: Added prerequisite SQLite → PostgreSQL migration requirement; updated rollout timeline

---

**Next Steps:**
1. Complete SQLite → PostgreSQL migration (see ADR: `adr-20240924-sqlite-to-postgresql-migration.md`)
2. Create feature specification for database migration and Phase 1 implementation
3. Design and test database migration procedures