-- Migration: Add qa_access column to users table
-- Run once on existing deployments
ALTER TABLE users ADD COLUMN IF NOT EXISTS qa_access BOOLEAN NOT NULL DEFAULT FALSE;
