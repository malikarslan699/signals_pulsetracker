-- PulseSignal Pro Database Initialization
-- This runs when PostgreSQL container first starts

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create initial admin user (password: Admin@123456)
-- Password hash will be created by the app on first run
-- This just creates the database schema marker

CREATE TABLE IF NOT EXISTS _schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO _schema_version (version) VALUES ('1.0.0') ON CONFLICT DO NOTHING;
