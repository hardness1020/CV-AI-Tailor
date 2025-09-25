# Feature — LLM-002 PostgreSQL Vector Embedding Storage

**Feature ID:** ft-llm-002
**Title:** PostgreSQL pgvector Embedding Storage & Similarity Search
**Status:** Pending - Documentation Complete
**Priority:** P1 (Core Enhancement)
**Owner:** Backend Team
**Target Date:** 2024-09-30
**Sprint:** LLM Enhancement Sprint 1

## Overview

Implement PostgreSQL with pgvector extension for storing and querying 1536-dimensional OpenAI embeddings, enabling semantic similarity calculations between job requirements and artifact content for intelligent CV generation and artifact ranking.

## Links
- **ADR**: [adr-20240924-embedding-storage-strategy.md](../adrs/adr-20240924-embedding-storage-strategy.md)
- **SPEC**: [spec-20240924-llm-artifacts.md](../specs/spec-20240924-llm-artifacts.md)

## Implementation Status

### Backend ❌ Pending
- ❌ pgvector extension installation and setup
- ❌ Database schema with VECTOR(1536) columns
- ❌ Django model fields for vector operations
- ❌ Similarity search implementation with native functions
- ❌ GIN index creation for efficient queries
- ❌ OpenAI embedding generation integration

### API Development ❌ Pending
- ❌ Embedding generation endpoints
- ❌ Similarity search API endpoints
- ❌ Artifact ranking by semantic relevance
- ❌ Job requirement matching functionality

### Testing ❌ Missing
- ❌ Vector operations unit tests
- ❌ Similarity search performance benchmarks
- ❌ Index optimization testing
- ❌ Large-scale embedding storage tests

## Acceptance Criteria

### Core Vector Operations
- [ ] pgvector extension installed and configured in PostgreSQL
- [ ] VECTOR(1536) columns store OpenAI embeddings efficiently
- [ ] Native similarity functions work: `<->` (L2), `<#>` (inner product), `<=>` (cosine)
- [ ] GIN indexes provide sub-500ms similarity queries at scale
- [ ] Django ORM integration with custom vector field types
- [ ] Raw SQL integration for complex vector operations

### Embedding Generation & Storage
- [ ] Generate embeddings for artifact content using OpenAI API
- [ ] Store embeddings alongside artifact metadata in single transaction
- [ ] Batch embedding generation for efficiency
- [ ] Update embeddings when artifact content changes
- [ ] Embedding versioning for model updates

### Similarity Search & Ranking
- [ ] Find similar artifacts within user's collection (<200 artifacts)
- [ ] Rank artifacts by relevance to job descriptions
- [ ] Real-time similarity search during CV generation
- [ ] Configurable similarity thresholds and result limits
- [ ] Combined keyword + semantic search capabilities

### Performance & Scalability
- [ ] Support 10k+ users with 100k+ total artifacts
- [ ] Similarity queries complete under 500ms p95
- [ ] Vector index maintenance during high write loads
- [ ] Efficient storage with controlled size growth
- [ ] Memory usage optimization for large embedding sets

## API Endpoints

### Embedding Management
```typescript
// Generate embeddings for artifact
POST /api/v1/artifacts/{id}/embeddings/
Request: {
  content_type: "full" | "summary" | "chunks",
  force_regenerate: boolean
}
Response: 201 {
  artifact_id: number,
  embedding_id: string,
  dimensions: 1536,
  generated_at: timestamp,
  content_hash: string
}

// Get artifact embeddings
GET /api/v1/artifacts/{id}/embeddings/
Response: 200 {
  artifact_id: number,
  embeddings: Array<{
    id: string,
    content_type: string,
    dimensions: number,
    created_at: timestamp
  }>
}
```

### Similarity Search
```typescript
// Find similar artifacts
POST /api/v1/artifacts/search/similar/
Request: {
  query_text?: string,
  query_embedding?: number[],
  limit: number = 10,
  similarity_threshold: number = 0.7,
  artifact_types?: string[],
  user_only: boolean = true
}
Response: 200 {
  results: Array<{
    artifact_id: number,
    similarity_score: number,
    distance: number,
    artifact: {
      title: string,
      type: string,
      description: string
    }
  }>,
  query_info: {
    method: "cosine" | "l2" | "inner_product",
    total_candidates: number,
    processing_time_ms: number
  }
}

// Rank artifacts for job description
POST /api/v1/artifacts/rank/
Request: {
  job_description: string,
  artifact_ids?: number[],
  ranking_method: "semantic" | "hybrid" | "keyword",
  top_k: number = 5
}
Response: 200 {
  ranked_artifacts: Array<{
    artifact_id: number,
    relevance_score: number,
    semantic_similarity: number,
    keyword_match_score: number,
    explanation: string
  }>,
  job_embedding_generated: boolean,
  processing_metadata: object
}
```

## Database Schema Updates

```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding columns to artifacts table
ALTER TABLE artifacts ADD COLUMN content_embedding VECTOR(1536);
ALTER TABLE artifacts ADD COLUMN summary_embedding VECTOR(1536);
ALTER TABLE artifacts ADD COLUMN embedding_metadata JSONB DEFAULT '{}';

-- Create dedicated embedding storage table
CREATE TABLE artifact_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id INTEGER REFERENCES artifacts(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL, -- 'full', 'summary', 'chunk'
    embedding_vector VECTOR(1536) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    model_version VARCHAR(50) DEFAULT 'text-embedding-3-small',
    model_dimensions INTEGER DEFAULT 1536,
    processing_cost_usd DECIMAL(10,6) DEFAULT 0.0,
    generated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create chunk embeddings for large documents
CREATE TABLE chunk_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_chunk_id UUID REFERENCES artifact_chunks(id) ON DELETE CASCADE,
    embedding_vector VECTOR(1536) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Create job description embeddings cache
CREATE TABLE job_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    job_description_hash VARCHAR(64) UNIQUE NOT NULL,
    embedding_vector VECTOR(1536) NOT NULL,
    generated_at TIMESTAMP DEFAULT NOW(),
    access_count INTEGER DEFAULT 1
);

-- Create efficient indexes with latest pgvector strategies (2024)
-- HNSW indexes for better query performance (recommended for production)
CREATE INDEX artifact_embeddings_hnsw_idx ON artifact_embeddings
USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX chunk_embeddings_hnsw_idx ON chunk_embeddings
USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX job_embeddings_hnsw_idx ON job_embeddings
USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- IVFFlat indexes as fallback for memory-constrained environments
-- CREATE INDEX artifact_embeddings_ivfflat_idx ON artifact_embeddings
-- USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 1000);

-- DiskANN indexes for very large datasets (Azure PostgreSQL only)
-- CREATE INDEX artifact_embeddings_diskann_idx ON artifact_embeddings
-- USING diskann (embedding_vector vector_cosine_ops)
-- WITH (max_neighbors = 32, l_value_ib = 50);

-- Optimize query performance parameters
-- For HNSW indexes:
-- SET hnsw.ef_search = 100;  -- Higher values = better accuracy, slower queries
-- For IVFFlat indexes (if used):
-- SET ivfflat.probes = 10;   -- Number of lists to search

-- Composite indexes for filtered searches
CREATE INDEX artifact_embeddings_user_type_idx ON artifact_embeddings(artifact_id, content_type);
CREATE INDEX job_embeddings_user_hash_idx ON job_embeddings(user_id, job_description_hash);
```

## Implementation Plan

### Phase 1: pgvector Setup & Basic Integration (Week 1)
```python
# Django vector field implementation
from django.contrib.postgres.fields import ArrayField
from django.db import models
import numpy as np

class VectorField(ArrayField):
    def __init__(self, size, **kwargs):
        super().__init__(
            models.FloatField(),
            size=size,
            **kwargs
        )

class ArtifactEmbedding(models.Model):
    artifact = models.ForeignKey('Artifact', on_delete=models.CASCADE)
    content_type = models.CharField(max_length=50)
    embedding_vector = VectorField(size=1536)
    content_hash = models.CharField(max_length=64)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['artifact', 'content_type', 'content_hash']
```

### Phase 2: Embedding Generation Service (Week 2)
```python
# Embedding generation service
import openai
import hashlib
from typing import List, Dict

class EmbeddingService:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    async def generate_embedding(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item.embedding for item in response.data]

    def generate_content_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()
```

### Phase 3: Optimized Similarity Search Implementation (Week 3)
```python
# Advanced similarity search manager with latest pgvector optimizations
from django.db import connection, transaction
from typing import List, Dict, Optional, Tuple
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class OptimizedSimilaritySearchManager:

    @contextmanager
    def optimized_connection(self, search_type: str = "hnsw"):
        """Context manager for query-optimized database connections"""
        with connection.cursor() as cursor:
            # Set optimal search parameters based on index type
            if search_type == "hnsw":
                cursor.execute("SET LOCAL hnsw.ef_search = 100;")  # High accuracy
            elif search_type == "ivfflat":
                cursor.execute("SET LOCAL ivfflat.probes = 10;")  # Balance speed/accuracy
            elif search_type == "diskann":
                cursor.execute("SET LOCAL diskann.l_value_is = 100;")  # High accuracy

            yield cursor

    def find_similar_artifacts(
        self,
        query_embedding: List[float],
        user_id: int,
        limit: int = 10,
        threshold: float = 0.7,
        content_types: Optional[List[str]] = None,
        index_type: str = "hnsw"
    ) -> List[Dict]:
        """Find similar artifacts with optimized indexing strategy"""

        # Build dynamic WHERE clause for content type filtering
        where_conditions = ["a.user_id = %s"]
        params = [user_embedding, user_id]

        if content_types:
            where_conditions.append("ae.content_type = ANY(%s)")
            params.append(content_types)

        # Add similarity threshold
        where_conditions.append("ae.embedding_vector <=> %s::vector < %s")
        params.extend([query_embedding, 1 - threshold])

        where_clause = " AND ".join(where_conditions)
        params.append(query_embedding)  # For ORDER BY
        params.append(limit)

        with self.optimized_connection(index_type) as cursor:
            start_time = time.time()

            cursor.execute(f"""
                SELECT
                    a.id,
                    a.title,
                    a.artifact_type,
                    ae.embedding_vector <=> %s::vector as similarity_score,
                    ae.content_type,
                    ae.generated_at,
                    a.updated_at
                FROM artifacts a
                JOIN artifact_embeddings ae ON a.id = ae.artifact_id
                WHERE {where_clause}
                ORDER BY ae.embedding_vector <=> %s::vector
                LIMIT %s
            """, params)

            query_time = time.time() - start_time
            results = [dict(zip([col[0] for col in cursor.description], row))
                      for row in cursor.fetchall()]

            # Log performance metrics
            logger.info(f"Similarity search completed", extra={
                "query_time_ms": round(query_time * 1000, 2),
                "results_count": len(results),
                "index_type": index_type,
                "similarity_threshold": threshold
            })

            return results

    def rank_artifacts_for_job(
        self,
        job_embedding: List[float],
        artifact_ids: List[int],
        method: str = "cosine",
        include_explanation: bool = True
    ) -> List[Dict]:
        """Rank artifacts by relevance to job description with detailed scoring"""

        distance_operators = {
            "cosine": "<=>",      # Cosine distance (0 = identical, 2 = opposite)
            "l2": "<->",          # Euclidean distance
            "inner_product": "<#>" # Inner product (higher = more similar)
        }

        distance_op = distance_operators.get(method, "<=>")

        with self.optimized_connection("hnsw") as cursor:
            start_time = time.time()

            cursor.execute(f"""
                SELECT
                    a.id,
                    a.title,
                    a.artifact_type,
                    a.description,
                    ae.embedding_vector {distance_op} %s::vector as relevance_score,
                    ae.content_type,
                    ae.embedding_vector <=> %s::vector as cosine_distance,
                    ae.embedding_vector <-> %s::vector as l2_distance,
                    ae.embedding_vector <#> %s::vector as inner_product
                FROM artifacts a
                JOIN artifact_embeddings ae ON a.id = ae.artifact_id
                WHERE a.id = ANY(%s)
                ORDER BY ae.embedding_vector {distance_op} %s::vector
                {"ASC" if method == "inner_product" else "ASC"}
            """, [
                job_embedding,  # Primary ranking metric
                job_embedding,  # Cosine distance for comparison
                job_embedding,  # L2 distance for comparison
                job_embedding,  # Inner product for comparison
                artifact_ids,   # Filter to specified artifacts
                job_embedding   # ORDER BY ranking
            ])

            query_time = time.time() - start_time
            results = []

            for row in cursor.fetchall():
                result = dict(zip([col[0] for col in cursor.description], row))

                if include_explanation:
                    # Add relevance explanation based on similarity scores
                    cosine_similarity = 1 - result['cosine_distance']
                    result['similarity_explanation'] = self._generate_similarity_explanation(
                        cosine_similarity, result['artifact_type']
                    )

                results.append(result)

            logger.info(f"Artifact ranking completed", extra={
                "query_time_ms": round(query_time * 1000, 2),
                "artifacts_ranked": len(results),
                "ranking_method": method
            })

            return results

    def _generate_similarity_explanation(self, similarity_score: float, artifact_type: str) -> str:
        """Generate human-readable explanation of similarity score"""
        if similarity_score >= 0.9:
            return f"Highly relevant {artifact_type} with strong alignment to job requirements"
        elif similarity_score >= 0.8:
            return f"Very relevant {artifact_type} with good skill overlap"
        elif similarity_score >= 0.7:
            return f"Relevant {artifact_type} with some matching qualifications"
        elif similarity_score >= 0.6:
            return f"Moderately relevant {artifact_type} with partial alignment"
        else:
            return f"Limited relevance {artifact_type} with minimal skill overlap"

    def batch_similarity_search(
        self,
        queries: List[Tuple[List[float], int, Dict]],  # (embedding, user_id, options)
        batch_size: int = 10
    ) -> List[List[Dict]]:
        """Perform multiple similarity searches in optimized batches"""
        results = []

        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            batch_results = []

            with self.optimized_connection("hnsw") as cursor:
                for query_embedding, user_id, options in batch:
                    search_results = self.find_similar_artifacts(
                        query_embedding=query_embedding,
                        user_id=user_id,
                        **options
                    )
                    batch_results.append(search_results)

            results.extend(batch_results)

        return results
```

## Test & Eval Plan

### Unit Tests
- [ ] Vector field serialization/deserialization
- [ ] Embedding generation with mock OpenAI responses
- [ ] Similarity calculation accuracy with known vectors
- [ ] Database constraint validation for vector dimensions
- [ ] Content hash generation consistency

### Integration Tests
- [ ] End-to-end embedding generation and storage
- [ ] Similarity search with realistic dataset (1000+ artifacts)
- [ ] Concurrent embedding operations
- [ ] Index maintenance during bulk operations
- [ ] Cross-user similarity search isolation

### Performance Tests
- [ ] Similarity queries under 500ms with 10k vectors
- [ ] Index creation time with large datasets
- [ ] Memory usage during batch embedding generation
- [ ] Concurrent search performance (100 simultaneous queries)
- [ ] Storage growth monitoring and optimization

### Accuracy Tests
- [ ] Semantic similarity matches human judgment (>80% agreement)
- [ ] Job-artifact relevance ranking quality
- [ ] Comparison with keyword-based ranking
- [ ] Multi-language content similarity (if applicable)

## Rollout Strategy

### Phase 1: Infrastructure Setup (Week 4)
- Deploy pgvector extension to staging
- Create vector tables and indexes
- Test basic vector operations

### Phase 2: Embedding Generation Pipeline (Week 5)
- Generate embeddings for existing artifacts (background task)
- Monitor OpenAI API usage and costs
- Validate embedding quality with sample queries

### Phase 3: Similarity Search API (Week 6)
- Enable similarity search endpoints
- A/B test against keyword search
- Monitor query performance and accuracy

### Phase 4: CV Generation Integration (Week 7)
- Integrate similarity search into CV generation
- Compare output quality with existing system
- Gradual rollout to user base

## Advanced Performance Monitoring & Optimization (2024)

### Index Performance Optimization
```sql
-- Monitor index usage and performance
SELECT
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes
WHERE indexname LIKE '%vector%';

-- Check index progress for HNSW creation
SELECT
    phase,
    round(100.0 * blocks_done / nullif(blocks_total, 0), 1) AS "%"
FROM pg_stat_progress_create_index
WHERE command = 'CREATE INDEX';

-- Optimize HNSW parameters based on dataset size
-- For < 100K vectors:
-- CREATE INDEX ... WITH (m = 16, ef_construction = 64)
-- For 100K - 1M vectors:
-- CREATE INDEX ... WITH (m = 32, ef_construction = 128)
-- For > 1M vectors:
-- CREATE INDEX ... WITH (m = 48, ef_construction = 200)
```

### Dynamic Query Optimization
```python
# Adaptive query optimization based on dataset characteristics
class AdaptiveQueryOptimizer:
    def __init__(self):
        self.performance_cache = {}

    def optimize_search_parameters(self, vector_count: int, query_type: str) -> Dict:
        """Dynamically adjust search parameters based on data size and query type"""

        if vector_count < 10000:
            # Small dataset - prioritize accuracy
            return {
                "hnsw_ef_search": 200,
                "ivfflat_probes": 20,
                "diskann_l_value": 150
            }
        elif vector_count < 100000:
            # Medium dataset - balance accuracy/speed
            return {
                "hnsw_ef_search": 100,
                "ivfflat_probes": 10,
                "diskann_l_value": 100
            }
        else:
            # Large dataset - prioritize speed
            return {
                "hnsw_ef_search": 50,
                "ivfflat_probes": 5,
                "diskann_l_value": 75
            }

    def get_optimal_index_type(self, dataset_size: int, query_patterns: Dict) -> str:
        """Recommend optimal index type based on usage patterns"""

        # High write volume -> IVFFlat (faster builds)
        if query_patterns.get('writes_per_hour', 0) > 1000:
            return 'ivfflat'

        # Large dataset with high query volume -> DiskANN (if available)
        if dataset_size > 1000000 and query_patterns.get('queries_per_hour', 0) > 10000:
            return 'diskann'

        # Default to HNSW for best query performance
        return 'hnsw'
```

### Query Performance Metrics
- **Similarity Search Latency**: Target P95 < 500ms (HNSW), < 200ms (DiskANN)
- **Index Scan Efficiency**: >95% index usage for vector queries
- **Concurrent Query Throughput**: Support 100 simultaneous searches (HNSW), 500 (DiskANN)
- **Memory Usage**: Vector operations should not exceed 2GB RAM
- **Index Build Time**: <30 minutes for 100K vectors (HNSW), <60 minutes (IVFFlat)

### Storage & Cost Metrics
- **Embedding Storage Growth**: Monitor vector column size growth (~6KB per 1536-dim vector)
- **OpenAI API Costs**: Track embedding generation expenses (~$0.00013 per 1K tokens)
- **Index Size**: HNSW ~2x data size, IVFFlat ~1.5x, DiskANN ~1.2x
- **Cache Hit Rate**: Job embedding cache >80% hit rate
- **Index Maintenance**: Monitor fragmentation and rebuild schedules

### Quality Metrics
- **Search Relevance**: User interaction with search results >70%
- **CV Quality Improvement**: A/B test against keyword-only system
- **False Positive Rate**: <10% irrelevant results in top 10
- **Coverage**: >95% artifacts have valid embeddings
- **Embedding Quality**: Monitor cosine similarity distribution for new embeddings

## Edge Cases & Risks

### Technical Risks
- **Vector Index Corruption**: Index rebuilding may cause downtime
  - *Mitigation*: Hot standby indexes and rolling rebuilds
- **High-Dimensional Curse**: Similarity may degrade with sparse vectors
  - *Mitigation*: Dimensionality analysis and potential PCA reduction
- **OpenAI Rate Limiting**: Embedding generation may be throttled
  - *Mitigation*: Batch processing and exponential backoff

### Performance Risks
- **Index Size Growth**: Large indexes may slow query performance
  - *Mitigation*: Partitioning by user_id and archival of old embeddings
  - *Monitoring*: Alert when index size > 10GB or query latency > 1s p95
- **Memory Pressure**: Vector operations may consume excessive RAM
  - *Mitigation*: Connection pooling, query parameter tuning, and memory monitoring
  - *HNSW specific*: Reduce `ef_search` parameter during high load
- **Index Corruption**: Vector indexes more susceptible to corruption than B-tree
  - *Mitigation*: Regular REINDEX operations and hot standby indexes
  - *Detection*: Monitor query plan changes and unexpected seq scans
- **Write Performance Degradation**: High-volume inserts can slow HNSW indexes
  - *Mitigation*: Batch insertions, consider IVFFlat for write-heavy workloads
  - *Monitoring*: Track insert latency and index build times

### Business Risks
- **Embedding Model Changes**: OpenAI model updates may break compatibility
  - *Mitigation*: Model versioning and migration strategies
- **Cost Escalation**: High embedding generation costs at scale
  - *Mitigation*: Caching, deduplication, and usage limits

## Latest Model Configuration & Cost Analysis (2025)

### OpenAI Embedding Models Comparison
| Model | Cost per MTok | Dimensions | MTEB Score | Pages per Dollar | Use Case |
|-------|---------------|------------|------------|------------------|----------|
| text-embedding-3-small | $0.02 | 1536 | 62.3% | 62,500 | Cost-optimized, high volume |
| text-embedding-3-large | $0.13 | 3072 | 64.6% | 9,615 | Quality-optimized, critical apps |

### Flexible Configuration System
```python
# Environment-driven model selection
EMBEDDING_CONFIG = {
    "cost_optimized": {
        "model": "text-embedding-3-small",
        "dimensions": 1536,
        "cost_per_mtok": 0.02,
        "recommended_for": "high_volume_processing"
    },
    "quality_optimized": {
        "model": "text-embedding-3-large",
        "dimensions": 3072,
        "cost_per_mtok": 0.13,
        "recommended_for": "semantic_analysis"
    },
    "balanced": {
        "model": "text-embedding-3-small",
        "dimensions": 1536,
        "cost_per_mtok": 0.02,
        "recommended_for": "general_purpose"
    }
}

# Easy model switching
class ConfigurableEmbeddingService:
    def __init__(self):
        self.config = EMBEDDING_CONFIG[settings.EMBEDDING_STRATEGY]

    async def generate_embeddings(self, texts: List[str]) -> List[dict]:
        return await embedding(
            model=self.config["model"],
            input=texts,
            dimensions=self.config["dimensions"]
        )
```

### Cost Analysis for 10,000 Artifacts
```yaml
scenarios:
  cost_optimized:
    model: text-embedding-3-small
    total_cost: $2.00  # 10K artifacts × 100 tokens avg × $0.02/MTok
    storage_size: 60MB  # 10K × 1536 dims × 4 bytes

  quality_optimized:
    model: text-embedding-3-large
    total_cost: $13.00  # 10K artifacts × 100 tokens avg × $0.13/MTok
    storage_size: 120MB  # 10K × 3072 dims × 4 bytes

  hybrid_approach:
    strategy: Use large model for complex artifacts, small for simple
    estimated_cost: $4.50  # Weighted average
    quality_improvement: 15% better semantic search accuracy
```

## Dependencies

### External Services
- PostgreSQL 15+ with pgvector extension
- OpenAI API for text-embedding-3-small/large models (configurable)
- Flexible model switching via environment configuration
- Redis for caching frequently accessed embeddings

### Internal Dependencies
- Enhanced content extraction (ft-llm-001)
- Existing artifact storage infrastructure
- Celery for background embedding generation
- Authentication system for user isolation