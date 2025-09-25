# Feature — LLM-001 Enhanced Content Extraction with LangChain

**Feature ID:** ft-llm-001
**Title:** LangChain Multi-Format Document Processing Framework
**Status:** Pending - Documentation Complete
**Priority:** P1 (Core Enhancement)
**Owner:** Backend Team
**Target Date:** 2024-09-30
**Sprint:** LLM Enhancement Sprint 1

## Overview

Implement LangChain-based document processing framework to support diverse artifact types (PDF documents, GitHub repositories, web profiles) with unified processing pipeline, advanced chunking strategies, and seamless integration with existing Django/Celery architecture.

## Links
- **ADR**: [adr-20240924-document-processing-framework.md](../adrs/adr-20240924-document-processing-framework.md)
- **SPEC**: [spec-20240924-llm-artifacts.md](../specs/spec-20240924-llm-artifacts.md)

## Implementation Status

### Backend ❌ Pending
- ❌ LangChain integration and dependency setup
- ❌ UnstructuredPDFLoader implementation
- ❌ GitHub repository analysis with LangChain loaders
- ❌ UnstructuredHTMLLoader for web profile processing
- ❌ Custom content extractors in LangChain format
- ❌ CharacterTextSplitter integration for chunking
- ❌ Migration from existing PyPDF2 implementation

### Integration ❌ Pending
- ❌ Celery task updates to use LangChain processors
- ❌ Document object serialization to JSON
- ❌ Database schema updates for enhanced metadata
- ❌ API endpoint updates for new document formats

### Testing ❌ Missing
- ❌ Unit tests for each document loader
- ❌ Integration tests with existing Celery tasks
- ❌ Performance benchmarks vs. current implementation

## Acceptance Criteria

### Core Document Processing
- [ ] UnstructuredPDFLoader successfully extracts content from PDF files
- [ ] GitHubIssuesLoader and GithubFileLoader analyze repository structure
- [ ] UnstructuredHTMLLoader processes web profiles (LinkedIn, portfolio sites)
- [ ] Custom extractors wrapped in LangChain Document format
- [ ] CharacterTextSplitter chunks large documents for LLM context windows
- [ ] All loaders return consistent Document objects with metadata

### Content Quality & Metadata
- [ ] Extract structured content (headings, tables, code blocks) from documents
- [ ] Preserve formatting context for technical documents
- [ ] GitHub analysis includes README content, code structure, and project descriptions
- [ ] Web profile extraction captures professional summary and experience sections
- [ ] Metadata includes source type, extraction confidence, and processing timestamps

### Integration & Performance
- [ ] LangChain processors integrate seamlessly with existing Celery tasks
- [ ] Document objects serialize to JSON for database storage
- [ ] Processing time remains under 60s p95 for typical artifacts
- [ ] Gradual migration path preserves existing functionality
- [ ] Fallback to PyPDF2 when LangChain processing fails

### Chunking & Optimization
- [ ] CharacterTextSplitter optimizes chunk size for LLM context windows
- [ ] Overlapping chunks preserve context continuity
- [ ] Chunk metadata includes source location and relevance scoring
- [ ] Large documents (>10,000 words) processed efficiently
- [ ] Memory usage remains stable during processing

## API Changes

### Enhanced Artifact Processing Endpoint
```typescript
POST /api/v1/artifacts/{id}/enhance/
Request: {
  processing_options: {
    extract_structure: boolean,
    enable_chunking: boolean,
    chunk_size: number,
    chunk_overlap: number,
    include_metadata: boolean
  }
}

Response: 200 {
  artifact_id: number,
  status: "processing",
  task_id: string,
  enhanced_content: {
    total_chunks: number,
    content_types: string[],
    metadata_extracted: object,
    processing_method: "langchain" | "legacy"
  }
}
```

### Document Analysis Results
```typescript
GET /api/v1/artifacts/{id}/analysis/
Response: 200 {
  artifact_id: number,
  analysis_results: {
    document_type: "pdf" | "github" | "web_profile",
    content_structure: {
      sections: Array<{title: string, content: string, chunk_ids: string[]}>,
      metadata: object,
      confidence_score: number
    },
    chunks: Array<{
      id: string,
      content: string,
      metadata: object,
      relevance_score?: number
    }>,
    processing_metadata: {
      loader_type: string,
      processing_time_ms: number,
      fallback_used: boolean
    }
  }
}
```

## Database Schema Updates

```sql
-- Enhanced artifact content storage
ALTER TABLE artifacts ADD COLUMN enhanced_content JSONB DEFAULT '{}';
ALTER TABLE artifacts ADD COLUMN content_chunks JSONB DEFAULT '[]';
ALTER TABLE artifacts ADD COLUMN processing_metadata JSONB DEFAULT '{}';

-- Document chunk storage
CREATE TABLE artifact_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id INTEGER REFERENCES artifacts(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding_vector VECTOR(1536), -- For future pgvector integration
    created_at TIMESTAMP DEFAULT NOW()
);

-- Processing job updates
ALTER TABLE artifact_processing_jobs ADD COLUMN langchain_metadata JSONB DEFAULT '{}';
ALTER TABLE artifact_processing_jobs ADD COLUMN fallback_used BOOLEAN DEFAULT FALSE;
```

## Implementation Plan

### Phase 1: Core LangChain Integration (Week 1)
```python
# Install dependencies
pip install langchain langchain-community unstructured

# Basic loader implementation
from langchain_community.document_loaders import (
    UnstructuredPDFLoader,
    GitHubIssuesLoader,
    GithubFileLoader,
    UnstructuredHTMLLoader
)
from langchain.text_splitter import CharacterTextSplitter
```

### Phase 2: Advanced Text Splitting Strategies (Week 2)
```python
# Latest LangChain text splitting approaches
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    SemanticChunker,
    HTMLHeaderTextSplitter,
    MarkdownHeaderTextSplitter
)

class AdvancedTextSplitter:
    def __init__(self, embeddings_model):
        # Semantic-based splitting (latest 2024 approach)
        self.semantic_splitter = SemanticChunker(
            embeddings=embeddings_model,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=80
        )

        # Structure-aware splitting
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

        # Document-specific splitters
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
        )

    def adaptive_split(self, documents: List[Document]) -> List[Document]:
        """Choose optimal splitting strategy based on document type and content"""
        result_chunks = []

        for doc in documents:
            # Use semantic splitting for long technical documents
            if len(doc.page_content) > 5000 and "technical" in doc.metadata.get("type", ""):
                chunks = self.semantic_splitter.split_documents([doc])
            # Use structure-based splitting for markdown
            elif doc.metadata.get("source_type") == "markdown":
                chunks = self.markdown_splitter.split_documents([doc])
            # Default recursive splitting
            else:
                chunks = self.recursive_splitter.split_documents([doc])

            result_chunks.extend(chunks)

        return result_chunks
```

### Phase 3: Custom GitHub Repository Processor (Week 2)
```python
# Enhanced GitHub repository analyzer with latest patterns
class GitHubRepositoryProcessor:
    def __init__(self, repo_url: str, github_token: str):
        self.repo_url = repo_url
        self.github_token = github_token
        self.text_splitter = AdvancedTextSplitter(embeddings_model)

    def process(self) -> List[Document]:
        documents = []

        # README processing with structure awareness
        readme_loader = GithubFileLoader(
            repo=self.repo_url,
            access_token=self.github_token,
            file_path="README.md"
        )
        readme_docs = readme_loader.load()

        # Code structure analysis
        code_loader = GithubFileLoader(
            repo=self.repo_url,
            access_token=self.github_token,
            file_filter=lambda path: path.endswith((".py", ".js", ".ts", ".java"))
        )
        code_docs = code_loader.load()

        # Apply adaptive splitting
        all_docs = readme_docs + code_docs
        return self.text_splitter.adaptive_split(all_docs)
```

### Phase 4: Multi-Provider LLM Integration (Week 3)
```python
# Multi-provider LLM with circuit breaker (2024 best practices)
from litellm import completion, embedding
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class MultiProviderLLMService:
    def __init__(self):
        self.providers = {
            "primary": {
                "model": "gpt-4",
                "api_key": settings.OPENAI_API_KEY,
                "embedding_model": "text-embedding-3-small"
            },
            "fallback": {
                "model": "claude-3-haiku-20240307",
                "api_key": settings.ANTHROPIC_API_KEY
            }
        }
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def extract_structured_content(self, content: str, content_type: str) -> dict:
        """Extract achievements, skills, and metadata using LLM"""
        prompt = self._build_extraction_prompt(content_type)

        try:
            if self.circuit_breaker_failures < self.circuit_breaker_threshold:
                response = await completion(
                    model="gpt-4",
                    messages=[{
                        "role": "system",
                        "content": prompt
                    }, {
                        "role": "user",
                        "content": content
                    }],
                    api_key=self.providers["primary"]["api_key"],
                    response_format={"type": "json_object"}
                )
                provider_used = "openai"
            else:
                # Fallback to Anthropic
                response = await completion(
                    model="claude-3-haiku-20240307",
                    messages=[{
                        "role": "user",
                        "content": f"{prompt}\n\n{content}"
                    }],
                    api_key=self.providers["fallback"]["api_key"]
                )
                provider_used = "anthropic"

            self.circuit_breaker_failures = 0  # Reset on success

            return {
                "extracted_content": json.loads(response.choices[0].message.content),
                "provider_used": provider_used,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }

        except Exception as e:
            self.circuit_breaker_failures += 1
            logger.error(f"LLM processing failed: {e}", exc_info=True)
            raise

    def _build_extraction_prompt(self, content_type: str) -> str:
        base_prompt = """
Extract structured information from the following professional content.
Return valid JSON with these fields:
- "achievements": Array of specific accomplishments with quantified results
- "skills": Object with "technical" and "soft" skill arrays
- "experience_context": Object with "role", "company", "duration", "responsibilities"
- "impact_metrics": Array of measurable outcomes and results
- "relevance_keywords": Array of industry/role-relevant terms
"""

        type_specific = {
            "pdf": "Focus on extracting professional experience, education, and quantified achievements.",
            "github": "Focus on technical projects, programming languages, and development achievements.",
            "web_profile": "Focus on professional summary, career progression, and public achievements."
        }

        return f"{base_prompt}\n\n{type_specific.get(content_type, '')}"

# Enhanced Celery task with multi-provider LLM
@shared_task(bind=True, max_retries=3)
def process_artifact_with_langchain(self, artifact_id: int):
    artifact = Artifact.objects.get(id=artifact_id)
    llm_service = MultiProviderLLMService()

    try:
        # Step 1: Load and chunk documents
        loader = get_langchain_loader(artifact)
        documents = loader.load()

        # Step 2: Advanced text splitting
        splitter = AdvancedTextSplitter(embeddings_model)
        chunks = splitter.adaptive_split(documents)

        # Step 3: LLM-powered content extraction
        enhanced_chunks = []
        for chunk in chunks:
            extraction_result = await llm_service.extract_structured_content(
                chunk.page_content,
                artifact.content_type
            )

            enhanced_chunks.append({
                "content": chunk.page_content,
                "metadata": chunk.metadata,
                "extracted_data": extraction_result["extracted_content"],
                "processing_metadata": {
                    "provider_used": extraction_result["provider_used"],
                    "tokens_used": extraction_result["tokens_used"],
                    "processed_at": timezone.now().isoformat()
                }
            })

        # Step 4: Store enhanced content
        artifact.enhanced_content = {
            "chunks": enhanced_chunks,
            "total_chunks": len(enhanced_chunks),
            "processing_method": "langchain_advanced",
            "llm_providers_used": list(set(c["processing_metadata"]["provider_used"] for c in enhanced_chunks))
        }
        artifact.processing_metadata = {
            "langchain_version": "0.1.0",
            "splitting_strategy": "adaptive",
            "total_tokens_used": sum(c["processing_metadata"]["tokens_used"] for c in enhanced_chunks),
            "processing_duration_seconds": (timezone.now() - artifact.updated_at).total_seconds()
        }
        artifact.save()

        return f"Enhanced artifact {artifact_id} with {len(enhanced_chunks)} chunks"

    except Exception as e:
        logger.error(f"LangChain processing failed for artifact {artifact_id}: {e}")
        # Fallback to legacy processing
        return process_artifact_legacy(artifact_id)
```

## Test & Eval Plan

### Unit Tests
- [ ] Each LangChain loader processes sample files correctly
- [ ] Document serialization/deserialization maintains data integrity
- [ ] Text splitter creates appropriate chunk sizes
- [ ] Error handling gracefully falls back to legacy processing
- [ ] GitHub API integration handles rate limiting

### Integration Tests
- [ ] End-to-end artifact processing with LangChain
- [ ] Celery task integration maintains existing API contracts
- [ ] Database operations handle enhanced metadata correctly
- [ ] Performance benchmarks show acceptable processing times
- [ ] Gradual migration preserves data consistency

### Performance Tests
- [ ] PDF processing completes within 30s for 50-page documents
- [ ] GitHub repository analysis finishes within 45s
- [ ] Memory usage remains under 500MB during processing
- [ ] Concurrent processing handles 10 artifacts simultaneously
- [ ] Chunk generation scales linearly with document size

## Rollout Strategy

### Phase 1: Parallel Processing (Week 4)
- Run both LangChain and legacy processing
- Compare outputs and quality metrics
- Feature flag controls which processor is used

### Phase 2: Gradual Migration (Week 5-6)
- 10% of artifacts use LangChain processing
- Monitor error rates and performance metrics
- Expand to 50% if quality metrics improve

### Phase 3: Full Migration (Week 7-8)
- 100% LangChain processing with legacy fallback
- Remove legacy code after stability confirmation
- Documentation and training for team

## Edge Cases & Risks

### Technical Risks
- **Large Document Memory Usage**: LangChain may consume excessive memory for large PDFs
  - *Mitigation*: Implement streaming processing and memory monitoring
- **GitHub Rate Limiting**: Repository analysis may exceed API limits
  - *Mitigation*: Implement exponential backoff and request queuing
- **Extraction Quality**: LangChain may miss domain-specific content
  - *Mitigation*: Custom extractors for technical documents

### Migration Risks
- **Data Loss**: Migration may lose existing processed content
  - *Mitigation*: Parallel processing during transition period
- **API Breaking Changes**: Enhanced endpoints may break frontend integration
  - *Mitigation*: Versioned APIs and backward compatibility

## Dependencies

### External Libraries
- LangChain framework and community extensions
- Unstructured.io for document processing
- GitHub API for repository analysis
- Enhanced PDF processing libraries

### Internal Dependencies
- Existing Celery task infrastructure
- Artifact storage and database schema
- Authentication system for API access
- Frontend updates for enhanced features