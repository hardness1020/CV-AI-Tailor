# Feature — DB-001 SQLite to PostgreSQL Migration

**File:** docs/features/ft-db-001-postgresql-migration.md
**Owner:** System
**TECH-SPECs:** `spec-20240924-llm-artifacts.md`
**ADRs:** `adr-20240924-sqlite-to-postgresql-migration.md`, `adr-20240924-embedding-storage-strategy.md`

## Acceptance Criteria

### Development Environment
- [ ] PostgreSQL 15+ with pgvector extension running in Docker Compose
- [ ] Django connects to PostgreSQL instead of SQLite
- [ ] All existing models and data migrated successfully
- [ ] pgvector extension installed and functional
- [ ] Vector similarity queries working (cosine distance)

### Data Integrity
- [ ] All existing user accounts preserved
- [ ] All artifacts and evidence links migrated
- [ ] All generated documents and job descriptions preserved
- [ ] Foreign key relationships maintained
- [ ] No data loss during migration

### Performance & Functionality
- [ ] Application startup time <10s with PostgreSQL
- [ ] All existing API endpoints functional
- [ ] Admin interface works with PostgreSQL
- [ ] Test suite passes with 100% success rate
- [ ] Vector operations ready for future LLM features

## Design Changes

### Infrastructure Changes
```yaml
# docker-compose.yml - Add PostgreSQL service
services:
  db:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: cv_tailor
      POSTGRES_USER: cv_tailor_user
      POSTGRES_PASSWORD: dev_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
```

### Django Settings Updates
```python
# settings.py - Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'cv_tailor'),
        'USER': os.environ.get('DB_USER', 'cv_tailor_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'dev_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

### Migration Scripts
- `migrate_sqlite_to_postgresql.py` - Data migration management command
- `install_pgvector.sql` - pgvector extension installation
- `verify_migration.py` - Data integrity verification

## Test & Eval Plan

### Unit Tests
- Database connection and configuration
- Model field compatibility (JSON fields, etc.)
- pgvector extension functionality
- Vector similarity calculations

### Integration Tests
- Complete application workflow with PostgreSQL
- Data migration with sample SQLite database
- API endpoints with real database operations
- Admin interface CRUD operations

### Migration Testing
- **Test dataset**: Create sample SQLite database with realistic data
- **Migration verification**: Compare row counts, field values, relationships
- **Performance baseline**: Query response times before/after migration
- **Rollback testing**: Ensure rollback procedures work

### Success Thresholds
- Migration completes in <5 minutes for development dataset
- Zero data loss (100% row count preservation)
- API response times within 10% of SQLite performance
- All tests pass after migration

## Telemetry & Metrics

### Migration Monitoring
- Migration script execution time and progress
- Data integrity verification results
- Database connection pool metrics
- Query performance comparisons

### Production Monitoring
- PostgreSQL connection count and status
- Database response times (p95, p99)
- Vector index performance metrics
- Storage usage growth

### Alerts
- Database connection failures
- Migration script failures
- Query performance degradation >20%
- Vector index corruption or missing

## Rollout & Canary

### Development Rollout
1. **Week 1**: Docker Compose setup and local PostgreSQL
2. **Week 2**: Migration scripts and data verification
3. **Week 3**: CI/CD pipeline updates
4. **Week 4**: Production deployment preparation

### Feature Flags
- `feature.postgresql_enabled` - Toggle between SQLite/PostgreSQL
- `feature.pgvector_ready` - Enable vector-dependent features
- `feature.migration_mode` - Special mode during data migration

### Rollback Strategy
- Maintain SQLite configuration as fallback
- Export PostgreSQL data back to SQLite if needed
- Feature flags allow instant database switching
- Automated rollback scripts for production

## Edge Cases & Risks

### Data Migration Risks
- **Large datasets**: Migration time increases significantly with data size
- **Concurrent access**: Application downtime during migration
- **Data corruption**: Partial migration failure leaves inconsistent state
- **Foreign key violations**: Complex relationships may fail during migration

### Operational Risks
- **PostgreSQL unavailable**: Docker container or service failures
- **Performance degradation**: Slower queries than SQLite for simple operations
- **Storage requirements**: PostgreSQL requires more disk space
- **Backup complexity**: More complex backup/restore procedures

### Mitigation Strategies
- Implement migration checkpoints and resume capability
- Test migration with production-sized datasets
- Automated data integrity verification
- Comprehensive rollback procedures

## Implementation Tasks

### Phase 1: Infrastructure Setup
- [ ] Add PostgreSQL Docker service with pgvector
- [ ] Create database initialization scripts
- [ ] Update Django database settings
- [ ] Configure connection pooling

### Phase 2: Migration Tools
- [ ] Create SQLite export management command
- [ ] Create PostgreSQL import management command
- [ ] Implement data verification tools
- [ ] Create rollback procedures

### Phase 3: Testing & Validation
- [ ] Update test database configuration
- [ ] Create migration test suite
- [ ] Performance benchmark comparison
- [ ] Integration testing with vector operations

### Phase 4: Documentation & Deployment
- [ ] Update developer setup documentation
- [ ] Create production migration runbook
- [ ] CI/CD pipeline modifications
- [ ] Monitoring and alerting setup