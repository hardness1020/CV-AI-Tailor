# Tech Spec — System

**Version:** v1.0.0
**File:** docs/specs/spec-20250923-system.md
**Status:** Draft
**PRD:** `prd-20250923.md`
**Contract Versions:** API v1.0 • Schema v1.0 • Prompt Set v1.0

## Overview & Goals

Build a comprehensive CV & Cover-Letter Auto-Tailor system that enables job seekers to upload work artifacts with evidence links and generate targeted, ATS-optimized career documents. Target CV generation ≤30s, ATS pass rate ≥65%, and support for 10,000 concurrent users with 1M+ stored artifacts.

Links to latest PRD: `docs/prds/prd-20250923.md`

## Architecture (Detailed)

### Topology (frameworks)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Public Internet                                │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │ HTTPS
┌─────────────────────▼───────────────────────────────────────────────────┐
│                    CDN/Ingress (Nginx)                                  │
│                   [Public Trust Boundary]                               │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │ HTTP
┌─────────────────────▼───────────────────────────────────────────────────┐
│                  React SPA Frontend                                     │
│                     (Vite, TypeScript)                                  │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │ HTTP REST API
┌─────────────────────▼───────────────────────────────────────────────────┐
│                Application Gateway (Django)                             │
│                   [Private Trust Boundary]                              │
│  ┌─────────────────┬─────────────────┬─────────────────┐                │
│  │   Auth Service  │  Core API       │  Export Service │                │
│  │   (Django)      │  (Django DRF)   │  (Django)       │                │
│  └─────────────────┼─────────────────┼─────────────────┘                │
└──────────────────┬─┼─────────────────┼─────────────────┬─────────────────┘
                   │ │                 │                 │
       ┌───────────▼─▼─────────────────▼─────────────────▼───────────┐
       │                    Redis Cluster                            │
       │          (Cache + Session + Queue Broker)                   │
       └─────────────────────┬───────────────────────────────────────┘
                             │ Queue Jobs
       ┌─────────────────────▼───────────────────────────────────────┐
       │               Celery Workers                                │
       │  ┌──────────────┬──────────────┬────────────────────────┐   │
       │  │ Artifact     │ Matching     │ Generation             │   │
       │  │ Processor    │ Engine       │ Service                │   │
       │  │ (Python)     │ (Python)     │ (Python)               │   │
       │  └──────────────┼──────────────┼────────────────────────┘   │
       └─────────────────┼──────────────┼────────────────────────────┘
                         │              │
                         │              │ LLM API Calls
                         │              └──────────────┐
                         │                             │
┌────────────────────────▼─────────────────────────────▼───────────────────┐
│                     PostgreSQL Database                                  │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────────────┐  │
│  │ Users       │ Artifacts   │ Evidence    │ Generated Documents     │  │
│  │ & Auth      │ & Labels    │ Links       │ & Versions              │  │
│  └─────────────┴─────────────┴─────────────┴─────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                         External LLM Provider                             │
│                        (OpenAI/Anthropic API)                            │
│                       [External Trust Boundary]                          │
└───────────────────────────────────────────────────────────────────────────┘
```

### Component Inventory

| Component | Framework/Runtime | Purpose | Interfaces (in/out) | Depends On | Scale/HA | Owner |
|-----------|------------------|---------|-------------------|------------|----------|-------|
| CDN/Ingress | Nginx | Static assets, SSL termination, load balancing | In: HTTPS from users; Out: HTTP to frontend | - | Multi-region, auto-failover | DevOps |
| Frontend | React (Vite, TypeScript) | SPA for artifact upload, CV generation, export | In: HTTP from CDN; Out: REST API calls to backend | CDN, API Gateway | Edge cached, multi-region | Frontend |
| API Gateway | Django + Gunicorn + uv | Request routing, auth, rate limiting | In: HTTP REST from frontend; Out: DB, Redis, Celery | Redis, PostgreSQL | 5+ replicas, HPA | Backend |
| Auth Service | Django (built-in auth) | User authentication, session management | In: Login/logout requests; Out: Session to Redis | Redis, PostgreSQL | Stateless, scales with API | Backend |
| Core API | Django DRF | Artifact CRUD, matching, generation orchestration | In: REST API calls; Out: DB queries, Celery tasks | PostgreSQL, Redis, Celery | Stateless, auto-scale | Backend |
| Export Service | Django + ReportLab/python-docx | PDF/Docx generation and formatting | In: Document data; Out: Binary files | PostgreSQL, Redis | CPU-intensive, separate scaling | Backend |
| Dependency Manager | uv | Python package and environment management | In: pyproject.toml; Out: Isolated Python environments | Python runtime | Development/deployment tool | Backend |
| Redis Cluster | Redis 7 | Session cache, API cache, Celery broker | In: Cache ops, queue ops; Out: Data retrieval | - | Primary+replica per region | DevOps |
| Celery Workers | Celery (Python + uv) | Async processing of artifacts and generation | In: Queue messages; Out: DB updates, LLM calls | Redis, PostgreSQL, LLM API | Auto-scale by queue depth | Backend |
| Artifact Processor | Python (Celery worker + uv) | Parse uploads, extract metadata, validate evidence | In: Upload tasks; Out: Structured artifact data | PostgreSQL, External APIs | Scales independently | Backend |
| Matching Engine | Python (Celery worker + uv) | Job description parsing, skill matching, ranking | In: JD + artifacts; Out: Relevance scores | PostgreSQL, LLM API | CPU/memory intensive scaling | Backend |
| Generation Service | Python (Celery worker + uv) | CV/cover letter content generation | In: Matched artifacts + template; Out: Generated content | LLM API, PostgreSQL | Rate-limited by LLM API | Backend |
| PostgreSQL | PostgreSQL 15 | Primary data storage for all entities | In: SQL queries; Out: Query results | - | Primary + read replicas + PITR | DevOps |
| LLM Provider | External HTTP API | Content generation, parsing, matching | In: HTTPS requests; Out: Generated text/analysis | - | External SLA dependency | Backend |

## Interfaces & Data Contracts

### Core API Endpoints
- `POST /api/v1/artifacts` - Upload and process work artifacts
- `GET /api/v1/artifacts` - List user's artifacts with filtering
- `POST /api/v1/labels` - Create reusable role labels
- `POST /api/v1/generate/cv` - Generate targeted CV
- `POST /api/v1/generate/cover-letter` - Generate cover letter
- `GET /api/v1/documents/{id}` - Retrieve generated documents
- `POST /api/v1/export/{id}` - Export to PDF/Docx format

### Data Schema Versions
- **API Schema v1.0:** RESTful endpoints with consistent error responses
- **Database Schema v1.0:** Normalized tables for artifacts, evidence, labels, generations
- **LLM Prompt Schema v1.0:** Structured prompts for parsing, matching, generation

### Error Taxonomy
- 400: Invalid request data (malformed JSON, missing required fields)
- 401: Authentication required
- 403: Insufficient permissions
- 404: Resource not found
- 422: Business logic validation failure (invalid file type, broken evidence link)
- 429: Rate limit exceeded
- 500: Internal server error
- 502: External service (LLM) unavailable
- 503: Service temporarily unavailable (maintenance)

## Data & Storage

### Primary Tables
- `users` - User accounts and preferences
- `artifacts` - Work projects with metadata (title, dates, stack, collaborators)
- `evidence_links` - URLs proving artifacts with validation status
- `labels` - Reusable role-theme tags grouping artifacts and skills
- `skills` - Normalized skill taxonomy (technologies, frameworks, domains)
- `job_descriptions` - Parsed JD data with requirements and company signals
- `generated_documents` - CV/cover letter versions with metadata
- `export_logs` - Track which evidence links were included in exports

### Indexes and Performance
- `artifacts.user_id, created_at` - User artifact listing
- `evidence_links.artifact_id, validation_status` - Evidence retrieval
- `generated_documents.user_id, job_description_hash` - Document versioning
- `skills.name` - Skill matching and normalization

### Migrations and Retention
- Initial schema migration: `001_create_base_tables.sql`
- Evidence link validation: 30-day rolling validation
- Generated documents: 90-day retention unless user-saved
- Export logs: 2-year retention for analytics

## Reliability & SLIs/SLOs

### Service Level Indicators
- **Availability:** Uptime percentage (excluding planned maintenance)
- **Latency:** P95 response time for CV generation
- **Error Rate:** 5xx error percentage
- **Evidence Link Health:** Percentage of working evidence links

### Service Level Objectives
- **Availability:** ≥99.5% during business hours (6 AM - 10 PM user timezone)
- **CV Generation Latency:** P95 ≤30 seconds end-to-end
- **Cover Letter Generation:** P95 ≤15 seconds
- **Error Rate:** ≤1% for user-facing endpoints
- **Evidence Link Validation:** ≥95% working links maintained

### Reliability Mechanisms
- **Circuit Breaker:** LLM API calls with 5% error threshold
- **Retry Logic:** Exponential backoff for transient failures (3 retries max)
- **Rate Limiting:** 100 requests/hour per user, 10 generations/hour
- **Graceful Degradation:** Template-based generation if LLM unavailable
- **Health Checks:** Deep health checks for all dependencies

## Security & Privacy

### Authentication & Authorization
- **Authentication:** JWT tokens with 24-hour expiry
- **Authorization:** Role-based access (user, admin)
- **Session Management:** Redis-backed sessions with secure cookies
- **API Security:** CORS, CSRF protection, input validation

### Data Protection
- **PII Handling:** No PII stored beyond email for account
- **Evidence Links:** Encrypted at rest, validated before display
- **Secrets Management:** Environment variables, no hardcoded credentials
- **Data Isolation:** User data strictly partitioned by user_id

### Audit and Logging
- **Structured Logging:** JSON format with correlation IDs
- **Audit Trail:** All document generations and exports logged
- **Security Events:** Failed logins, suspicious patterns
- **Log Retention:** 30 days detailed, 2 years aggregated

## Evaluation Plan

### Test Datasets
- **Golden CV Examples:** 100 high-quality CVs across different roles
- **Job Description Corpus:** 500 JDs from various companies and roles
- **Evidence Link Test Set:** 1000 validated links of different types
- **ATS Compatibility Suite:** Test exports against 10 major ATS systems

### Quality Metrics
- **Content Relevance:** User ratings ≥8/10 for generated content
- **Evidence Accuracy:** ≥95% evidence links remain valid
- **ATS Pass Rate:** ≥65% compatibility across test ATS systems
- **Keyword Matching:** ≥85% of critical JD keywords included appropriately

### Test Harness
- **Automated Regression:** Daily runs against golden dataset
- **Performance Testing:** Load testing for 10,000 concurrent users
- **Integration Testing:** End-to-end user journey validation
- **Security Testing:** Regular penetration testing and vulnerability scans

## Rollout & Ops Impact

### Feature Flags
- `feature.artifact_upload.enabled` - Control artifact upload functionality
- `feature.cv_generation.enabled` - Toggle CV generation
- `feature.cover_letter.enabled` - Enable cover letter feature
- `feature.export.pdf_enabled` - Control PDF export
- `feature.export.docx_enabled` - Control Docx export

### Rollout Strategy
- **Phase 1 (Beta):** 100 invited users, limited features
- **Phase 2 (Gradual):** 10% traffic, full feature set
- **Phase 3 (Full):** 100% traffic with monitoring

### Monitoring Dashboards
- **User Metrics:** Registrations, uploads, generations, exports
- **Performance:** Response times, queue depths, resource utilization
- **Quality:** User ratings, error rates, evidence link health
- **Business:** Conversion rates, retention, feature adoption

### Alerting
- **Critical:** Service down, database unreachable, LLM API failures
- **Warning:** High latency, elevated error rates, queue backing up
- **Info:** Daily metrics summaries, weekly quality reports

## Risks & Rollback

### Technical Risks
1. **LLM API Rate Limits/Costs** → Mitigation: Caching, request optimization, backup providers
2. **Evidence Link Degradation** → Mitigation: Regular validation, archive.org fallbacks
3. **Database Performance** → Mitigation: Read replicas, query optimization, caching
4. **User Data Privacy** → Mitigation: Encryption, access controls, audit logging

### Business Risks
1. **Poor Content Quality** → Mitigation: Human review loops, user feedback integration
2. **ATS Compatibility Issues** → Mitigation: Regular ATS testing, format variations
3. **User Adoption** → Mitigation: Onboarding optimization, user research
4. **Competitive Pressure** → Mitigation: Unique evidence-linking differentiator

### Rollback Plan
- **Feature Flags:** Immediate disable of problematic features
- **Database Rollback:** Point-in-time recovery for data issues
- **Code Rollback:** Blue-green deployment for rapid version reversion
- **Data Migration Rollback:** Reversible migrations with validation

## Open Questions

1. **LLM Provider Selection:** OpenAI vs Anthropic vs hybrid approach for different use cases
2. **Evidence Validation Frequency:** Real-time vs batch validation trade-offs
3. **User Data Export:** Scope and format for GDPR compliance
4. **Integration Strategy:** Priority order for job board and LinkedIn integrations
5. **Monetization Impact:** How pricing tiers affect technical architecture

## Changelog

- 2025-09-23: Draft created; system architecture defined; component inventory completed; SLOs established; uv dependency management integration added