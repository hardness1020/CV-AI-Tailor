# ADR: Multi-Provider LLM Strategy for Artifact Processing

**File:** docs/adrs/adr-20240924-llm-provider-selection.md
**Status:** Draft

## Context

CV Tailor's enhanced artifact processing system requires reliable LLM services for content extraction, summarization, and semantic ranking. The system currently uses both OpenAI and Anthropic APIs with fallback logic, but this approach needs formalization for production reliability and cost optimization.

Key considerations:
- Processing volume: ~1000 artifacts/day at scale
- Content types: PDFs, GitHub repos, web profiles
- Latency requirements: <60s p95 for artifact enhancement
- Cost constraints: <$0.50 per artifact processing
- Reliability needs: 98% success rate for content processing

## Decision

Implement a **dual-provider strategy** with OpenAI as primary and Anthropic as fallback:

1. **OpenAI GPT-4** for content summarization and achievement extraction
2. **OpenAI text-embedding-3-small** for semantic similarity calculations
3. **Anthropic Claude-3-Haiku** as fallback for content processing during OpenAI outages
4. **Circuit breaker pattern** with 5-failure threshold triggering 30s fallback period

## Consequences

### Positive
+ **Reliability**: 99.5%+ uptime through provider redundancy
+ **Cost efficiency**: OpenAI embeddings significantly cheaper than alternatives
+ **Performance**: GPT-4 superior quality for structured content extraction
+ **Existing integration**: Builds on current dual-provider infrastructure

### Negative
− **Complexity**: Multiple API key management and provider-specific logic
− **Consistency**: Potential output variations between providers during fallbacks
− **Cost risk**: Higher token usage if both providers used simultaneously
− **Vendor lock-in**: Heavy reliance on two specific providers

## Alternatives

1. **OpenAI-only**: Simpler but single point of failure
2. **Anthropic-only**: Good quality but higher embedding costs
3. **Open-source models**: Lower cost but significant infrastructure complexity
4. **Azure OpenAI**: Enterprise reliability but higher latency

## Rollback Plan

- **Immediate**: Feature flags allow instant fallback to keyword matching
- **Provider switch**: Configuration-driven provider priority changes
- **Full rollback**: Cached summaries preserve functionality during transitions
- **Data preservation**: All enhanced content stored independently of provider choice

## Links

- **TECH-SPEC**: `spec-20240924-llm-artifacts.md`
- **Feature**: `ft-llm-001-content-extraction.md` (pending)