# Feature Development Schedule

## Active Features

| ID | Title | Status | Owner | Priority | Target Date | Dependencies |
|----|-------|--------|-------|----------|-------------|--------------|
| ft-000 | User Authentication & Profile Management | **Done** | Backend Team | P0 | 2025-09-23 | None |
| ft-001 | Artifact Upload System | Draft | Backend Team | P0 | TBD | ft-000 |
| ft-002 | CV Generation System | Draft | ML/Backend Team | P0 | TBD | ft-001, LLM Integration |
| ft-003 | Document Export System | Draft | Backend Team | P0 | TBD | ft-002 |

## Feature Status Definitions

- **Draft**: Feature specification created, not yet approved for development
- **Approved**: Feature approved and ready for development
- **In Progress**: Active development underway
- **Testing**: Feature complete, undergoing QA testing
- **Done**: Feature completed and deployed to production
- **Blocked**: Development blocked by dependencies or issues
- **Cancelled**: Feature cancelled or deprioritized

## Priority Levels

- **P0**: Critical for MVP launch
- **P1**: Important for launch but can be delayed if necessary
- **P2**: Post-launch features for immediate roadmap
- **P3**: Future features for consideration

## Milestone Planning

### MVP Launch (Phase 1)
**Target**: TBD
**Critical Features**: ft-000 ✅, ft-001, ft-002, ft-003
**Requirements**:
- ✅ User authentication and profile management
- Complete artifact upload workflow
- Basic CV generation functionality
- PDF export capability

### Enhanced Features (Phase 2)
**Target**: TBD
**Features**: Cover letter generation, advanced templates, evidence integration

### Scale and Optimization (Phase 3)
**Target**: TBD
**Features**: Performance optimization, advanced AI features, enterprise features

## Notes

- All features must complete Stages A-D (PRD, SPEC, ADR, FEATURE) before development
- Feature dependencies must be resolved before starting development
- Target dates will be set after team capacity planning
- Priority levels may be adjusted based on user feedback and business requirements

## Change Log

- 2025-09-23: Added ft-000 (User Authentication) as completed foundation feature
- 2025-09-23: Updated dependencies - ft-001 now depends on ft-000 instead of "Auth System"
- 2025-09-23: Updated MVP requirements to include completed authentication system
- 2025-09-23: Initial feature schedule created with ft-001, ft-002, ft-003
- Features created following Stage D of workflow documentation