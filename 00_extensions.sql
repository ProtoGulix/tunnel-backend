-- ============================================================================
-- 00_extensions.sql - Extensions PostgreSQL requises
-- ============================================================================
-- Extension nécessaire pour génération UUID
--
-- @requires PostgreSQL >= 12
-- @see https://www.postgresql.org/docs/current/uuid-ossp.html
-- ============================================================================

-- Extension génération UUID (v4)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';
