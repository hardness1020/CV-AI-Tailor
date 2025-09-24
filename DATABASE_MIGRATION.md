# Database Migration: SQLite to PostgreSQL

This document provides step-by-step instructions for migrating CV Tailor from SQLite to PostgreSQL with pgvector support for enhanced LLM artifact processing.

## Overview

The migration enables:
- PostgreSQL database for production scalability
- pgvector extension for vector similarity search
- Enhanced LLM artifact processing capabilities
- Semantic similarity matching for CV generation

## Prerequisites

### System Requirements
- Docker and Docker Compose
- Python 3.11+
- Git

### Current Setup Verification
```bash
# Verify current database
cd backend
python manage.py dbshell
# Should show SQLite prompt: sqlite>
.exit
```

## Migration Process

### Step 1: Environment Setup

1. **Copy environment configuration:**
```bash
cd backend
cp .env.example .env
```

2. **Configure environment variables in `.env`:**
```env
DB_ENGINE=postgresql
DB_NAME=cv_tailor
DB_USER=cv_tailor_user
DB_PASSWORD=cv_tailor_dev_password
DB_HOST=localhost
DB_PORT=5432
```

### Step 2: Start PostgreSQL with Docker

1. **Start PostgreSQL service:**
```bash
# From project root
docker-compose up -d db redis
```

2. **Verify PostgreSQL is running:**
```bash
docker-compose logs db
# Should show: "database system is ready to accept connections"
```

3. **Test connection:**
```bash
docker exec -it cv_tailor_db psql -U cv_tailor_user -d cv_tailor
# Should connect to PostgreSQL prompt
\q
```

### Step 3: Setup pgvector Extension

1. **Install and verify pgvector:**
```bash
cd backend
python manage.py setup_pgvector --test-vectors
```

Expected output:
```
Setting up pgvector extension...
✓ pgvector extension installed
✓ pgvector extension verified: vector v0.5.1
✓ Vector operations working correctly
✓ Vector operations test completed successfully
pgvector setup completed successfully!
```

### Step 4: Migrate Database Schema

1. **Create PostgreSQL schema:**
```bash
python manage.py migrate
```

This will create all tables in PostgreSQL.

### Step 5: Migrate Data from SQLite

1. **Dry run (verify migration plan):**
```bash
python manage.py migrate_to_postgresql --dry-run
```

2. **Perform actual migration:**
```bash
python manage.py migrate_to_postgresql
```

Expected output:
```
Starting migration from SQLite to PostgreSQL
SQLite database: /workspace/backend/db.sqlite3
PostgreSQL database: cv_tailor
Found X tables to migrate:
  - accounts_user (User)
  - artifacts_artifact (Artifact)
  - ... (other tables)
✓ Migrated XX records from accounts_user
✓ Migrated XX records from artifacts_artifact
...
Migration completed successfully! Total records migrated: XXX
Verifying migration...
✓ accounts_user: XX records (matches SQLite)
✓ artifacts_artifact: XX records (matches SQLite)
...
Migration verification passed!
```

### Step 6: Update Application Configuration

1. **Test application with PostgreSQL:**
```bash
python manage.py runserver
```

2. **Verify admin interface:**
- Visit: http://localhost:8000/admin/
- Login with existing admin credentials
- Verify all data is present

3. **Run test suite:**
```bash
python manage.py test
```

### Step 7: Start Complete Application

1. **Start all services:**
```bash
# From project root
docker-compose up -d
```

2. **Verify services:**
```bash
docker-compose ps
# All services should show "Up" status
```

## Verification Checklist

### Database Verification
- [ ] PostgreSQL container running
- [ ] pgvector extension installed
- [ ] All tables migrated successfully
- [ ] Data counts match between SQLite and PostgreSQL
- [ ] Foreign key relationships preserved

### Application Verification
- [ ] Django application starts without errors
- [ ] Admin interface accessible
- [ ] API endpoints functional
- [ ] User authentication working
- [ ] File uploads working

### Vector Operations Verification
- [ ] pgvector extension functional
- [ ] Vector similarity queries working
- [ ] Embedding storage ready for future features

## Rollback Procedure

If migration fails or issues arise:

1. **Stop PostgreSQL services:**
```bash
docker-compose down
```

2. **Revert to SQLite configuration:**
```bash
# In backend/.env
DB_ENGINE=sqlite
```

3. **Restart with SQLite:**
```bash
cd backend
python manage.py runserver
```

## Troubleshooting

### Common Issues

**Issue: PostgreSQL connection refused**
```bash
# Check if container is running
docker-compose ps
docker-compose logs db

# Restart if needed
docker-compose restart db
```

**Issue: Migration command not found**
```bash
# Ensure you're in the backend directory
cd backend
python manage.py help | grep migrate_to_postgresql
```

**Issue: pgvector not installed**
```bash
# Check extension in database
docker exec -it cv_tailor_db psql -U cv_tailor_user -d cv_tailor -c "\\dx"
# Should show vector extension
```

**Issue: Data integrity errors**
```bash
# Verify migration
python manage.py migrate_to_postgresql --verify-only
```

### Performance Optimization

After migration, optimize PostgreSQL performance:

```sql
-- Connect to database
\c cv_tailor

-- Analyze tables for query optimization
ANALYZE;

-- Check database size
SELECT pg_size_pretty(pg_database_size('cv_tailor'));

-- Monitor query performance
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

## Next Steps

After successful migration:

1. **Enable LLM Features**: Follow feature specifications for enhanced artifact processing
2. **Vector Indexing**: Create appropriate vector indexes for your use case
3. **Monitoring**: Set up PostgreSQL monitoring and alerting
4. **Backups**: Configure automated database backups
5. **Production Deployment**: Plan production PostgreSQL deployment

## Support

For issues during migration:
1. Check Docker logs: `docker-compose logs`
2. Verify environment variables in `.env`
3. Test individual components separately
4. Review error messages in detail

The migration preserves all existing functionality while enabling advanced vector search capabilities for future LLM features.