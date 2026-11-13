"""
LeadVoix Business JARVIS — Phase B Orchestration Test Suite
Covers:
- Database isolation & customer data write protection (CustomerDataWriteViolationError)
- Persistent task queue & atomic claiming (SELECT FOR UPDATE SKIP LOCKED)
- Concurrent worker collision avoidance
- Lease expiration, heartbeat, and crash recovery (reap_expired_leases)
- Exponential backoff & dead-letter queue (DLQ) transitions
- Telegram two-phase persistent dispatch reservation (in_flight -> completed/failed)
- Telegram crash-window recovery disambiguation
- Founder approvals: HMAC-SHA256 signature, expiration, and replay protection
- Immutable operational audit logging
- Worker lifecycle, graceful shutdown, and emergency kill switch
"""

from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.db.database import (
    Base,
    get_context_configure_kwargs,
    get_migration_database_url,
)
from backend.app.models.jarvis import (
    JarvisApprovalRecord,
    JarvisAuditLog,
    JarvisDispatchIdempotency,
    JarvisTask,
    JarvisTaskAttempt,
)
from backend.app.api.jarvis import get_jarvis_health
from backend.app.models.lead import Lead
from backend.app.services.jarvis_approvals import JarvisApprovalManager
from backend.app.services.jarvis_audit import (
    evaluate_worker_health,
    get_latest_worker_heartbeat,
    record_audit_event,
    record_worker_heartbeat,
    record_worker_lifecycle,
)
from backend.app.services.jarvis_collector import (
    CustomerDataWriteViolationError,
    InvalidTimezoneConfigurationError,
    ReadOnlyWriteAttemptError,
    apply_operational_guards,
    apply_read_only_guards,
    calculate_digest_window,
    get_jarvis_operational_database_url,
    get_jarvis_timezone,
    get_operational_sessionmaker,
    is_operational_db_required,
    reset_operational_engine,
)
from backend.app.services.jarvis_digest import (
    check_or_reserve_db_dispatch,
    finalize_db_dispatch,
    generate_and_dispatch_digest,
)
from backend.app.services.jarvis_queue import JarvisQueueManager
from backend.app.workers.jarvis_worker import JarvisOrchestratorWorker, is_kill_switch_active


class JarvisPhaseBOrchestrationTests(unittest.TestCase):
    def setUp(self):
        # Create an isolated in-memory SQLite engine simulating PostgreSQL schema 'jarvis'
        self.engine = create_engine(
            "sqlite:///:memory:",
            execution_options={"schema_translate_map": {"jarvis": None}},
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        self.patcher_env = patch.dict(os.environ, {
            "ENABLE_JARVIS": "true",
            "JARVIS_INTERNAL_ORG_ID": "1",
            "JARVIS_KILL_SWITCH": "false",
            "SECRET_KEY": "test-super-secret-key-for-approvals",
        }, clear=False)
        self.patcher_env.start()

    def tearDown(self):
        self.patcher_env.stop()
        self.engine.dispose()

    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    # --- 1. Database Isolation & Customer Data Write Protection ---

    def test_operational_session_blocks_writes_to_customer_saas_data(self):
        """Operational session permits jarvis.* writes but strictly blocks modifications on customer SaaS tables."""
        session = self.SessionLocal()
        apply_operational_guards(session)

        # 1. Writing to jarvis tables must succeed
        task = JarvisTask(task_type="test", status="pending", payload={})
        session.add(task)
        session.commit()
        self.assertIsNotNone(task.id)

        # 2. Writing to customer SaaS table via ORM must raise CustomerDataWriteViolationError
        customer_lead = Lead(
            organization_id=1,
            first_name="Customer",
            last_name="Prospect",
            phone="+1234567890",
            status="NEW",
        )
        with self.assertRaises(CustomerDataWriteViolationError):
            session.add(customer_lead)

        # 3. Direct SQL write touching customer SaaS table must be blocked
        with self.assertRaises(CustomerDataWriteViolationError):
            session.execute(text("INSERT INTO leads (first_name) VALUES ('Hacked');"))

        with self.assertRaises(CustomerDataWriteViolationError):
            session.execute(text("UPDATE agent_calls SET status = 'deleted';"))

        with self.assertRaises(CustomerDataWriteViolationError):
            session.execute(text("DELETE FROM organizations WHERE id = 1;"))

        session.close()

    # --- 2. Persistent Task Queue & Atomic Claiming ---

    def test_task_enqueue_and_atomic_claim(self):
        """Tasks are enqueued as pending and atomically claimed with claim token and lease."""
        with self.get_session() as session:
            task = JarvisQueueManager.enqueue_task(
                session,
                task_type="digest_morning",
                payload={"date": "2026-11-10"},
                organization_id=1,
            )
            self.assertEqual(task.status, "pending")
            self.assertEqual(task.attempts, 0)

            # Claim task with worker-1
            claimed = JarvisQueueManager.claim_next_task(session, worker_id="worker-1", lease_seconds=120)
            self.assertIsNotNone(claimed)
            self.assertEqual(claimed.id, task.id)
            self.assertEqual(claimed.status, "claimed")
            self.assertEqual(claimed.locked_by, "worker-1")
            self.assertEqual(claimed.attempts, 1)
            self.assertIsNotNone(claimed.claim_token)
            self.assertIsNotNone(claimed.lease_expires_at)

    def test_concurrent_worker_collision_avoidance(self):
        """When Worker 1 claims a task, Worker 2 must NOT be able to claim the same task."""
        with self.get_session() as session1:
            with self.get_session() as session2:
                task = JarvisQueueManager.enqueue_task(
                    session1,
                    task_type="digest_morning",
                    payload={"date": "2026-11-10"},
                )

                # Worker 1 claims task
                claimed1 = JarvisQueueManager.claim_next_task(session1, worker_id="worker-1")
                self.assertIsNotNone(claimed1)

                # Worker 2 attempts to claim next task -> must receive None
                claimed2 = JarvisQueueManager.claim_next_task(session2, worker_id="worker-2")
                self.assertIsNone(claimed2)

    # --- 3. Lease Expiration, Heartbeat, and Restart Recovery ---

    def test_lease_renewal_heartbeat(self):
        """Heartbeat successfully extends lease_expires_at."""
        with self.get_session() as session:
            task = JarvisQueueManager.enqueue_task(session, task_type="long_task", payload={})
            claimed = JarvisQueueManager.claim_next_task(session, worker_id="worker-1", lease_seconds=60)
            initial_lease = claimed.lease_expires_at

            pytime_now = datetime.now(timezone.utc)
            success = JarvisQueueManager.renew_lease(
                session,
                claimed.id,
                claimed.claim_token,
                extension_seconds=300,
            )
            self.assertTrue(success)
            session.refresh(claimed)
            self.assertGreater(claimed.lease_expires_at, initial_lease)

    def test_reap_expired_leases_and_restart_recovery(self):
        """Expired task leases are safely reclaimed to pending for retry."""
        with self.get_session() as session:
            task = JarvisQueueManager.enqueue_task(session, task_type="abandoned_task", payload={})
            claimed = JarvisQueueManager.claim_next_task(session, worker_id="crashed-worker", lease_seconds=10)

            # Simulate passage of time where lease expired in the past
            expired_time = datetime.now(timezone.utc) - timedelta(seconds=30)
            claimed.lease_expires_at = expired_time
            session.commit()

            # Reaping reclaims the task
            reaped_count = JarvisQueueManager.reap_expired_leases(session, now=datetime.now(timezone.utc))
            self.assertEqual(reaped_count, 1)

            session.refresh(task)
            self.assertEqual(task.status, "pending")
            self.assertIsNone(task.claim_token)
            self.assertIsNone(task.locked_by)
            self.assertIn("Lease expired", task.last_error)

            # Another worker can now claim it
            reclaimed = JarvisQueueManager.claim_next_task(session, worker_id="recovered-worker")
            self.assertIsNotNone(reclaimed)
            self.assertEqual(reclaimed.id, task.id)
            self.assertEqual(reclaimed.attempts, 2)

    # --- 4. Exponential Backoff and Dead-Letter Queue (DLQ) ---

    def test_retry_exponential_backoff_and_dead_letter(self):
        """Failed tasks back off exponentially and move to dead_letter upon exhausting max_attempts."""
        with self.get_session() as session:
            task = JarvisQueueManager.enqueue_task(session, task_type="flaky_task", payload={}, max_attempts=3)

            # Attempt 1: fails
            claimed1 = JarvisQueueManager.claim_next_task(session, worker_id="w1")
            token1 = claimed1.claim_token
            JarvisQueueManager.fail_task(session, claimed1.id, token1, "Failure 1", base_backoff_seconds=10)
            session.refresh(task)
            self.assertEqual(task.status, "pending")
            # Backoff for attempt 1: 10 * 2^(1-1) = 10s
            expected_min = datetime.now(timezone.utc) + timedelta(seconds=8)
            next_run = task.next_run_at
            if next_run.tzinfo is None:
                next_run = next_run.replace(tzinfo=timezone.utc)
            self.assertGreaterEqual(next_run, expected_min)

            # Simulate time passed so it becomes eligible again
            task.next_run_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            session.commit()

            # Attempt 2: fails
            claimed2 = JarvisQueueManager.claim_next_task(session, worker_id="w1")
            token2 = claimed2.claim_token
            JarvisQueueManager.fail_task(session, claimed2.id, token2, "Failure 2", base_backoff_seconds=10)
            session.refresh(task)
            self.assertEqual(task.status, "pending")
            self.assertEqual(task.attempts, 2)

            task.next_run_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            session.commit()

            # Attempt 3: fails -> must transition to dead_letter
            claimed3 = JarvisQueueManager.claim_next_task(session, worker_id="w1")
            token3 = claimed3.claim_token
            JarvisQueueManager.fail_task(session, claimed3.id, token3, "Fatal Error", base_backoff_seconds=10)
            session.refresh(task)
            self.assertEqual(task.status, "dead_letter")
            self.assertEqual(task.attempts, 3)
            self.assertIn("Fatal Error", task.last_error)

    # --- 5. Telegram Two-Phase Dispatch Reservation & Crash Recovery ---

    def test_telegram_two_phase_reservation_lifecycle(self):
        """Tests in_flight reservation -> completed transition in database."""
        with self.get_session() as session:
            key = "1:morning:2026-11-10"
            today = date(2026, 11, 10)

            # 1. Phase 1: Reserve in DB
            allowed, status, _, is_crash = check_or_reserve_db_dispatch(
                session, key, org_id=1, digest_type="morning", window_date=today
            )
            self.assertTrue(allowed)
            self.assertEqual(status, "in_flight")
            self.assertFalse(is_crash)

            # Verify in-flight record exists
            rec = session.query(JarvisDispatchIdempotency).filter_by(idempotency_key=key).first()
            self.assertIsNotNone(rec)
            self.assertEqual(rec.status, "in_flight")

            # 2. Duplicate concurrent attempt while in_flight is active is blocked
            allowed2, status2, _, _ = check_or_reserve_db_dispatch(
                session, key, org_id=1, digest_type="morning", window_date=today
            )
            self.assertFalse(allowed2)
            self.assertEqual(status2, "in_flight_active")

            # 3. Phase 2: Confirm delivery outcome
            finalize_db_dispatch(session, key, success=True, telegram_result={"message_id": 888})
            session.refresh(rec)
            self.assertEqual(rec.status, "completed")
            self.assertEqual(rec.telegram_message_id, 888)

            # 4. Subsequent attempt is blocked as already_dispatched
            allowed3, status3, _, _ = check_or_reserve_db_dispatch(
                session, key, org_id=1, digest_type="morning", window_date=today
            )
            self.assertFalse(allowed3)
            self.assertEqual(status3, "already_dispatched")

    def test_telegram_crash_window_recovery_detection(self):
        """When an in_flight reservation has an expired lease (crash scenario), crash_window_recovery is triggered."""
        with self.get_session() as session:
            key = "1:evening:2026-11-10"
            today = date(2026, 11, 10)

            # Simulate worker reserved in_flight and then crashed
            expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            crashed_rec = JarvisDispatchIdempotency(
                organization_id=1,
                digest_type="evening",
                window_date=today,
                idempotency_key=key,
                status="in_flight",
                lease_expires_at=expired_time,
            )
            session.add(crashed_rec)
            session.commit()

            # Recovering worker checks reservation
            allowed, status, details, is_crash = check_or_reserve_db_dispatch(
                session, key, org_id=1, digest_type="evening", window_date=today
            )
            self.assertTrue(allowed)
            self.assertEqual(status, "crash_window_recovery")
            self.assertTrue(is_crash)

    # --- 6. Founder Approvals Gateway ---

    def test_approval_creation_and_signature_validation(self):
        """Approval requests require valid cryptographically signed HMAC token."""
        with self.get_session() as session:
            record, raw_token = JarvisApprovalManager.create_request(
                session,
                action_type="bulk_outreach",
                payload_preview={"recipient_count": 50},
                risk_tier="critical",
                ttl_hours=12,
            )
            self.assertEqual(record.status, "pending")
            self.assertEqual(record.risk_tier, "critical")

            # 1. Invalid token signature must fail
            res_bad = JarvisApprovalManager.resolve_request(
                session,
                record_id=record.id,
                token="forged-fake-token",
                decision="approved",
                responded_by="attacker",
            )
            self.assertFalse(res_bad["success"])
            self.assertEqual(res_bad["reason"], "invalid_signature")

            # 2. Valid token signature succeeds
            res_ok = JarvisApprovalManager.resolve_request(
                session,
                record_id=record.id,
                token=raw_token,
                decision="approved",
                responded_by="founder@leadvoix.com",
            )
            self.assertTrue(res_ok["success"])
            self.assertEqual(res_ok["status"], "approved")

            # 3. Replay protection: subsequent attempt must be rejected
            res_replay = JarvisApprovalManager.resolve_request(
                session,
                record_id=record.id,
                token=raw_token,
                decision="approved",
                responded_by="replay_attacker",
            )
            self.assertFalse(res_replay["success"])
            self.assertEqual(res_replay["reason"], "already_resolved")

    def test_approval_expiration(self):
        """Expired approval requests are blocked from execution."""
        with self.get_session() as session:
            record, raw_token = JarvisApprovalManager.create_request(
                session,
                action_type="deploy_prompt",
                payload_preview={},
                ttl_hours=1,
            )
            # Expire record manually
            record.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
            session.commit()

            res = JarvisApprovalManager.resolve_request(
                session,
                record_id=record.id,
                token=raw_token,
                decision="approved",
                responded_by="founder",
            )
            self.assertFalse(res["success"])
            self.assertEqual(res["reason"], "expired")

    # --- 7. Immutable Operational Audit Logging ---

    def test_append_only_audit_log_recording(self):
        """Audit events are appended with timestamp and actor."""
        with self.get_session() as session:
            entry = record_audit_event(
                session,
                event_type="DISPATCH_COMPLETED",
                details={"digest_type": "morning", "telegram_id": 999},
                actor="jarvis-worker-node-1",
            )
            self.assertIsNotNone(entry.id)
            self.assertEqual(entry.event_type, "DISPATCH_COMPLETED")
            self.assertEqual(entry.actor, "jarvis-worker-node-1")
            self.assertEqual(entry.details["telegram_id"], 999)

    # --- 8. Worker Lifecycle, Kill Switch, and Shutdown ---

    def test_emergency_kill_switch_active_detection(self):
        """Worker respects JARVIS_KILL_SWITCH=true and ENABLE_JARVIS=false."""
        with patch.dict(os.environ, {"JARVIS_KILL_SWITCH": "true"}):
            self.assertTrue(is_kill_switch_active())
        with patch.dict(os.environ, {"JARVIS_KILL_SWITCH": "false", "ENABLE_JARVIS": "false"}):
            self.assertTrue(is_kill_switch_active())
        with patch.dict(os.environ, {"JARVIS_KILL_SWITCH": "false", "ENABLE_JARVIS": "true"}):
            self.assertFalse(is_kill_switch_active())

    def test_worker_run_cycle_and_graceful_shutdown(self):
        """Worker completes tasks and stops cleanly upon stop() event."""
        @contextmanager
        def mock_db_factory():
            session = self.SessionLocal()
            try:
                yield session
            finally:
                session.close()

        # Enqueue health check task
        with self.get_session() as session:
            JarvisQueueManager.enqueue_task(session, task_type="health_check", payload={})

        worker = JarvisOrchestratorWorker(
            worker_id="test-worker-unit",
            poll_interval=0.1,
            max_cycles=1,
            db_factory=mock_db_factory,
        )

        cycle_res = worker.run_cycle()
        self.assertEqual(cycle_res["outcome"], "completed")
        self.assertEqual(cycle_res["tasks_processed"], 1)

        health = worker.get_health()
        self.assertEqual(health["worker_id"], "test-worker-unit")
        self.assertEqual(health["tasks_processed"], 1)

        worker.stop()
        self.assertTrue(worker.stop_event.is_set())

    # --- 9. Phase B Security Remediation Tests ---

    def test_ddl_script_least_privilege_and_no_create_for_runtime_role(self):
        """Verify that the DDL script adheres to least-privilege security model."""
        sql_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "jarvis_phase_b_roles_and_schema.sql")
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read().upper()
        self.assertIn("LEADVOIX_MIGRATOR", sql_content)
        self.assertIn("ALTER SCHEMA JARVIS OWNER TO LEADVOIX_MIGRATOR", sql_content)
        self.assertIn("GRANT USAGE ON SCHEMA JARVIS TO JARVIS_OPERATOR", sql_content)
        self.assertIn("REVOKE CREATE ON SCHEMA JARVIS FROM JARVIS_OPERATOR", sql_content)
        self.assertNotIn("GRANT USAGE, CREATE ON SCHEMA JARVIS TO JARVIS_OPERATOR", sql_content)
        self.assertIn("REVOKE ALL ON SCHEMA PUBLIC FROM JARVIS_OPERATOR", sql_content)
        self.assertIn("REVOKE ALL ON ALL TABLES IN SCHEMA PUBLIC FROM JARVIS_OPERATOR", sql_content)
        self.assertIn("REVOKE ALL ON SCHEMA JARVIS FROM PUBLIC", sql_content)

    def test_migrator_role_attributes_enforce_no_createdb_no_superuser(self):
        """Verify leadvoix_migrator is strictly NOCREATEDB, NOSUPERUSER, NOCREATEROLE in both CREATE and ALTER branches."""
        sql_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "jarvis_phase_b_roles_and_schema.sql")
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read().upper()
        self.assertNotIn("CREATEDB NOINHERIT", sql_content)
        self.assertIn("CREATE ROLE LEADVOIX_MIGRATOR WITH LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE", sql_content)
        self.assertIn("ALTER ROLE LEADVOIX_MIGRATOR WITH LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE", sql_content)

    def test_customer_data_isolation_and_column_level_reader_grants(self):
        """Verify strict isolation: operator/migrator denied SaaS access, reader granted minimal columns only."""
        sql_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "jarvis_phase_b_roles_and_schema.sql")
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read().upper()

        # 1. jarvis_operator has ZERO access to public schema or customer SaaS tables
        self.assertIn("REVOKE ALL ON SCHEMA PUBLIC FROM JARVIS_OPERATOR", sql_content)
        self.assertIn("REVOKE ALL ON ALL TABLES IN SCHEMA PUBLIC FROM JARVIS_OPERATOR", sql_content)
        self.assertNotIn("GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO JARVIS_OPERATOR", sql_content)

        # 2. leadvoix_migrator has ZERO access to customer SaaS tables
        self.assertIn("REVOKE ALL ON ALL TABLES IN SCHEMA PUBLIC FROM LEADVOIX_MIGRATOR", sql_content)
        self.assertNotIn("GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO LEADVOIX_MIGRATOR", sql_content)

        # 3. Column-level least privilege on the 6 collector tables for jarvis_business_reader
        self.assertIn("GRANT SELECT (ID, NAME, SLUG, PLAN) ON TABLE PUBLIC.ORGANIZATIONS TO JARVIS_BUSINESS_READER", sql_content)
        self.assertIn("GRANT SELECT (ID, ORGANIZATION_ID, STATUS, SOURCE, CREATED_AT) ON TABLE PUBLIC.LEADS TO JARVIS_BUSINESS_READER", sql_content)
        self.assertIn("GRANT SELECT (ID, ORGANIZATION_ID, DURATION, STATUS, DIRECTION, CREATED_AT) ON TABLE PUBLIC.AGENT_CALLS TO JARVIS_BUSINESS_READER", sql_content)
        self.assertIn("GRANT SELECT (ID, ORGANIZATION_ID, STATUS, AMOUNT, CREATED_AT) ON TABLE PUBLIC.DEALS TO JARVIS_BUSINESS_READER", sql_content)
        self.assertIn("GRANT SELECT (ID, ORGANIZATION_ID, STATUS, CREATED_AT) ON TABLE PUBLIC.TASKS TO JARVIS_BUSINESS_READER", sql_content)
        self.assertIn("GRANT SELECT (ID, STATUS, AGENT_CALL_ID, CREATED_AT) ON TABLE PUBLIC.CALL_PROCESSING_JOBS TO JARVIS_BUSINESS_READER", sql_content)

        # 4. Sensitive tables must NEVER be granted to reader, operator, or migrator
        for sensitive_table in ["USERS", "AGENT_CALL_TRANSCRIPTS", "AGENT_CALL_SUMMARIES", "AGENT_CALL_INTELLIGENCE", "AGENT_KNOWLEDGE", "SUBSCRIPTIONS"]:
            self.assertNotIn(f"TO JARVIS_BUSINESS_READER;\nGRANT SELECT ON TABLE PUBLIC.{sensitive_table}", sql_content)
            self.assertNotIn(f"GRANT SELECT ON TABLE PUBLIC.{sensitive_table}", sql_content)

    def test_alembic_base_revision_precondition_check(self):
        """Verify DDL script verifies public.alembic_version exists and asserts base revision 3c8d1e2f4a5b."""
        sql_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "jarvis_phase_b_roles_and_schema.sql")
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read().upper()
        self.assertIn("3C8D1E2F4A5B", sql_content)
        self.assertIn("PUBLIC.ALEMBIC_VERSION DOES NOT EXIST", sql_content)
        self.assertIn("EXPECTED BASE REVISION 3C8D1E2F4A5B", sql_content)

    def test_operational_database_url_fails_closed_in_production(self):
        """Operational database connection fails closed in production when unconfigured."""
        reset_operational_engine()
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "JARVIS_OPERATIONAL_DATABASE_URL": ""}):
            self.assertTrue(is_operational_db_required())
            with self.assertRaises(RuntimeError) as ctx:
                get_jarvis_operational_database_url()
            self.assertIn("Security violation: JARVIS_OPERATIONAL_DATABASE_URL is mandatory", str(ctx.exception))

    def test_operational_database_url_accepts_configured_credentials(self):
        """Operational database connection returns configured URL when provided."""
        reset_operational_engine()
        test_url = "postgresql://jarvis_operator:secret@db:5432/postgres"
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "JARVIS_OPERATIONAL_DATABASE_URL": test_url}):
            self.assertEqual(get_jarvis_operational_database_url(), test_url)

    def test_operational_engine_no_autocommit_and_bounded_pool(self):
        """Operational engine does not use AUTOCOMMIT and configures bounded connection pool."""
        reset_operational_engine()
        test_url = "postgresql://jarvis_operator:secret@db.internal:5432/leadvoix"
        with patch.dict(os.environ, {"JARVIS_OPERATIONAL_DATABASE_URL": test_url, "REQUIRE_JARVIS_OPERATIONAL": "false"}):
            sm = get_operational_sessionmaker()
            engine = sm.kw["bind"]
            self.assertFalse(sm.kw.get("autocommit", False))
            self.assertNotEqual(engine.get_execution_options().get("isolation_level"), "AUTOCOMMIT")
            self.assertTrue(hasattr(engine, "pool"))
            self.assertEqual(engine.pool.size(), 3)
            self.assertEqual(engine.pool._max_overflow, 2)
            self.assertEqual(engine.pool._timeout, 30)
            self.assertEqual(engine.pool._recycle, 1800)

    def test_duplicate_scheduled_task_prevention(self):
        """Scheduled tasks are deduplicated via unique idempotency_key."""
        with self.get_session() as session:
            key = "digest_morning:1:2026-11-10"
            task1 = JarvisQueueManager.enqueue_task(
                session,
                task_type="digest_morning",
                payload={"date": "2026-11-10"},
                organization_id=1,
                idempotency_key=key,
            )
            self.assertIsNotNone(task1.id)
            task2 = JarvisQueueManager.enqueue_task(
                session,
                task_type="digest_morning",
                payload={"date": "2026-11-10"},
                organization_id=1,
                idempotency_key=key,
            )
            self.assertEqual(task2.id, task1.id)
            total_tasks = session.query(JarvisTask).filter(JarvisTask.idempotency_key == key).count()
            self.assertEqual(total_tasks, 1)

    def test_ddl_database_portability_and_secret_safeguard(self):
        """Verify dynamic database connection, secret placeholder guard, and safe default privileges."""
        sql_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "jarvis_phase_b_roles_and_schema.sql")
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_content = f.read().upper()
        # 1. Database name portability: uses current_database()
        self.assertIn("CURRENT_DATABASE()", sql_content)
        self.assertIn("GRANT CONNECT ON DATABASE %I", sql_content)
        self.assertNotIn("GRANT CONNECT ON DATABASE POSTGRES TO", sql_content)
        # 2. Secret safeguard: placeholder password detection
        self.assertIn("PLACEHOLDER PASSWORDS DETECTED", sql_content)
        self.assertIn("RAISE EXCEPTION", sql_content)
        # 3. Alembic version permissions for leadvoix_migrator
        self.assertIn("ALEMBIC_VERSION", sql_content)
        self.assertIn("GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE PUBLIC.ALEMBIC_VERSION TO LEADVOIX_MIGRATOR", sql_content)
        # 4. Safe Default Privileges: Only SELECT, INSERT for jarvis_operator (never UPDATE or DELETE)
        self.assertIn("ALTER DEFAULT PRIVILEGES FOR ROLE LEADVOIX_MIGRATOR IN SCHEMA JARVIS \n    GRANT SELECT, INSERT ON TABLES TO JARVIS_OPERATOR", sql_content)
        self.assertNotIn("ALTER DEFAULT PRIVILEGES FOR ROLE LEADVOIX_MIGRATOR IN SCHEMA JARVIS \n    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO JARVIS_OPERATOR", sql_content)

    def test_alembic_migration_includes_post_table_hardening(self):
        """Verify that Alembic migration encapsulates table-level hardening and audit immutability."""
        migration_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "alembic", "versions",
            "4f7e2a1b9c3d_create_jarvis_schema_and_operational_tables.py"
        )
        with open(migration_path, "r", encoding="utf-8") as f:
            mig_content = f.read()
        self.assertIn("bind.dialect.name == \"postgresql\"", mig_content)
        self.assertIn("REVOKE UPDATE, DELETE, TRUNCATE ON TABLE jarvis.audit_logs FROM jarvis_operator", mig_content)
        self.assertIn("GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE jarvis.jarvis_tasks TO jarvis_operator", mig_content)

    # --- 10. Timezone & Scheduling Resilience Tests ---

    def test_timezone_configuration_default_and_custom(self):
        """Verify get_jarvis_timezone defaults to Asia/Kolkata and accepts custom IANA timezones."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JARVIS_TIMEZONE", None)
            default_tz = get_jarvis_timezone()
            self.assertEqual(default_tz.key, "Asia/Kolkata")

        with patch.dict(os.environ, {"JARVIS_TIMEZONE": "America/New_York"}):
            ny_tz = get_jarvis_timezone()
            self.assertEqual(ny_tz.key, "America/New_York")

        with patch.dict(os.environ, {"JARVIS_TIMEZONE": "UTC"}):
            utc_tz = get_jarvis_timezone()
            self.assertEqual(utc_tz.key, "UTC")

        # Worker initialization with custom timezone
        worker = JarvisOrchestratorWorker(worker_id="test-tz-worker", timezone_name="Europe/London")
        self.assertEqual(worker.timezone.key, "Europe/London")
        self.assertEqual(worker.get_health()["timezone"], "Europe/London")

    def test_invalid_timezone_configuration_fails_closed(self):
        """Verify invalid timezone configuration raises InvalidTimezoneConfigurationError and fails closed."""
        with patch.dict(os.environ, {"JARVIS_TIMEZONE": "Mars/Base_Alpha"}):
            with self.assertRaises(InvalidTimezoneConfigurationError) as ctx:
                get_jarvis_timezone()
            self.assertIn("Invalid JARVIS_TIMEZONE configuration", str(ctx.exception))

        with self.assertRaises(InvalidTimezoneConfigurationError):
            JarvisOrchestratorWorker(worker_id="bad-tz-worker", timezone_name="Invalid/Not_Real_TZ")

    def test_scheduled_briefing_timing_windows(self):
        """Verify briefings are enqueued at scheduled times (08:00 morning, 21:00 evening)."""
        tz = ZoneInfo("Asia/Kolkata")
        worker = JarvisOrchestratorWorker(worker_id="test-sched-worker", timezone_name="Asia/Kolkata")

        with self.get_session() as session:
            # 1. At 07:59 IST: before morning window -> 0 tasks enqueued
            t_0759 = datetime(2026, 11, 10, 7, 59, 0, tzinfo=tz)
            enqueued = worker.check_and_enqueue_scheduled_briefings(session, ref_now=t_0759)
            self.assertEqual(enqueued, [])
            self.assertEqual(session.query(JarvisTask).count(), 0)

            # 2. At 08:00 IST: morning window reached -> morning briefing enqueued
            t_0800 = datetime(2026, 11, 10, 8, 0, 0, tzinfo=tz)
            enqueued = worker.check_and_enqueue_scheduled_briefings(session, ref_now=t_0800)
            self.assertEqual(enqueued, ["digest_morning"])
            self.assertEqual(session.query(JarvisTask).count(), 1)

            # 3. At 08:05 IST: already enqueued for today -> 0 additional tasks
            t_0805 = datetime(2026, 11, 10, 8, 5, 0, tzinfo=tz)
            enqueued = worker.check_and_enqueue_scheduled_briefings(session, ref_now=t_0805)
            self.assertEqual(enqueued, [])
            self.assertEqual(session.query(JarvisTask).count(), 1)

            # 4. At 20:59 IST: before evening window -> evening not yet due
            t_2059 = datetime(2026, 11, 10, 20, 59, 0, tzinfo=tz)
            enqueued = worker.check_and_enqueue_scheduled_briefings(session, ref_now=t_2059)
            self.assertEqual(enqueued, [])
            self.assertEqual(session.query(JarvisTask).count(), 1)

            # 5. At 21:00 IST: evening window reached -> evening briefing enqueued
            t_2100 = datetime(2026, 11, 10, 21, 0, 0, tzinfo=tz)
            enqueued = worker.check_and_enqueue_scheduled_briefings(session, ref_now=t_2100)
            self.assertEqual(enqueued, ["digest_evening"])
            self.assertEqual(session.query(JarvisTask).count(), 2)

    def test_idempotent_catch_up_missed_morning_window(self):
        """Worker offline during 08:00-08:15 catches up today's morning briefing upon later startup."""
        tz = ZoneInfo("Asia/Kolkata")
        worker = JarvisOrchestratorWorker(worker_id="test-catchup-worker", timezone_name="Asia/Kolkata")

        with self.get_session() as session:
            # Worker starts at 10:30 IST (well after 08:00-08:15 window)
            t_1030 = datetime(2026, 11, 10, 10, 30, 0, tzinfo=tz)
            enqueued = worker.check_and_enqueue_scheduled_briefings(session, ref_now=t_1030)
            self.assertEqual(enqueued, ["digest_morning"])

            task = session.query(JarvisTask).filter_by(idempotency_key="digest_morning:1:2026-11-10").first()
            self.assertIsNotNone(task)
            self.assertEqual(task.status, "pending")
            self.assertEqual(task.payload.get("digest_type"), "morning")
            self.assertEqual(task.payload.get("date"), "2026-11-10")

    def test_idempotent_catch_up_missed_evening_window(self):
        """Worker starting late at night catches up both morning and evening briefings if unqueued."""
        tz = ZoneInfo("Asia/Kolkata")
        worker = JarvisOrchestratorWorker(worker_id="test-late-worker", timezone_name="Asia/Kolkata")

        with self.get_session() as session:
            # Worker starts at 22:30 IST (after both 08:00 and 21:00)
            t_2230 = datetime(2026, 11, 10, 22, 30, 0, tzinfo=tz)
            enqueued = worker.check_and_enqueue_scheduled_briefings(session, ref_now=t_2230)
            self.assertIn("digest_morning", enqueued)
            self.assertIn("digest_evening", enqueued)
            self.assertEqual(session.query(JarvisTask).count(), 2)

    def test_worker_reboot_duplicate_prevention(self):
        """Worker reboot on same day preserves existing tasks and creates zero duplicates."""
        tz = ZoneInfo("Asia/Kolkata")
        worker1 = JarvisOrchestratorWorker(worker_id="worker-node-1", timezone_name="Asia/Kolkata")

        with self.get_session() as session:
            # Worker 1 runs at 08:00
            t_0800 = datetime(2026, 11, 10, 8, 0, 0, tzinfo=tz)
            worker1.check_and_enqueue_scheduled_briefings(session, ref_now=t_0800)

            # Task is claimed and completed
            task = JarvisQueueManager.claim_next_task(session, worker_id="worker-node-1")
            self.assertIsNotNone(task)
            JarvisQueueManager.complete_task(session, task.id, task.claim_token)

            # Worker 1 crashes. Worker 2 starts fresh at 14:00 (cold cache)
            worker2 = JarvisOrchestratorWorker(worker_id="worker-node-2", timezone_name="Asia/Kolkata")
            t_1400 = datetime(2026, 11, 10, 14, 0, 0, tzinfo=tz)
            enqueued = worker2.check_and_enqueue_scheduled_briefings(session, ref_now=t_1400)
            self.assertEqual(enqueued, [])

            # Must still have only 1 task for the morning briefing
            morning_tasks = session.query(JarvisTask).filter(
                JarvisTask.idempotency_key == "digest_morning:1:2026-11-10"
            ).all()
            self.assertEqual(len(morning_tasks), 1)
            self.assertEqual(morning_tasks[0].status, "completed")

    def test_concurrent_worker_scheduled_task_deduplication(self):
        """Two concurrent workers simultaneously checking scheduled tasks produce exactly 1 task."""
        tz = ZoneInfo("Asia/Kolkata")
        worker_a = JarvisOrchestratorWorker(worker_id="worker-a", timezone_name="Asia/Kolkata")
        worker_b = JarvisOrchestratorWorker(worker_id="worker-b", timezone_name="Asia/Kolkata")

        with self.get_session() as session:
            t_0800 = datetime(2026, 11, 10, 8, 0, 0, tzinfo=tz)
            worker_a.check_and_enqueue_scheduled_briefings(session, ref_now=t_0800)
            worker_b.check_and_enqueue_scheduled_briefings(session, ref_now=t_0800)

            total_tasks = session.query(JarvisTask).filter_by(idempotency_key="digest_morning:1:2026-11-10").count()
            self.assertEqual(total_tasks, 1)

    def test_calculate_digest_window_with_custom_timezone(self):
        """calculate_digest_window accurately calculates boundaries for non-IST timezones."""
        ny_tz = ZoneInfo("America/New_York")
        ref_date = date(2026, 11, 10)
        start_utc, end_utc, label = calculate_digest_window("morning", target_date=ref_date, tz=ny_tz)

        start_ny = start_utc.astimezone(ny_tz)
        end_ny = end_utc.astimezone(ny_tz)

        # Previous day in America/New_York (Nov 9)
        self.assertEqual(start_ny.date(), date(2026, 11, 9))
        self.assertEqual(start_ny.time(), time.min)
        self.assertEqual(end_ny.date(), date(2026, 11, 9))
        self.assertIn("Morning Briefing", label)

    # --- 11. Worker Heartbeat & Health Monitoring Tests ---

    def test_heartbeat_persistence_in_audit_logs(self):
        """Worker periodically persists heartbeat to jarvis.audit_logs."""
        @contextmanager
        def mock_db_factory():
            session = self.SessionLocal()
            try:
                yield session
            finally:
                session.close()

        worker = JarvisOrchestratorWorker(
            worker_id="worker-hb-unit-1",
            poll_interval=0.1,
            heartbeat_interval=0.01,
            max_cycles=1,
            db_factory=mock_db_factory,
        )
        worker.run_cycle()

        with self.get_session() as session:
            hb = session.query(JarvisAuditLog).filter_by(
                actor="worker-hb-unit-1",
                event_type="WORKER_HEARTBEAT",
            ).first()
            self.assertIsNotNone(hb)
            self.assertEqual(hb.actor, "worker-hb-unit-1")
            self.assertEqual(hb.details.get("status"), "running")
            self.assertIn("uptime_seconds", hb.details)
            self.assertIsNotNone(hb.created_at)

    def test_worker_lifecycle_startup_and_graceful_shutdown(self):
        """Worker records WORKER_STARTED, WORKER_HEARTBEAT, and WORKER_STOPPED events."""
        @contextmanager
        def mock_db_factory():
            session = self.SessionLocal()
            try:
                yield session
            finally:
                session.close()

        worker = JarvisOrchestratorWorker(
            worker_id="worker-lifecycle-node",
            poll_interval=0.1,
            heartbeat_interval=0.01,
            max_cycles=1,
            db_factory=mock_db_factory,
        )
        worker.run()

        with self.get_session() as session:
            events = [
                e.event_type for e in session.query(JarvisAuditLog).filter_by(
                    actor="worker-lifecycle-node"
                ).order_by(JarvisAuditLog.id.asc()).all()
            ]
            self.assertIn("WORKER_STARTED", events)
            self.assertIn("WORKER_HEARTBEAT", events)
            self.assertIn("WORKER_STOPPED", events)

    def test_stale_heartbeat_detection(self):
        """Heartbeats older than threshold (90s) are detected as stale."""
        now = datetime.now(timezone.utc)
        stale_time = now - timedelta(seconds=150)
        mock_record = {
            "event_type": "WORKER_HEARTBEAT",
            "actor": "stale-worker-1",
            "created_at": stale_time,
            "details": {"uptime_seconds": 300},
        }
        status, info = evaluate_worker_health(mock_record, now=now, stale_threshold_seconds=90)
        self.assertEqual(status, "stale")
        self.assertEqual(info["status"], "stale")
        self.assertEqual(info["worker_id"], "stale-worker-1")
        self.assertGreaterEqual(info["seconds_since_heartbeat"], 140)

    def test_missing_heartbeat_detection(self):
        """Missing heartbeat is evaluated as unavailable."""
        status, info = evaluate_worker_health(None)
        self.assertEqual(status, "unavailable")
        self.assertIsNone(info["worker_id"])
        self.assertIsNone(info["last_heartbeat"])

    def test_multiple_worker_identities_disambiguation(self):
        """get_latest_worker_heartbeat cleanly disambiguates between different worker nodes."""
        with self.get_session() as session:
            now = datetime.now(timezone.utc)
            record_worker_heartbeat(session, worker_id="node-alpha", details={"node": "A"})
            record_worker_heartbeat(session, worker_id="node-beta", details={"node": "B"})

            hb_alpha = get_latest_worker_heartbeat(session, worker_id="node-alpha")
            hb_beta = get_latest_worker_heartbeat(session, worker_id="node-beta")

            self.assertIsNotNone(hb_alpha)
            self.assertIsNotNone(hb_beta)
            self.assertEqual(hb_alpha["actor"], "node-alpha")
            self.assertEqual(hb_beta["actor"], "node-beta")
            self.assertEqual(hb_alpha["details"]["node"], "A")
            self.assertEqual(hb_beta["details"]["node"], "B")

    def test_health_endpoint_fresh_heartbeat_is_healthy(self):
        """When worker has a fresh heartbeat, GET /api/jarvis/health reports status healthy and worker running."""
        with self.get_session() as session:
            record_worker_heartbeat(session, worker_id="active-worker-7", details={"uptime_seconds": 45})

            with patch.dict(os.environ, {"ENABLE_JARVIS": "true", "JARVIS_INTERNAL_ORG_ID": "1"}):
                data = get_jarvis_health(db=session)
                self.assertEqual(data["status"], "healthy")
                self.assertEqual(data["worker_status"], "running")
                self.assertEqual(data["worker_id"], "active-worker-7")
                self.assertIsNotNone(data["last_heartbeat"])
                self.assertEqual(data["worker"]["status"], "running")

    def test_health_endpoint_stale_heartbeat_not_healthy(self):
        """When worker heartbeat is stale (>90s), GET /api/jarvis/health must NOT report healthy (reports degraded)."""
        with self.get_session() as session:
            # Insert a heartbeat 180 seconds in the past
            stale_time = datetime.now(timezone.utc) - timedelta(seconds=180)
            stale_log = JarvisAuditLog(
                event_type="WORKER_HEARTBEAT",
                actor="zombie-worker",
                organization_id=1,
                details={"uptime_seconds": 600},
                created_at=stale_time,
            )
            session.add(stale_log)
            session.commit()

            with patch.dict(os.environ, {"ENABLE_JARVIS": "true", "JARVIS_INTERNAL_ORG_ID": "1"}):
                data = get_jarvis_health(db=session)
                self.assertNotEqual(data["status"], "healthy")
                self.assertEqual(data["status"], "degraded")
                self.assertEqual(data["worker_status"], "stale")
                self.assertEqual(data["worker_id"], "zombie-worker")

    def test_health_endpoint_missing_heartbeat_not_healthy(self):
        """When no worker heartbeat exists in DB, GET /api/jarvis/health must NOT report healthy (reports degraded)."""
        with self.get_session() as session:
            with patch.dict(os.environ, {"ENABLE_JARVIS": "true", "JARVIS_INTERNAL_ORG_ID": "1"}):
                data = get_jarvis_health(db=session)
                self.assertNotEqual(data["status"], "healthy")
                self.assertEqual(data["status"], "degraded")
                self.assertEqual(data["worker_status"], "unavailable")

    def test_health_endpoint_gracefully_stopped_worker(self):
        """When worker records WORKER_STOPPED, GET /api/jarvis/health reports status degraded and worker stopped."""
        with self.get_session() as session:
            record_worker_lifecycle(session, worker_id="stopped-worker", event_type="WORKER_STOPPED", details={"reason": "SIGTERM"})

            with patch.dict(os.environ, {"ENABLE_JARVIS": "true", "JARVIS_INTERNAL_ORG_ID": "1"}):
                data = get_jarvis_health(db=session)
                self.assertNotEqual(data["status"], "healthy")
                self.assertEqual(data["status"], "degraded")
                self.assertEqual(data["worker_status"], "stopped")
                self.assertEqual(data["worker_id"], "stopped-worker")

    # --- 12. Alembic Hardening & Database DDL Protection Tests ---

    def test_migration_database_url_prefers_migration_env_var(self):
        """get_migration_database_url prioritizes MIGRATION_DATABASE_URL over default DATABASE_URL."""
        custom_url = "postgresql://leadvoix_migrator:secret123@db.example.com:5432/leadvoix"
        with patch.dict(os.environ, {"MIGRATION_DATABASE_URL": custom_url}):
            self.assertEqual(get_migration_database_url(), custom_url)

    def test_migration_database_url_accepts_alembic_database_url(self):
        """get_migration_database_url accepts ALEMBIC_DATABASE_URL as an alias."""
        custom_url = "postgresql://leadvoix_migrator:secret123@db.example.com:5432/leadvoix"
        with patch.dict(os.environ, {"MIGRATION_DATABASE_URL": "", "ALEMBIC_DATABASE_URL": custom_url}):
            self.assertEqual(get_migration_database_url(), custom_url)

    def test_migration_database_url_normalizes_postgres_protocol(self):
        """get_migration_database_url normalizes postgres:// prefix to postgresql://."""
        legacy_url = "postgres://leadvoix_migrator:secret123@db.example.com:5432/leadvoix"
        expected_url = "postgresql://leadvoix_migrator:secret123@db.example.com:5432/leadvoix"
        with patch.dict(os.environ, {"MIGRATION_DATABASE_URL": legacy_url}):
            self.assertEqual(get_migration_database_url(), expected_url)

    def test_migration_database_url_fallback_to_settings_database_url(self):
        """When migration env vars are unset, get_migration_database_url falls back to settings.DATABASE_URL."""
        with patch.dict(os.environ, {"MIGRATION_DATABASE_URL": "", "ALEMBIC_DATABASE_URL": ""}):
            from backend.app.core.config import settings
            expected = settings.DATABASE_URL
            if expected.startswith("postgres://"):
                expected = expected.replace("postgres://", "postgresql://", 1)
            self.assertEqual(get_migration_database_url(), expected)

    def test_migration_database_url_fails_when_all_unset(self):
        """When neither MIGRATION_DATABASE_URL nor settings.DATABASE_URL is available, raises RuntimeError."""
        with patch.dict(os.environ, {"MIGRATION_DATABASE_URL": "", "ALEMBIC_DATABASE_URL": ""}):
            with patch("backend.app.db.database.settings") as mock_settings:
                mock_settings.DATABASE_URL = ""
                with self.assertRaises(RuntimeError) as ctx:
                    get_migration_database_url()
                self.assertIn("Neither MIGRATION_DATABASE_URL nor DATABASE_URL", str(ctx.exception))

    def test_alembic_configure_kwargs_includes_schemas_and_pins_public_version_table_for_postgres(self):
        """get_context_configure_kwargs sets include_schemas=True and pins alembic_version to schema public for PostgreSQL."""
        mock_conn = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
        kwargs = get_context_configure_kwargs(connection=mock_conn)
        self.assertTrue(kwargs.get("include_schemas"))
        self.assertEqual(kwargs.get("version_table"), "alembic_version")
        self.assertEqual(kwargs.get("version_table_schema"), "public")

        # Also verify offline mode with postgres URL
        offline_kwargs = get_context_configure_kwargs(url="postgresql://leadvoix_migrator:pw@localhost/db")
        self.assertTrue(offline_kwargs.get("include_schemas"))
        self.assertEqual(offline_kwargs.get("version_table"), "alembic_version")
        self.assertEqual(offline_kwargs.get("version_table_schema"), "public")

    def test_alembic_configure_kwargs_omits_version_schema_for_sqlite(self):
        """For non-PostgreSQL dialects (e.g. SQLite), version_table_schema is omitted to prevent invalid database errors."""
        mock_conn = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))
        kwargs = get_context_configure_kwargs(connection=mock_conn)
        self.assertTrue(kwargs.get("include_schemas"))
        self.assertNotIn("version_table_schema", kwargs)

    def test_audit_log_trigger_ddl_in_phase_b_sql_script(self):
        """scripts/jarvis_phase_b_roles_and_schema.sql contains the audit log append-only trigger and security documentation."""
        sql_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "jarvis_phase_b_roles_and_schema.sql")
        with open(sql_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Trigger function definition
        self.assertIn("CREATE OR REPLACE FUNCTION jarvis.prevent_audit_log_mutation()", content)
        self.assertIn("RETURNS trigger AS $$", content)
        self.assertIn("RAISE EXCEPTION", content)
        self.assertIn("append-only audit trail", content)

        # Triggers
        self.assertIn("CREATE TRIGGER trg_protect_audit_logs_mutation", content)
        self.assertIn("BEFORE UPDATE OR DELETE ON jarvis.audit_logs", content)
        self.assertIn("FOR EACH ROW", content)
        self.assertIn("CREATE TRIGGER trg_protect_audit_logs_truncate", content)
        self.assertIn("BEFORE TRUNCATE ON jarvis.audit_logs", content)

        # Least-privilege grant layer
        self.assertIn("GRANT SELECT, INSERT ON TABLE jarvis.audit_logs TO jarvis_operator;", content)
        self.assertIn("REVOKE UPDATE, DELETE, TRUNCATE ON TABLE jarvis.audit_logs FROM jarvis_operator;", content)

        # Superuser / owner limitation documentation
        self.assertIn("Database-Owner / Superuser Limitation", content)
        self.assertIn("DISABLE TRIGGER", content)

    def test_alembic_phase_b_migration_includes_trigger_and_downgrade(self):
        """Alembic revision 4f7e2a1b9c3d applies the trigger on upgrade and drops it on downgrade."""
        rev_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "alembic", "versions",
            "4f7e2a1b9c3d_create_jarvis_schema_and_operational_tables.py"
        )
        with open(rev_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Upgrade creates trigger
        self.assertIn("CREATE OR REPLACE FUNCTION jarvis.prevent_audit_log_mutation()", content)
        self.assertIn("CREATE TRIGGER trg_protect_audit_logs_mutation", content)
        self.assertIn("CREATE TRIGGER trg_protect_audit_logs_truncate", content)

        # Downgrade drops trigger and function
        self.assertIn("DROP TRIGGER IF EXISTS trg_protect_audit_logs_mutation ON jarvis.audit_logs;", content)
        self.assertIn("DROP TRIGGER IF EXISTS trg_protect_audit_logs_truncate ON jarvis.audit_logs;", content)
        self.assertIn("DROP FUNCTION IF EXISTS jarvis.prevent_audit_log_mutation() CASCADE;", content)

    # --- 13. Deployment Manifests & Procfile Validation Tests ---

    def test_procfile_contains_web_worker_and_jarvis(self):
        """Procfile preserves existing web and call-worker entries and includes dedicated jarvis worker."""
        procfile_path = os.path.join(os.path.dirname(__file__), "..", "..", "Procfile")
        with open(procfile_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        procfile_dict = {}
        for line in lines:
            parts = line.split(":", 1)
            if len(parts) == 2:
                procfile_dict[parts[0].strip()] = parts[1].strip()

        # Existing services preserved
        self.assertIn("web", procfile_dict)
        self.assertIn("uvicorn backend.app.main:app", procfile_dict["web"])
        self.assertIn("worker", procfile_dict)
        self.assertIn("python -m backend.app.workers.call_worker", procfile_dict["worker"])

        # Dedicated jarvis worker added
        self.assertIn("jarvis", procfile_dict)
        self.assertEqual(procfile_dict["jarvis"], "python -m backend.app.workers.jarvis_worker")

    def test_render_yaml_valid_syntax_and_three_services(self):
        """deployment/render.yaml is valid YAML and defines exactly three services without replacing existing ones."""
        import yaml
        yaml_path = os.path.join(os.path.dirname(__file__), "..", "..", "deployment", "render.yaml")
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.assertIn("services", data)
        services = data["services"]
        self.assertEqual(len(services), 3)

        service_names = [s.get("name") for s in services]
        self.assertEqual(service_names, ["leadvoix-backend", "leadvoix-call-worker", "leadvoix-jarvis-worker"])

    def test_render_jarvis_worker_service_configuration(self):
        """leadvoix-jarvis-worker in render.yaml is properly configured as a background worker with secure env vars."""
        import yaml
        yaml_path = os.path.join(os.path.dirname(__file__), "..", "..", "deployment", "render.yaml")
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        jarvis_service = next(s for s in data["services"] if s.get("name") == "leadvoix-jarvis-worker")
        self.assertEqual(jarvis_service.get("type"), "worker")
        self.assertEqual(jarvis_service.get("env"), "python")
        self.assertEqual(jarvis_service.get("buildCommand"), "pip install -r backend/requirements.txt")
        self.assertEqual(jarvis_service.get("startCommand"), "python -m backend.app.workers.jarvis_worker process")

        env_vars = {item["key"]: item for item in jarvis_service.get("envVars", [])}

        # Safe defaults
        self.assertEqual(env_vars["ENABLE_JARVIS"].get("value"), "false")
        self.assertEqual(env_vars["JARVIS_KILL_SWITCH"].get("value"), "false")
        self.assertEqual(env_vars["JARVIS_INTERNAL_ORG_ID"].get("value"), "1")
        self.assertEqual(env_vars["JARVIS_TIMEZONE"].get("value"), "Asia/Kolkata")
        self.assertEqual(env_vars["PYTHON_VERSION"].get("value"), "3.11.15")

        # Secrets shielded via sync: false (zero hardcoded credentials)
        for secret_key in [
            "JARVIS_DATABASE_URL",
            "JARVIS_OPERATIONAL_DATABASE_URL",
            "MIGRATION_DATABASE_URL",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
        ]:
            self.assertIn(secret_key, env_vars)
            self.assertFalse(env_vars[secret_key].get("sync", True))
            self.assertNotIn("value", env_vars[secret_key])

    def test_jarvis_worker_cli_accepts_process_command(self):
        """jarvis_worker CLI parses 'process' positional argument and options without error."""
        from backend.app.workers.jarvis_worker import main, JarvisOrchestratorWorker

        # Verify parser handles 'process'
        with patch("sys.argv", ["jarvis_worker.py", "process", "--once"]):
            with patch.object(JarvisOrchestratorWorker, "run") as mock_run:
                main()
                mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
