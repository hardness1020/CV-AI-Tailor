# Tech Specs Index

## Current Specifications

### System Architecture
- **Current**: [spec-20250923-system.md](spec-20250923-system.md) - v1.0.0 (Current)
  - Comprehensive system architecture for CV & Cover-Letter Auto-Tailor
  - Component topology with Django, React, Redis, PostgreSQL, and Celery
  - Infrastructure design supporting 10,000 concurrent users
  - Updated with authentication system implementation details

### API Design
- **Current**: [spec-20250923-api-v2.md](spec-20250923-api-v2.md) - v2.0.0 (Current)
  - REST API specification using Django DRF with comprehensive JWT authentication
  - Updated authentication contracts with user profiles and token blacklisting
  - Enhanced security, password management, and error handling
- **Superseded**: [spec-20250923-api.md](spec-20250923-api.md) - v1.0.0 (Superseded)
  - Initial API specification with basic authentication outline

### Frontend Application
- **Current**: [spec-20250923-frontend.md](spec-20250923-frontend.md) - v1.0.0 (Draft)
  - React SPA with TypeScript and Vite
  - State management, component architecture, and PWA features
  - Performance optimization and security patterns

### LLM Integration
- **Current**: [spec-20250923-llm.md](spec-20250923-llm.md) - v1.0.0 (Draft)
  - Large Language Model integration architecture
  - Prompt management, quality evaluation, and A/B testing
  - Multi-provider support with failover and circuit breakers

## Specification Status Legend
- **Draft**: Under development, not yet approved
- **Accepted**: Approved and ready for implementation
- **Current**: Active specification being used
- **Superseded**: Replaced by newer version

## Related Documentation
- **PRD**: [prd-20250923.md](../prds/prd-20250923.md) - Product requirements
- **Features**: [features/](../features/) - Feature specifications
- **ADRs**: [adrs/](../adrs/) - Architecture decision records
- **OP-NOTEs**: [op-notes/](../op-notes/) - Operational procedures

## Change Control
All specifications follow the versioning policy defined in [workflow rules](../../rules/00-workflow.md):
- Minor editorial fixes: update current file + changelog
- Material changes: create new dated snapshot
- Contract/topology/framework/SLO changes: new dated specification required