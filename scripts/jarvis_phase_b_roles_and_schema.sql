-- ============================================================================
-- LeadVoix Business JARVIS — Phase B Database Roles & Schema Setup
-- ============================================================================
-- Purpose: Complete logical and operational isolation between customer SaaS
-- data (public schema) and internal JARVIS operations (jarvis schema).
--
-- Security Model:
-- 1. Dedicated Migration Owner: 'leadvoix_migrator' owns schema 'jarvis' & DDL.
--    Permitted to update 'public.alembic_version'; strictly blocked from SaaS DML.
-- 2. Runtime Reader: 'jarvis_business_reader' has SELECT-only on approved columns
--    across 6 collector tables; zero access to users, transcripts, or credentials.
-- 3. Runtime Operator: 'jarvis_operator' has USAGE (NO CREATE) on schema 'jarvis',
--    operational DML on approved tables, append-only on audit_logs, and ZERO access to public schema.
-- 4. Safe Default Privileges: Future tables created in 'jarvis' default to SELECT, INSERT only.
-- 5. Neither runtime role owns protected schemas or tables.
-- 6. Database Name Portability: Uses current_database() to connect to the active database.
-- 7. Secret Safeguard: Fails immediately if default placeholder passwords are not replaced.
--
-- DO NOT EXECUTE THIS SCRIPT IN APPLICATION CODE.
-- Must be reviewed and executed directly by the Founder / DBA in PostgreSQL.
-- ============================================================================

-- ============================================================================
-- PART 1: PRE-MIGRATION SETUP (Run before 'alembic upgrade head')
-- ============================================================================

BEGIN;

-- 1. Secret Safeguard & Dynamic Role Setup
-- NOTE FOR DBA / FOUNDER:
-- Replace the placeholder passwords below with cryptographically random secrets before execution.
DO $$
DECLARE
    migrator_pw text := 'REPLACE_WITH_STRONG_SECRET_MIGRATOR';
    reader_pw   text := 'REPLACE_WITH_STRONG_SECRET_READONLY';
    operator_pw text := 'REPLACE_WITH_STRONG_SECRET_OPERATOR';
    curr_db     text := current_database();
BEGIN
    -- Fail-closed safeguard: abort execution if placeholders were not changed
    IF migrator_pw LIKE 'REPLACE_%' OR reader_pw LIKE 'REPLACE_%' OR operator_pw LIKE 'REPLACE_%' THEN
        RAISE EXCEPTION 'Security Violation: Placeholder passwords detected. Replace placeholder passwords with strong secrets before executing.';
    END IF;

    -- Create Dedicated Migration Owner Role (Strict Least Privilege: NOCREATEDB, NOSUPERUSER, NOCREATEROLE)
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'leadvoix_migrator') THEN
        EXECUTE format('CREATE ROLE leadvoix_migrator WITH LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L;', migrator_pw);
    ELSE
        EXECUTE format('ALTER ROLE leadvoix_migrator WITH LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L;', migrator_pw);
    END IF;

    -- Create Runtime Reader Role (if not exists)
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'jarvis_business_reader') THEN
        EXECUTE format('CREATE ROLE jarvis_business_reader WITH LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L;', reader_pw);
    ELSE
        EXECUTE format('ALTER ROLE jarvis_business_reader WITH LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L;', reader_pw);
    END IF;

    -- Create Runtime Operator Role (if not exists)
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'jarvis_operator') THEN
        EXECUTE format('CREATE ROLE jarvis_operator WITH LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L;', operator_pw);
    ELSE
        EXECUTE format('ALTER ROLE jarvis_operator WITH LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L;', operator_pw);
    END IF;

    -- Grant CONNECT on the current active database dynamically (supports postgres, leadvoix_staging, Render, Supabase, etc.)
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO leadvoix_migrator;', curr_db);
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO jarvis_business_reader;', curr_db);
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO jarvis_operator;', curr_db);
END $$;

-- 2. Bootstrap Schema 'jarvis' via Privileged Connection and Assign Ownership to Migration Owner
CREATE SCHEMA IF NOT EXISTS jarvis;
ALTER SCHEMA jarvis OWNER TO leadvoix_migrator;
GRANT ALL ON SCHEMA jarvis TO leadvoix_migrator;
REVOKE ALL ON SCHEMA jarvis FROM PUBLIC;

-- 3. Customer SaaS Data Protection (Schema 'public' Boundary Isolation)
-- A. jarvis_operator: ZERO ACCESS TO PUBLIC SCHEMA OR CUSTOMER TABLES
REVOKE ALL ON SCHEMA public FROM jarvis_operator;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM jarvis_operator;

-- B. leadvoix_migrator: ZERO ACCESS TO CUSTOMER SAAS TABLES (Alembic version table only)
GRANT USAGE ON SCHEMA public TO leadvoix_migrator;
REVOKE CREATE ON SCHEMA public FROM leadvoix_migrator;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM leadvoix_migrator;

-- C. Pre-migration check: Enforce that core customer SaaS migrations are complete (base revision: 3c8d1e2f4a5b)
DO $$
DECLARE
    curr_rev text;
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version') THEN
        RAISE EXCEPTION 'Alembic Safety Violation: public.alembic_version does not exist. Core SaaS migrations (up to 3c8d1e2f4a5b) must be applied by database admin before JARVIS setup.';
    END IF;

    SELECT version_num INTO curr_rev FROM public.alembic_version LIMIT 1;
    IF curr_rev IS NULL OR curr_rev NOT IN ('3c8d1e2f4a5b', '4f7e2a1b9c3d') THEN
        RAISE EXCEPTION 'Alembic Safety Violation: Expected base revision 3c8d1e2f4a5b (or 4f7e2a1b9c3d), but found %. Core SaaS migrations must be fully up-to-date.', curr_rev;
    END IF;

    -- Grant exact least-privilege DML required for Alembic revision tracking only
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.alembic_version TO leadvoix_migrator;
END $$;

-- D. jarvis_business_reader: STRICT MINIMAL COLUMN-LEVEL ACCESS TO 6 COLLECTOR TABLES ONLY
GRANT USAGE ON SCHEMA public TO jarvis_business_reader;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM jarvis_business_reader;

-- 1. Organizations: id, name, slug, plan only (Twilio credentials & settings shielded)
GRANT SELECT (id, name, slug, plan) ON TABLE public.organizations TO jarvis_business_reader;
-- 2. Leads: aggregate metrics columns only (personal names, phones, emails shielded)
GRANT SELECT (id, organization_id, status, source, created_at) ON TABLE public.leads TO jarvis_business_reader;
-- 3. Agent Calls: duration & direction only (caller phone numbers & audio recordings shielded)
GRANT SELECT (id, organization_id, duration, status, direction, created_at) ON TABLE public.agent_calls TO jarvis_business_reader;
-- 4. Deals: status & amount only (contact/account details shielded)
GRANT SELECT (id, organization_id, status, amount, created_at) ON TABLE public.deals TO jarvis_business_reader;
-- 5. Tasks: status only (task descriptions & assignees shielded)
GRANT SELECT (id, organization_id, status, created_at) ON TABLE public.tasks TO jarvis_business_reader;
-- 6. Call Processing Jobs: status & call link only
GRANT SELECT (id, status, agent_call_id, created_at) ON TABLE public.call_processing_jobs TO jarvis_business_reader;

-- 4. Schema 'jarvis' Runtime Access: USAGE ONLY (Strictly NO CREATE)
GRANT USAGE ON SCHEMA jarvis TO jarvis_business_reader;
GRANT USAGE ON SCHEMA jarvis TO jarvis_operator;

REVOKE CREATE ON SCHEMA jarvis FROM jarvis_business_reader;
REVOKE CREATE ON SCHEMA jarvis FROM jarvis_operator;

-- 5. Safe Default Privileges for Tables Created by Migration Owner
-- Security Inversion: Future tables default to SELECT, INSERT ONLY for jarvis_operator.
-- This ensures jarvis.audit_logs NEVER inherits UPDATE or DELETE privileges by default.
ALTER DEFAULT PRIVILEGES FOR ROLE leadvoix_migrator IN SCHEMA jarvis 
    GRANT SELECT, INSERT ON TABLES TO jarvis_operator;
ALTER DEFAULT PRIVILEGES FOR ROLE leadvoix_migrator IN SCHEMA jarvis 
    GRANT USAGE, SELECT ON SEQUENCES TO jarvis_operator;
ALTER DEFAULT PRIVILEGES FOR ROLE leadvoix_migrator IN SCHEMA jarvis 
    GRANT SELECT ON TABLES TO jarvis_business_reader;

-- Fallback default privileges if migration runs as postgres / supabase_admin:
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA jarvis 
    GRANT SELECT, INSERT ON TABLES TO jarvis_operator;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA jarvis 
    GRANT USAGE, SELECT ON SEQUENCES TO jarvis_operator;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA jarvis 
    GRANT SELECT ON TABLES TO jarvis_business_reader;

COMMIT;

-- ============================================================================
-- PART 2: POST-MIGRATION HARDENING (Run immediately after 'alembic upgrade head')
-- ============================================================================
-- Note: The Alembic migration automatically applies these grants during upgrade.
-- This block is provided as a standalone hardening and verification script.
--
-- SECURITY ARCHITECTURE & THREAT MODEL:
-- 1. Dual-Layer Defense:
--    a. Role Layer: jarvis_operator is granted SELECT and INSERT only on jarvis.audit_logs.
--       UPDATE, DELETE, and TRUNCATE are explicitly REVOKED.
--    b. Trigger Layer: A database-level BEFORE UPDATE OR DELETE trigger raises an uncatchable
--       exception if ANY role attempts row mutation or deletion, even if permissions
--       are inadvertently modified. A BEFORE TRUNCATE trigger blocks table truncation.
-- 2. Runtime Protection:
--    Neither jarvis_operator nor jarvis_business_reader can bypass or alter this trigger
--    because both roles have USAGE only on schema jarvis with strictly NO CREATE or ALTER.
-- 3. Database-Owner / Superuser Limitation:
--    In PostgreSQL, a database superuser (e.g. postgres, cloud platform root) or the
--    table owner (leadvoix_migrator) possesses DDL rights and can execute
--    'ALTER TABLE jarvis.audit_logs DISABLE TRIGGER ALL;' or 'DROP TRIGGER ...'.
--    PostgreSQL engines cannot prevent superusers or table owners from modifying table
--    definitions. However, application services authenticate exclusively as jarvis_operator
--    (which has zero DDL privileges) and cannot disable, drop, or bypass the trigger.
-- ============================================================================

BEGIN;

-- 1. Explicit operational table permissions for jarvis_operator (grants UPDATE/DELETE to mutable queues):
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE jarvis.jarvis_tasks TO jarvis_operator;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE jarvis.dispatch_idempotency TO jarvis_operator;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE jarvis.task_attempts TO jarvis_operator;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE jarvis.approval_records TO jarvis_operator;

-- 2. Audit Log Immutability: SELECT and INSERT only. Block UPDATE, DELETE, and TRUNCATE:
GRANT SELECT, INSERT ON TABLE jarvis.audit_logs TO jarvis_operator;
REVOKE UPDATE, DELETE, TRUNCATE ON TABLE jarvis.audit_logs FROM jarvis_operator;

-- 3. Sequences:
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA jarvis TO jarvis_operator;

-- 4. Read-only access for jarvis_business_reader across all jarvis tables:
GRANT SELECT ON ALL TABLES IN SCHEMA jarvis TO jarvis_business_reader;

-- 5. Audit Log Database-Level Append-Only Trigger
CREATE OR REPLACE FUNCTION jarvis.prevent_audit_log_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Security Violation: jarvis.audit_logs is an append-only audit trail. % operations are strictly forbidden.', TG_OP;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_protect_audit_logs_mutation ON jarvis.audit_logs;
CREATE TRIGGER trg_protect_audit_logs_mutation
BEFORE UPDATE OR DELETE ON jarvis.audit_logs
FOR EACH ROW
EXECUTE FUNCTION jarvis.prevent_audit_log_mutation();

DROP TRIGGER IF EXISTS trg_protect_audit_logs_truncate ON jarvis.audit_logs;
CREATE TRIGGER trg_protect_audit_logs_truncate
BEFORE TRUNCATE ON jarvis.audit_logs
FOR EACH STATEMENT
EXECUTE FUNCTION jarvis.prevent_audit_log_mutation();

COMMIT;
