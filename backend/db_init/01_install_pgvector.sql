-- Initialize PostgreSQL database for CV Tailor with pgvector extension
-- This script runs automatically when the Docker container starts

-- Install pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database user if not exists (in case of manual setup)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cv_tailor_user') THEN
      CREATE ROLE cv_tailor_user WITH LOGIN PASSWORD 'cv_tailor_dev_password';
   END IF;
END
$$;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE cv_tailor TO cv_tailor_user;

-- Allow the user to create extensions (needed for potential future extensions)
ALTER USER cv_tailor_user CREATEDB;

-- Set default timezone
SET timezone = 'UTC';

-- Show installed extensions for verification
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Verify pgvector is working with a test query
SELECT vector_dims(ARRAY[1,2,3]::vector);

COMMENT ON DATABASE cv_tailor IS 'CV Tailor application database with pgvector support for semantic similarity search';