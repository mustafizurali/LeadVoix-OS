"""
LeadVoix Business JARVIS — Step 5: Real PostgreSQL 18 Staging Verification Harness (Revised v3)

Performs comprehensive real database isolation, migration, dual-layer least-privilege,
and multi-process queue concurrency verification against a freshly initialized,
ephemeral PostgreSQL 18 instance.

Safety Guarantees & Non-Destructive Invariants:
1. Fresh Run Directory: Every run creates a uniquely named data directory under
   scratch/runs/pg18_staging_<timestamp>_<hex>. Never reuses fixed directories.
2. Explicit initdb & Cluster Verification: Runs initdb explicitly with temporary SCRAM
   password authentication. Validates resulting PG_VERSION, postmaster.pid, port,
   and cluster identity before connecting.
3. Port Conflict Guard: Verifies staging port 5433 is free before starting.
   Refuses to continue if the port is in use or the directory is already present.
4. Unique Staging Database: Database is named leadvoix_staging_<run_id>.
   Aborts if the database already exists.
5. No In-Place Deletions: Starts with a fresh database; never deletes pre-existing tasks.
6. Process Isolation: Starts postgres directly with PID tracking and stops ONLY
   that specific PID. If startup verification fails, cleans up the spawned process immediately.
7. Server Logging: Redirects PostgreSQL stdout and stderr to the run's server.log.
   Verifies the log file exists, contains data, and is retained after shutdown.
8. Separate Trigger vs Permission Verification:
   - Asserts InsufficientPrivilege (permission denial) for jarvis_operator.
   - Asserts RaiseException from trg_protect_audit_logs_mutation / trg_protect_audit_logs_truncate
     for table owner (leadvoix_migrator).
9. Lease Recovery ID Verification: Identifies the exact claimed task dynamically,
   captures its ID, and asserts that precisely that task is reclaimed and re-claimed.
10. Zero Production / Port 5432 Impact: Completely isolated from port 5432 and remote hosts.
11. Secret-Safe Child Process Runner & Robust Process Cleanup: Passes connection URL strictly
    via process environment variables (JARVIS_OPERATIONAL_DATABASE_URL). Ephemeral worker_runner.py
    contains zero credentials, secrets, or connection strings. Both child Popen processes are
    guaranteed to be terminated and waited for in a try...finally block on timeouts or exceptions
    prior to deleting worker_runner.py. Only the exact child processes spawned are affected.
    Child stderr is strictly sanitized to prevent any database credentials or environment
    variables from leaking into exception messages.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import logging
import os
import re
import secrets
import socket
import subprocess
import sys
import time

from alembic.config import Config
from alembic import command
import psycopg2
from psycopg2.errors import InsufficientPrivilege, RaiseException
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# --- Configuration & Paths ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PG_BIN_DIR = r"C:\Program Files\PostgreSQL\18\bin"
INITDB_EXE = os.path.join(PG_BIN_DIR, "initdb.exe")
POSTGRES_EXE = os.path.join(PG_BIN_DIR, "postgres.exe")
PG_CTL_EXE = os.path.join(PG_BIN_DIR, "pg_ctl.exe")

RUNS_BASE_DIR = os.path.join(
    os.path.expanduser("~"),
    ".gemini",
    "antigravity",
    "brain",
    "b2eb0bff-28c1-4528-9a0f-c22c66d9ec55",
    "scratch",
    "runs",
)

# Unique run identity (timestamp + random token)
RUN_TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
RUN_TOKEN = secrets.token_hex(4)
RUN_ID = f"{RUN_TIMESTAMP}_{RUN_TOKEN}"

RUN_DATA_DIR = os.path.join(RUNS_BASE_DIR, f"pg18_staging_{RUN_ID}")
SERVER_LOG_FILE = os.path.join(RUN_DATA_DIR, "server.log")
STAGING_PORT = 5433
STAGING_DB_NAME = f"leadvoix_staging_{RUN_ID}"

# Ephemeral role secrets (generated randomly for this test run only; never printed or logged)
SUPERUSER_PW = "stg_su_" + secrets.token_hex(16)
MIGRATOR_PW = "stg_mig_" + secrets.token_hex(16)
READER_PW = "stg_rdr_" + secrets.token_hex(16)
OPERATOR_PW = "stg_opr_" + secrets.token_hex(16)

SUPERUSER_URL = f"postgresql://postgres:{SUPERUSER_PW}@127.0.0.1:{STAGING_PORT}/{STAGING_DB_NAME}"
SUPERUSER_POSTGRES_URL = f"postgresql://postgres:{SUPERUSER_PW}@127.0.0.1:{STAGING_PORT}/postgres"
MIGRATOR_URL = f"postgresql://leadvoix_migrator:{MIGRATOR_PW}@127.0.0.1:{STAGING_PORT}/{STAGING_DB_NAME}"
READER_URL = f"postgresql://jarvis_business_reader:{READER_PW}@127.0.0.1:{STAGING_PORT}/{STAGING_DB_NAME}"
OPERATOR_URL = f"postgresql://jarvis_operator:{OPERATOR_PW}@127.0.0.1:{STAGING_PORT}/{STAGING_DB_NAME}"


def check_environment_and_port_safety():
    """Validates port isolation, binary existence, and directory freshness."""
    print(f"[1/8] Verifying environment and port safety...")
    
    # 1. Enforce port isolation: STAGING_PORT must NEVER be 5432
    assert STAGING_PORT != 5432, "CRITICAL SAFETY VIOLATION: Staging port cannot be 5432 (default production/dev port)!"
    
    # 2. Verify PostgreSQL 18 binaries exist
    for binary_path in [INITDB_EXE, POSTGRES_EXE, PG_CTL_EXE]:
        if not os.path.isfile(binary_path):
            raise FileNotFoundError(f"Required PostgreSQL 18 binary not found: {binary_path}")
            
    # 3. Refuse to continue if STAGING_PORT is already occupied
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        port_check = s.connect_ex(("127.0.0.1", STAGING_PORT))
        if port_check == 0:
            raise RuntimeError(
                f"SAFETY VIOLATION: Port {STAGING_PORT} is already occupied by an active process. "
                "Refusing to proceed to prevent colliding with any running service."
            )
            
    # 4. Refuse to continue if RUN_DATA_DIR already exists
    if os.path.exists(RUN_DATA_DIR):
        raise RuntimeError(
            f"SAFETY VIOLATION: Target data directory '{RUN_DATA_DIR}' already exists. "
            "Refusing to reuse existing directories."
        )
        
    print(f"      Port {STAGING_PORT} is free and available.")
    print(f"      Target data directory is unique: {RUN_DATA_DIR}")


def init_fresh_cluster():
    """Runs initdb explicitly with temporary SCRAM authentication."""
    print(f"[2/8] Creating fresh PostgreSQL 18 cluster with SCRAM authentication...")
    os.makedirs(RUNS_BASE_DIR, exist_ok=True)
    os.makedirs(RUN_DATA_DIR, exist_ok=False)
    
    # Write temporary password file in RUNS_BASE_DIR (outside RUN_DATA_DIR so data dir remains empty for initdb)
    temp_pw_file = os.path.join(RUNS_BASE_DIR, f".init_pw_{RUN_ID}.tmp")
    with open(temp_pw_file, "w", encoding="utf-8") as f:
        f.write(SUPERUSER_PW)
        
    try:
        cmd = [
            INITDB_EXE,
            "-D", RUN_DATA_DIR,
            "-U", "postgres",
            "--auth=scram-sha-256",
            f"--pwfile={temp_pw_file}",
            "--encoding=UTF8",
            "--no-instructions",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"initdb failed (exit code {res.returncode}):\n{res.stderr}\n{res.stdout}")
    finally:
        if os.path.exists(temp_pw_file):
            os.remove(temp_pw_file)
            
    # Verify resulting cluster files
    version_file = os.path.join(RUN_DATA_DIR, "PG_VERSION")
    conf_file = os.path.join(RUN_DATA_DIR, "postgresql.conf")
    assert os.path.isfile(version_file), f"initdb did not create {version_file}"
    assert os.path.isfile(conf_file), f"initdb did not create {conf_file}"
    
    with open(version_file, "r") as f:
        version_num = f.read().strip()
    assert version_num == "18", f"Expected PostgreSQL version 18, found {version_num}"
    
    # Configure port, address binding strictly to 127.0.0.1, and fast test performance
    with open(conf_file, "a", encoding="utf-8") as f:
        f.write(
            f"\nport = {STAGING_PORT}\n"
            "listen_addresses = '127.0.0.1'\n"
            "fsync = off\n"
            "synchronous_commit = off\n"
        )
        
    print(f"      Cluster initialized successfully (PostgreSQL {version_num}, SCRAM auth enabled).")


def start_verified_postgres():
    """
    Starts PostgreSQL 18 process, redirects logs to server.log, and verifies PID,
    port, and cluster identity. If verification fails, cleanly terminates the spawned process.
    """
    print(f"[3/8] Starting PostgreSQL 18 on port {STAGING_PORT} (logging to server.log)...")
    server_log_handle = open(SERVER_LOG_FILE, "a", encoding="utf-8")
    proc = subprocess.Popen(
        [POSTGRES_EXE, "-D", RUN_DATA_DIR, "-p", str(STAGING_PORT)],
        stdout=server_log_handle,
        stderr=subprocess.STDOUT,
    )
    expected_pid = proc.pid
    
    try:
        # Wait for server connection
        connected = False
        last_conn_err = None
        for attempt in range(25):
            try:
                conn = psycopg2.connect(
                    host="127.0.0.1",
                    port=STAGING_PORT,
                    user="postgres",
                    password=SUPERUSER_PW,
                    dbname="postgres",
                    connect_timeout=1,
                )
                conn.close()
                connected = True
                break
            except Exception as e:
                last_conn_err = e
                time.sleep(0.4)
                
        if not connected:
            raise RuntimeError(f"Failed to connect to isolated PostgreSQL server on port {STAGING_PORT}: {last_conn_err}")
            
        # Verify postmaster.pid file exists and matches our expected PID and port
        pid_file = os.path.join(RUN_DATA_DIR, "postmaster.pid")
        assert os.path.isfile(pid_file), f"postmaster.pid file missing in {RUN_DATA_DIR}"
        with open(pid_file, "r") as f:
            pid_lines = [line.strip() for line in f]
        recorded_pid = int(pid_lines[0])
        recorded_port = int(pid_lines[3])
        
        assert recorded_pid == expected_pid, f"PID mismatch: expected {expected_pid}, postmaster recorded {recorded_pid}"
        assert recorded_port == STAGING_PORT, f"Port mismatch: expected {STAGING_PORT}, postmaster recorded {recorded_port}"
        
        # Verify cluster identity via SQL query
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=STAGING_PORT,
            user="postgres",
            password=SUPERUSER_PW,
            dbname="postgres",
        )
        cur = conn.cursor()
        cur.execute("SELECT current_setting('data_directory'), current_setting('port'), version();")
        active_data_dir, active_port, active_version = cur.fetchone()
        cur.close()
        conn.close()
        
        assert os.path.normpath(active_data_dir) == os.path.normpath(RUN_DATA_DIR), (
            f"Cluster data directory mismatch! Expected {RUN_DATA_DIR}, active server reported {active_data_dir}"
        )
        assert int(active_port) == STAGING_PORT, f"Cluster port mismatch! Expected {STAGING_PORT}, reported {active_port}"
        assert "PostgreSQL 18" in active_version, f"Version mismatch: {active_version}"
        
        print(f"      VERIFIED: Connected to PID {expected_pid} on port {STAGING_PORT}.")
        print(f"      VERIFIED: Data directory confirmed as {RUN_DATA_DIR}.")
        return proc, server_log_handle
    except Exception as exc:
        print(f"      Startup verification failed ({exc}). Terminating spawned process {expected_pid}...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
            proc.wait(timeout=5)
        server_log_handle.close()
        raise


def stop_verified_postgres(proc, server_log_handle):
    """Safely terminates ONLY the exact process spawned by this script and preserves logs."""
    target_pid = proc.pid
    print(f"[8/8] Safely stopping PostgreSQL 18 process (PID {target_pid})...")
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
        proc.wait(timeout=5)
        
    if server_log_handle is not None and not server_log_handle.closed:
        server_log_handle.flush()
        server_log_handle.close()
        
    # Verify server.log exists and is preserved
    assert os.path.isfile(SERVER_LOG_FILE), f"server.log was not created at {SERVER_LOG_FILE}"
    log_size = os.path.getsize(SERVER_LOG_FILE)
    assert log_size > 0, f"server.log is empty!"
    print(f"      Process {target_pid} terminated cleanly.")
    print(f"      Server log preserved ({log_size} bytes): {SERVER_LOG_FILE}")


def create_unique_staging_database():
    """Creates a uniquely named staging database. Aborts if it already exists."""
    print(f"[4/8] Creating unique staging database '{STAGING_DB_NAME}'...")
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=STAGING_PORT,
        user="postgres",
        password=SUPERUSER_PW,
        dbname="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (STAGING_DB_NAME,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise RuntimeError(f"SAFETY VIOLATION: Database '{STAGING_DB_NAME}' already exists! Aborting.")
        
    cur.execute(f"CREATE DATABASE {STAGING_DB_NAME};")
    cur.close()
    conn.close()
    print(f"      Created fresh staging database '{STAGING_DB_NAME}'.")


def run_migrations_and_ddl():
    """Applies SaaS migrations, Phase B roles, and JARVIS operational migrations."""
    print(f"[5/8] Running Alembic migrations and Phase B DDL...")

    # 1. Base SaaS migrations up to 3c8d1e2f4a5b
    os.environ["MIGRATION_DATABASE_URL"] = SUPERUSER_URL
    cfg = Config(os.path.join(BASE_DIR, "alembic.ini"))
    print("      Applying core SaaS migrations up to 3c8d1e2f4a5b...")
    command.upgrade(cfg, "3c8d1e2f4a5b")

    # 2. Apply scripts/jarvis_phase_b_roles_and_schema.sql (Part 1)
    print("      Applying Phase B Setup SQL (roles, schema, public boundaries)...")
    sql_path = os.path.join(BASE_DIR, "scripts", "jarvis_phase_b_roles_and_schema.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Replace placeholders with strong staging secrets
    part1_sql = sql_content.replace("'REPLACE_WITH_STRONG_SECRET_MIGRATOR'", f"'{MIGRATOR_PW}'")
    part1_sql = part1_sql.replace("'REPLACE_WITH_STRONG_SECRET_READONLY'", f"'{READER_PW}'")
    part1_sql = part1_sql.replace("'REPLACE_WITH_STRONG_SECRET_OPERATOR'", f"'{OPERATOR_PW}'")

    conn = psycopg2.connect(SUPERUSER_URL)
    conn.autocommit = True
    cur = conn.cursor()
    part1_code = part1_sql.split("-- PART 2: POST-MIGRATION HARDENING")[0]
    cur.execute(part1_code)

    # 3. Apply Phase B Alembic migration 4f7e2a1b9c3d under leadvoix_migrator
    print("      Applying Phase B migration 4f7e2a1b9c3d via leadvoix_migrator...")
    os.environ["MIGRATION_DATABASE_URL"] = MIGRATOR_URL
    command.upgrade(cfg, "4f7e2a1b9c3d")

    # 4. Apply Part 2 hardening
    print("      Applying Phase B Hardening SQL (triggers, sequences, permissions)...")
    part2_code = part1_sql.split("-- PART 2: POST-MIGRATION HARDENING")[1]
    part2_exec = "BEGIN;" + part2_code.split("BEGIN;", 1)[1]
    cur.execute(part2_exec)
    cur.close()
    conn.close()

    # Verify public.alembic_version
    conn = psycopg2.connect(SUPERUSER_URL)
    cur = conn.cursor()
    cur.execute("SELECT version_num FROM public.alembic_version;")
    current_rev = cur.fetchone()[0]
    assert current_rev == "4f7e2a1b9c3d", f"Expected revision 4f7e2a1b9c3d, found {current_rev}"
    print(f"      Verified public.alembic_version revision: {current_rev}")

    # Verify 5 jarvis tables
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'jarvis' ORDER BY table_name;
    """)
    tables = [r[0] for r in cur.fetchall()]
    expected_tables = ["approval_records", "audit_logs", "dispatch_idempotency", "jarvis_tasks", "task_attempts"]
    assert tables == expected_tables, f"Tables mismatch: {tables} vs {expected_tables}"
    print(f"      Verified all 5 operational tables in 'jarvis' schema: {tables}")
    cur.close()
    conn.close()


def verify_least_privilege_permissions():
    """Tests least-privilege matrix for migrator, reader, and operator."""
    print(f"[6/8] Verifying PostgreSQL least-privilege security matrix...")

    # --- Test 1: leadvoix_migrator ---
    conn_mig = psycopg2.connect(MIGRATOR_URL)
    cur_mig = conn_mig.cursor()
    cur_mig.execute("SELECT version_num FROM public.alembic_version;")
    assert cur_mig.fetchone()[0] == "4f7e2a1b9c3d"

    # Assert NO database-level CREATE for leadvoix_migrator
    cur_mig.execute("SELECT has_database_privilege('leadvoix_migrator', current_database(), 'CREATE');")
    assert cur_mig.fetchone()[0] is False, "Security violation: leadvoix_migrator has database-level CREATE!"
    print("      PASS: leadvoix_migrator has NO database-level CREATE privilege")

    try:
        cur_mig.execute("SELECT * FROM public.users;")
        raise AssertionError("Security violation: leadvoix_migrator was able to query public.users!")
    except InsufficientPrivilege:
        conn_mig.rollback()
        print("      PASS: leadvoix_migrator blocked from querying public.users (InsufficientPrivilege)")
    cur_mig.close()
    conn_mig.close()

    # --- Test 2: jarvis_business_reader ---
    conn_rdr = psycopg2.connect(READER_URL)
    cur_rdr = conn_rdr.cursor()
    cur_rdr.execute("SELECT id, name, slug, plan FROM public.organizations;")
    print("      PASS: jarvis_business_reader queried approved columns on public.organizations")

    # Assert NO database-level CREATE for jarvis_business_reader
    cur_rdr.execute("SELECT has_database_privilege('jarvis_business_reader', current_database(), 'CREATE');")
    assert cur_rdr.fetchone()[0] is False, "Security violation: jarvis_business_reader has database-level CREATE!"
    print("      PASS: jarvis_business_reader has NO database-level CREATE privilege")

    try:
        cur_rdr.execute("SELECT * FROM public.users;")
        raise AssertionError("Security violation: jarvis_business_reader was able to query public.users!")
    except InsufficientPrivilege:
        conn_rdr.rollback()
        print("      PASS: jarvis_business_reader blocked from querying public.users (InsufficientPrivilege)")
    try:
        cur_rdr.execute("SELECT first_name, phone FROM public.leads;")
        raise AssertionError("Security violation: jarvis_business_reader was able to query PII on public.leads!")
    except InsufficientPrivilege:
        conn_rdr.rollback()
        print("      PASS: jarvis_business_reader blocked from querying PII on public.leads (InsufficientPrivilege)")
    try:
        cur_rdr.execute("INSERT INTO public.organizations (name, slug) VALUES ('Hacked', 'hacked');")
        raise AssertionError("Security violation: jarvis_business_reader was able to INSERT into public.organizations!")
    except InsufficientPrivilege:
        conn_rdr.rollback()
        print("      PASS: jarvis_business_reader blocked from INSERT into public.organizations (InsufficientPrivilege)")
    cur_rdr.close()
    conn_rdr.close()

    # --- Test 3: jarvis_operator ---
    conn_opr = psycopg2.connect(OPERATOR_URL)
    cur_opr = conn_opr.cursor()

    # Assert NO database-level CREATE for jarvis_operator
    cur_opr.execute("SELECT has_database_privilege('jarvis_operator', current_database(), 'CREATE');")
    assert cur_opr.fetchone()[0] is False, "Security violation: jarvis_operator has database-level CREATE!"
    print("      PASS: jarvis_operator has NO database-level CREATE privilege")
    try:
        cur_opr.execute("SELECT * FROM public.users;")
        raise AssertionError("Security violation: jarvis_operator was able to query public.users!")
    except InsufficientPrivilege:
        conn_opr.rollback()
        print("      PASS: jarvis_operator blocked from querying public.users (InsufficientPrivilege)")
    try:
        cur_opr.execute("SELECT * FROM public.leads;")
        raise AssertionError("Security violation: jarvis_operator was able to query public.leads!")
    except InsufficientPrivilege:
        conn_opr.rollback()
        print("      PASS: jarvis_operator blocked from querying public.leads (InsufficientPrivilege)")
    try:
        cur_opr.execute("CREATE TABLE jarvis.hack_table (id serial primary key);")
        raise AssertionError("Security violation: jarvis_operator was able to CREATE TABLE in schema jarvis!")
    except InsufficientPrivilege:
        conn_opr.rollback()
        print("      PASS: jarvis_operator blocked from CREATE TABLE in schema jarvis (InsufficientPrivilege)")
    
    # Valid operational DML on jarvis_tasks
    cur_opr.execute("""
        INSERT INTO jarvis.jarvis_tasks (task_type, payload) 
        VALUES ('test_permission', '{"test": true}') RETURNING id;
    """)
    tid = cur_opr.fetchone()[0]
    conn_opr.commit()
    print(f"      PASS: jarvis_operator inserted task #{tid} into jarvis.jarvis_tasks")

    cur_opr.execute("DELETE FROM jarvis.jarvis_tasks WHERE id = %s;", (tid,))
    conn_opr.commit()
    cur_opr.close()
    conn_opr.close()


def verify_audit_log_protections_distinguished():
    """
    Separately verifies:
    1. Role-Level Permission Denial (InsufficientPrivilege) for jarvis_operator.
    2. Database-Level Trigger Rejection (RaiseException) for table owner (leadvoix_migrator).
    """
    print(f"[7/8] Verifying audit log protections (distinguishing permissions vs triggers)...")

    # 1. Insert a baseline audit log entry using jarvis_operator (permitted to INSERT)
    conn_opr = psycopg2.connect(OPERATOR_URL)
    cur_opr = conn_opr.cursor()
    cur_opr.execute("""
        INSERT INTO jarvis.audit_logs (event_type, actor, organization_id, details)
        VALUES ('TEST_AUDIT_SECURITY', 'sec_probe', 1, '{"test": true}')
        RETURNING id;
    """)
    audit_id = cur_opr.fetchone()[0]
    conn_opr.commit()
    print(f"      Seeded audit log record #{audit_id} as jarvis_operator.")

    # --- PART A: Verify Role Permission Denial for jarvis_operator ---
    print("      --- Part A: Testing jarvis_operator role-level grants (InsufficientPrivilege) ---")
    
    # A1: UPDATE -> Role permission denial
    try:
        cur_opr.execute("UPDATE jarvis.audit_logs SET actor = 'tampered' WHERE id = %s;", (audit_id,))
        conn_opr.commit()
        raise AssertionError("Violation: jarvis_operator UPDATE on audit_logs succeeded!")
    except InsufficientPrivilege:
        conn_opr.rollback()
        print("      PASS: jarvis_operator UPDATE rejected by role permissions (InsufficientPrivilege).")

    # A2: DELETE -> Role permission denial
    try:
        cur_opr.execute("DELETE FROM jarvis.audit_logs WHERE id = %s;", (audit_id,))
        conn_opr.commit()
        raise AssertionError("Violation: jarvis_operator DELETE on audit_logs succeeded!")
    except InsufficientPrivilege:
        conn_opr.rollback()
        print("      PASS: jarvis_operator DELETE rejected by role permissions (InsufficientPrivilege).")

    # A3: TRUNCATE -> Role permission denial
    try:
        cur_opr.execute("TRUNCATE jarvis.audit_logs;")
        conn_opr.commit()
        raise AssertionError("Violation: jarvis_operator TRUNCATE on audit_logs succeeded!")
    except InsufficientPrivilege:
        conn_opr.rollback()
        print("      PASS: jarvis_operator TRUNCATE rejected by role permissions (InsufficientPrivilege).")
        
    cur_opr.close()
    conn_opr.close()

    # --- PART B: Verify Database Trigger Rejection for table owner (leadvoix_migrator) ---
    print("      --- Part B: Testing table owner triggers (RaiseException from prevent_audit_log_mutation) ---")
    conn_mig = psycopg2.connect(MIGRATOR_URL)
    cur_mig = conn_mig.cursor()

    # B1: UPDATE -> Trigger rejection
    try:
        cur_mig.execute("UPDATE jarvis.audit_logs SET actor = 'tampered' WHERE id = %s;", (audit_id,))
        conn_mig.commit()
        raise AssertionError("Violation: leadvoix_migrator UPDATE on audit_logs succeeded!")
    except RaiseException as exc:
        conn_mig.rollback()
        assert "Security Violation: jarvis.audit_logs is an append-only audit trail" in str(exc)
        assert "UPDATE" in str(exc)
        print("      PASS: leadvoix_migrator UPDATE rejected by database trigger (RaiseException).")

    # B2: DELETE -> Trigger rejection
    try:
        cur_mig.execute("DELETE FROM jarvis.audit_logs WHERE id = %s;", (audit_id,))
        conn_mig.commit()
        raise AssertionError("Violation: leadvoix_migrator DELETE on audit_logs succeeded!")
    except RaiseException as exc:
        conn_mig.rollback()
        assert "Security Violation: jarvis.audit_logs is an append-only audit trail" in str(exc)
        assert "DELETE" in str(exc)
        print("      PASS: leadvoix_migrator DELETE rejected by database trigger (RaiseException).")

    # B3: TRUNCATE -> Statement trigger rejection
    try:
        cur_mig.execute("TRUNCATE jarvis.audit_logs;")
        conn_mig.commit()
        raise AssertionError("Violation: leadvoix_migrator TRUNCATE on audit_logs succeeded!")
    except RaiseException as exc:
        conn_mig.rollback()
        assert "Security Violation: jarvis.audit_logs is an append-only audit trail" in str(exc)
        assert "TRUNCATE" in str(exc)
        print("      PASS: leadvoix_migrator TRUNCATE rejected by database trigger (RaiseException).")

    cur_mig.close()
    conn_mig.close()


def sanitize_diagnostic_output(text_val: str) -> str:
    """
    Sanitizes process output and exception messages:
    Removes database passwords, connection URLs, and auth tokens.
    """
    if not text_val:
        return ""
    # Redact URL credentials: protocol://user:pass@host:port/dbname
    sanitized = re.sub(r"://([^:]+):([^@]+)@", r"://\1:<redacted_secret>@", text_val)
    # Redact known ephemeral secrets generated in this run
    for secret in (SUPERUSER_PW, MIGRATOR_PW, READER_PW, OPERATOR_PW):
        sanitized = sanitized.replace(secret, "<redacted_secret>")
    # Redact connection environment variables if present
    sanitized = re.sub(r"(JARVIS_OPERATIONAL_DATABASE_URL|MIGRATION_DATABASE_URL)=[^\s'\"]+", r"\1=<redacted>", sanitized)
    return sanitized


def verify_multiprocess_concurrency():
    """
    Tests queue concurrency with 2 simultaneous OS processes using SELECT FOR UPDATE SKIP LOCKED.
    Verifies 0 duplicate claims and dynamically captures and tests lease recovery.
    """
    print(f"[8/8] Running multi-process queue concurrency test (2 worker processes)...")

    # 1. Assert queue is currently empty (new database; never deletes pre-existing data)
    engine = create_engine(OPERATOR_URL)
    with engine.begin() as conn:
        initial_count = conn.execute(text("SELECT count(*) FROM jarvis.jarvis_tasks;")).scalar()
        assert initial_count == 0, f"Expected 0 initial tasks in clean staging database, found {initial_count}!"

        # Seed 20 test tasks
        for i in range(1, 21):
            conn.execute(
                text("""
                    INSERT INTO jarvis.jarvis_tasks (task_type, payload, status, next_run_at)
                    VALUES (:ttype, :payload, 'pending', now())
                """),
                {"ttype": f"concurrent_job_{i}", "payload": json.dumps({"index": i})}
            )
    print("      Seeded 20 pending tasks into jarvis.jarvis_tasks.")

    # 2. Worker child process runner script (secret-safe: zero credentials on disk)
    worker_script_path = os.path.join(RUN_DATA_DIR, "worker_runner.py")
    p1 = None
    p2 = None
    out1, err1 = "", ""
    out2, err2 = "", ""

    try:
        with open(worker_script_path, "w", encoding="utf-8") as f:
            f.write(f'''"""
Ephemeral child worker runner for multi-process queue concurrency testing.
Zero credentials stored: receives database URL securely via environment variable.
"""
import os
import sys
import time

sys.path.insert(0, r"{BASE_DIR}")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.services.jarvis_queue import JarvisQueueManager
from backend.app.models.jarvis import JarvisTask

worker_id = sys.argv[1]
db_url = os.environ.get("JARVIS_OPERATIONAL_DATABASE_URL")
if not db_url:
    print("ERROR: JARVIS_OPERATIONAL_DATABASE_URL environment variable missing", file=sys.stderr)
    sys.exit(1)

engine = create_engine(db_url, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

claimed_tasks = []
start = time.time()
while time.time() - start < 15:
    with Session() as session:
        task = JarvisQueueManager.claim_next_task(session, worker_id, lease_seconds=120)
        if task:
            claimed_tasks.append(task.id)
            time.sleep(0.02)
        else:
            time.sleep(0.05)
            with Session() as s2:
                pending = s2.query(JarvisTask).filter(JarvisTask.status == 'pending').count()
                if pending == 0:
                    break

print(f"{{worker_id}} claimed: {{claimed_tasks}}")
''')

        # 3. Launch 2 simultaneous worker processes passing connection URL via child_env
        child_env = os.environ.copy()
        child_env["JARVIS_OPERATIONAL_DATABASE_URL"] = OPERATOR_URL

        p1 = subprocess.Popen(
            [sys.executable, worker_script_path, "worker-node-alpha"],
            env=child_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        p2 = subprocess.Popen(
            [sys.executable, worker_script_path, "worker-node-beta"],
            env=child_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            out1, err1 = p1.communicate(timeout=25)
            out2, err2 = p2.communicate(timeout=25)
        except Exception:
            # Explicit cleanup of only these two child processes if communication fails or times out
            for proc in (p1, p2):
                if proc is not None and proc.poll() is None:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
            for proc in (p1, p2):
                if proc is not None and proc.poll() is None:
                    try:
                        proc.wait(timeout=5)
                    except Exception:
                        try:
                            proc.kill()
                            proc.wait(timeout=5)
                        except Exception:
                            pass
            raise

    finally:
        # Guarantee both exact child processes are fully terminated and reaped
        # before attempting to clean up worker_runner.py on disk
        for proc in (p1, p2):
            if proc is not None and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
        for proc in (p1, p2):
            if proc is not None and proc.poll() is None:
                try:
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                        proc.wait(timeout=5)
                    except Exception:
                        pass

        # Cleanup worker_runner.py strictly after child processes have exited
        if os.path.exists(worker_script_path):
            try:
                os.remove(worker_script_path)
            except Exception:
                pass

    # Sanitize stderr before formatting into exception messages
    sanitized_err1 = sanitize_diagnostic_output(err1).strip()
    sanitized_err2 = sanitize_diagnostic_output(err2).strip()

    if p1.returncode != 0:
        raise RuntimeError(f"worker-node-alpha failed with exit code {p1.returncode}: {sanitized_err1}")
    if p2.returncode != 0:
        raise RuntimeError(f"worker-node-beta failed with exit code {p2.returncode}: {sanitized_err2}")

    print(f"      {out1.strip()}")
    print(f"      {out2.strip()}")

    # 4. Verify results
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, status, locked_by, claim_token FROM jarvis.jarvis_tasks;")).fetchall()

    claimed_by_alpha = [r for r in rows if r.locked_by == "worker-node-alpha"]
    claimed_by_beta = [r for r in rows if r.locked_by == "worker-node-beta"]
    all_tokens = [r.claim_token for r in rows if r.claim_token is not None]

    total_tasks = len(rows)
    total_claimed = len(claimed_by_alpha) + len(claimed_by_beta)
    unique_tokens = len(set(all_tokens))

    print(f"      Concurrency Results: Total={total_tasks}, Alpha={len(claimed_by_alpha)}, Beta={len(claimed_by_beta)}")
    print(f"      Unique Claim Tokens: {unique_tokens} / {total_tasks}")

    assert total_tasks == 20, f"Expected 20 tasks, got {total_tasks}"
    assert total_claimed == 20, f"Expected 20 claimed tasks, got {total_claimed}"
    assert unique_tokens == 20, f"Duplicate claim token detected! Tokens: {len(all_tokens)}, Unique: {unique_tokens}"
    assert len(claimed_by_alpha) > 0, "Worker Alpha claimed 0 tasks!"
    assert len(claimed_by_beta) > 0, "Worker Beta claimed 0 tasks!"
    print("      PASS: Exactly 0 duplicate claims under high multi-process contention.")

    # 5. Lease expiration and recovery verification (dynamic ID without hardcoding)
    print("      Verifying lease expiration and recovery...")
    # Dynamically select the first claimed task from Worker Alpha
    target_task = claimed_by_alpha[0]
    target_task_id = target_task.id
    original_token = target_task.claim_token
    print(f"      Selected task #{target_task_id} (locked by {target_task.locked_by}) for lease expiration recovery.")

    with engine.begin() as conn:
        past_time = datetime.now(timezone.utc) - timedelta(seconds=600)
        conn.execute(
            text("""
                UPDATE jarvis.jarvis_tasks 
                SET lease_expires_at = :past, status = 'claimed', locked_by = 'crashed-worker'
                WHERE id = :target_id;
            """),
            {"past": past_time, "target_id": target_task_id}
        )

    Session = sessionmaker(bind=engine)
    with Session() as session:
        from backend.app.services.jarvis_queue import JarvisQueueManager
        from backend.app.models.jarvis import JarvisTask

        reclaimed_count = JarvisQueueManager.reap_expired_leases(session)
        assert reclaimed_count == 1, f"Expected exactly 1 reclaimed lease, got {reclaimed_count}"

        # Independently query the seeded task by ID and verify post-recovery state
        recovered_task = session.query(JarvisTask).filter(JarvisTask.id == target_task_id).first()
        assert recovered_task is not None, f"Task #{target_task_id} not found in database!"
        assert recovered_task.status == "pending", f"Expected status 'pending', got '{recovered_task.status}'"
        assert recovered_task.locked_by is None, f"Expected locked_by is None, got '{recovered_task.locked_by}'"
        assert recovered_task.claim_token is None, f"Expected claim_token is None, got '{recovered_task.claim_token}'"
        assert recovered_task.lease_expires_at is None, f"Expected lease_expires_at is None, got '{recovered_task.lease_expires_at}'"
        assert recovered_task.locked_at is None, f"Expected locked_at is None, got '{recovered_task.locked_at}'"

        # Worker beta claims the recovered task
        recovered_claim = JarvisQueueManager.claim_next_task(session, "worker-node-beta", lease_seconds=120)
        assert recovered_claim is not None and recovered_claim.id == target_task_id
        assert recovered_claim.locked_by == "worker-node-beta"
        assert recovered_claim.claim_token != original_token
        print(f"      PASS: Exactly task #{target_task_id} recovered to pending and re-claimed with new token.")


def main():
    print("================================================================================")
    print("LeadVoix Business JARVIS — Step 5: Real PostgreSQL 18 Staging Verification")
    print(f"Run ID: {RUN_ID}")
    print("================================================================================")
    check_environment_and_port_safety()
    init_fresh_cluster()
    proc, server_log_handle = start_verified_postgres()
    try:
        create_unique_staging_database()
        run_migrations_and_ddl()
        verify_least_privilege_permissions()
        verify_audit_log_protections_distinguished()
        verify_multiprocess_concurrency()
        print("================================================================================")
        print("Step 5 PostgreSQL 18 Staging Verification: ALL CHECKS PASSED (100% SUCCESS)")
        print(f"Evidence Preserved at: {RUN_DATA_DIR}")
        print(f"Staging Database Name: {STAGING_DB_NAME} (Port {STAGING_PORT})")
        print("================================================================================")
    finally:
        stop_verified_postgres(proc, server_log_handle)


if __name__ == "__main__":
    main()
