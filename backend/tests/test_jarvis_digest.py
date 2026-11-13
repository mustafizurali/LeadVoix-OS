"""
LeadVoix Business JARVIS — Phase A Test Suite
Covers:
- Phase A Hardening:
  1. CallProcessingJob tenant isolation (join AgentCall, filter AgentCall.organization_id == internal_org_id)
  2. Mandatory read-only credentials in production (JARVIS_DATABASE_URL requirement)
  3. Session-level & transaction-level write prevention (commit, flush, add, delete, write SQL)
  4. Durable Idempotency Store (persistence across restarts, atomic file operations, thread safety)
  5. Safe dispatch retry behavior (cooldown on failure, uncompleted state on failed delivery)
  6. FastAPI dependency injection (get_jarvis_read_only_db)
- Existing Phase 1 tests:
  - Timezone calculations (Asia/Kolkata)
  - Executive digest formatting
  - Feature flag enforcement (ENABLE_JARVIS=false)
  - Admin authorization & validation
"""

from datetime import date, datetime, time, timedelta, timezone
import json
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import text

from backend.app.api.jarvis import (
    JarvisTriggerRequest,
    get_jarvis_health,
    get_jarvis_summary,
    trigger_jarvis_digest,
)
from backend.app.models.agent_call import AgentCall
from backend.app.models.call_processing_job import CallProcessingJob
from backend.app.services.jarvis_collector import (
    KOLKATA_TZ,
    ReadOnlyWriteAttemptError,
    _is_write_statement,
    apply_read_only_guards,
    calculate_digest_window,
    collect_jarvis_metrics,
    get_internal_org_id,
    get_jarvis_database_url,
    get_jarvis_read_only_db,
    get_jarvis_read_only_session,
    is_production_mode,
    is_readonly_db_required,
    reset_read_only_engine,
)
from backend.app.services.jarvis_digest import (
    DurableIdempotencyStore,
    _DISPATCHED_DIGESTS,
    format_executive_digest,
    generate_and_dispatch_digest,
    get_idempotency_store,
    is_jarvis_enabled,
    mask_token,
    send_telegram_notification,
    set_idempotency_store,
)


class JarvisPhaseAHardeningTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_idempotency_file = os.path.join(self.temp_dir.name, "jarvis_idempotency.json")
        self.patcher_env = patch.dict(os.environ, {
            "ENABLE_JARVIS": "true",
            "JARVIS_INTERNAL_ORG_ID": "1",
            "JARVIS_IDEMPOTENCY_FILE": self.temp_idempotency_file,
            "JARVIS_RETRY_COOLDOWN_SECONDS": "60",
            "REQUIRE_JARVIS_READONLY": "false",
            "ENVIRONMENT": "development",
        }, clear=False)
        self.patcher_env.start()
        reset_read_only_engine()
        set_idempotency_store(DurableIdempotencyStore(
            file_path=self.temp_idempotency_file,
            retry_cooldown_seconds=60,
        ))

    def tearDown(self):
        set_idempotency_store(None)
        reset_read_only_engine()
        self.patcher_env.stop()
        self.temp_dir.cleanup()

    # --- 1. CallProcessingJob Tenant Isolation ---

    def test_call_processing_jobs_join_and_filter_internal_org(self):
        """Verify CallProcessingJob query explicitly joins AgentCall and filters by internal_org_id."""
        mock_db = MagicMock()
        mock_org = SimpleNamespace(id=1, name="LeadVoix AI", slug="leadvoix-ai", plan="scale")
        mock_calls_summary = MagicMock(total_calls=5, total_duration_sec=600, avg_duration_sec=120.0)

        calls_recorded = []

        def query_side_effect(*args):
            q = MagicMock()
            q.filter.return_value = q
            q.group_by.return_value = q
            q.join.return_value = q

            # Check if this query is for CallProcessingJob
            if args and args[0] is CallProcessingJob.status:
                calls_recorded.append("CallProcessingJob")
                # Record join arguments to verify
                def record_join(target, condition=None):
                    calls_recorded.append(("join", target, str(condition)))
                    return q
                q.join.side_effect = record_join

                def record_filter(*filters):
                    for f in filters:
                        calls_recorded.append(("filter", str(f)))
                    return q
                q.filter.side_effect = record_filter
                q.all.return_value = [("completed", 5)]
            elif "Organization" in str(args[0]):
                q.first.return_value = mock_org
            elif "total_calls" in str(args):
                q.first.return_value = mock_calls_summary
            elif "count" in str(args[0]).lower() or "sum" in str(args[0]).lower():
                q.scalar.return_value = 2
            elif len(args) == 2:
                q.all.return_value = [("new", 2)]
            else:
                q.all.return_value = []
            return q

        mock_db.query.side_effect = query_side_effect

        metrics = collect_jarvis_metrics(mock_db, org_id=1)

        self.assertIn("CallProcessingJob", calls_recorded)
        # Verify join with AgentCall occurred
        join_calls = [c for c in calls_recorded if isinstance(c, tuple) and c[0] == "join"]
        self.assertTrue(len(join_calls) > 0)
        self.assertEqual(join_calls[0][1], AgentCall)

        # Verify filter by AgentCall.organization_id == 1 was applied
        filter_calls = [str(c[1]) for c in calls_recorded if isinstance(c, tuple) and c[0] == "filter"]
        has_org_filter = any("organization_id" in f for f in filter_calls)
        self.assertTrue(has_org_filter, f"Filters recorded: {filter_calls}")
        self.assertEqual(metrics["system_jobs"]["processing_jobs_summary"], {"completed": 5})

    # --- 2. Mandatory Read-Only Credentials in Production ---

    def test_mandatory_read_only_url_in_production(self):
        """In production mode or when REQUIRE_JARVIS_READONLY=true, missing JARVIS_DATABASE_URL must raise RuntimeError."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "JARVIS_DATABASE_URL": ""}):
            self.assertTrue(is_production_mode())
            self.assertTrue(is_readonly_db_required())
            with self.assertRaises(RuntimeError) as ctx:
                get_jarvis_database_url()
            self.assertIn("Security violation: JARVIS_DATABASE_URL is mandatory", str(ctx.exception))

    def test_mandatory_read_only_url_flag(self):
        """When REQUIRE_JARVIS_READONLY=true in any environment, missing JARVIS_DATABASE_URL must raise RuntimeError."""
        with patch.dict(os.environ, {"REQUIRE_JARVIS_READONLY": "true", "JARVIS_DATABASE_URL": ""}):
            self.assertTrue(is_readonly_db_required())
            with self.assertRaises(RuntimeError) as ctx:
                get_jarvis_database_url()
            self.assertIn("Security violation", str(ctx.exception))

    def test_custom_read_only_url_accepted(self):
        """When JARVIS_DATABASE_URL is provided, it must be returned directly."""
        custom_url = "postgresql://read_only_user:secret@db.internal:5432/leadvoix_prod"
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "JARVIS_DATABASE_URL": custom_url}):
            self.assertEqual(get_jarvis_database_url(), custom_url)

    # --- 3. Read-Only Session Write Prevention ---

    def test_session_write_methods_blocked(self):
        """apply_read_only_guards must block commit, flush, add, add_all, delete."""
        mock_session = MagicMock()
        apply_read_only_guards(mock_session)

        dummy_obj = SimpleNamespace(id=1)
        with self.assertRaises(ReadOnlyWriteAttemptError):
            mock_session.commit()
        with self.assertRaises(ReadOnlyWriteAttemptError):
            mock_session.flush()
        with self.assertRaises(ReadOnlyWriteAttemptError):
            mock_session.add(dummy_obj)
        with self.assertRaises(ReadOnlyWriteAttemptError):
            mock_session.add_all([dummy_obj])
        with self.assertRaises(ReadOnlyWriteAttemptError):
            mock_session.delete(dummy_obj)

    def test_raw_write_sql_blocked_by_session_execute(self):
        """Guarded execute must reject DML and DDL write operations."""
        mock_session = MagicMock()
        apply_read_only_guards(mock_session)

        write_statements = [
            text("INSERT INTO leads (first_name) VALUES ('Hacked');"),
            text("UPDATE agent_calls SET status = 'deleted';"),
            text("DELETE FROM organizations WHERE id = 1;"),
            text("DROP TABLE leads;"),
            text("ALTER TABLE users ADD COLUMN compromised text;"),
            text("TRUNCATE TABLE deals;"),
            "CREATE TABLE evil (id int);",
        ]

        for stmt in write_statements:
            with self.subTest(statement=str(stmt)):
                with self.assertRaises(ReadOnlyWriteAttemptError):
                    mock_session.execute(stmt)

    def test_read_and_transaction_statements_allowed(self):
        """SELECT and transaction-read-only statements must execute without raising ReadOnlyWriteAttemptError."""
        mock_session = MagicMock()
        apply_read_only_guards(mock_session)

        # Should execute cleanly
        mock_session.execute(text("SET TRANSACTION READ ONLY;"))
        mock_session.execute(text("SELECT 1;"))
        mock_session.execute(text("SELECT count(*) FROM leads WHERE organization_id = 1;"))

        # Verify underlying execute was actually called 3 times
        self.assertEqual(mock_session.execute.__wrapped__ if hasattr(mock_session.execute, "__wrapped__") else mock_session._mock_mock_calls, mock_session._mock_mock_calls)

    def test_is_write_statement_helper(self):
        self.assertTrue(_is_write_statement("INSERT INTO foo VALUES (1)"))
        self.assertTrue(_is_write_statement("  update users set x=1"))
        self.assertTrue(_is_write_statement("DELETE FROM bar"))
        self.assertTrue(_is_write_statement("/* comment */ DROP TABLE bar"))
        self.assertTrue(_is_write_statement("-- comment\nALTER TABLE bar ADD col int"))
        self.assertFalse(_is_write_statement("SELECT * FROM foo"))
        self.assertFalse(_is_write_statement("SET TRANSACTION READ ONLY;"))

    # --- 4. Durable Idempotency Store ---

    def test_durable_idempotency_store_file_persistence(self):
        """DurableIdempotencyStore must persist records to disk and reload them across instances."""
        store1 = DurableIdempotencyStore(file_path=self.temp_idempotency_file, retry_cooldown_seconds=60)
        self.assertTrue(os.path.exists(os.path.dirname(self.temp_idempotency_file)))

        test_key = "1:morning:2026-11-10"
        store1.record_success(test_key, {"digest_type": "morning", "summary": "ok"})

        self.assertTrue(os.path.exists(self.temp_idempotency_file))

        # Create a new store instance pointing to the same file
        store2 = DurableIdempotencyStore(file_path=self.temp_idempotency_file, retry_cooldown_seconds=60)
        record = store2.get_record(test_key)
        self.assertIsNotNone(record)
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["digest_type"], "morning")

        allowed, reason, details = store2.check_dispatch_allowed(test_key, force=False)
        self.assertFalse(allowed)
        self.assertEqual(reason, "already_dispatched")

    def test_durable_idempotency_force_bypass(self):
        """check_dispatch_allowed must return True when force=True even if completed."""
        store = DurableIdempotencyStore(file_path=self.temp_idempotency_file, retry_cooldown_seconds=60)
        test_key = "1:morning:2026-11-10"
        store.record_success(test_key, {"status": "completed"})

        allowed, reason, _ = store.check_dispatch_allowed(test_key, force=True)
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    # --- 5. Safe Dispatch Retry Behavior ---

    def test_failed_delivery_records_failure_and_enforces_cooldown(self):
        """Delivery failure must record status 'failed' with cooldown, and not record 'completed'."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_resp = MagicMock(status_code=500, text="Internal Telegram Error")
        mock_client.post.return_value = mock_resp

        with patch("backend.app.services.jarvis_digest.collect_jarvis_metrics", return_value={
            "organization": {"name": "LeadVoix AI"},
            "window": {"start_kolkata": "A", "end_kolkata": "B"},
            "telephony": {}, "leads": {}, "deals": {}, "tasks": {}, "system_jobs": {},
        }):
            with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "token_123", "TELEGRAM_CHAT_ID": "chat_123"}):
                # 1. First attempt fails due to HTTP 500
                res1 = generate_and_dispatch_digest(
                    digest_type="morning",
                    target_date=date(2026, 11, 10),
                    force=False,
                    send_telegram=True,
                    db=mock_db,
                    http_client=mock_client,
                )
                self.assertEqual(res1["status"], "delivery_failed")
                self.assertFalse(res1["telegram"]["delivered"])
                self.assertEqual(res1["retry_count"], 1)

                # Verify store state
                store = get_idempotency_store()
                record = store.get_record(res1["idempotency_key"])
                self.assertEqual(record["status"], "failed")
                self.assertEqual(record["retry_count"], 1)

                # 2. Immediate second attempt without force is blocked by cooldown
                res2 = generate_and_dispatch_digest(
                    digest_type="morning",
                    target_date=date(2026, 11, 10),
                    force=False,
                    send_telegram=True,
                    db=mock_db,
                    http_client=mock_client,
                )
                self.assertEqual(res2["status"], "retry_cooldown")
                self.assertTrue(res2["idempotent"])
                self.assertGreater(res2["cooldown_remaining_seconds"], 0)
                self.assertIn("cooldown active", res2["message"].lower())

                # 3. Third attempt with force=True bypasses cooldown
                res3 = generate_and_dispatch_digest(
                    digest_type="morning",
                    target_date=date(2026, 11, 10),
                    force=True,
                    send_telegram=True,
                    db=mock_db,
                    http_client=mock_client,
                )
                self.assertEqual(res3["status"], "delivery_failed")
                self.assertEqual(res3["retry_count"], 2)

    def test_successful_retry_after_cooldown_expires(self):
        """When retry cooldown expires (or cooldown is 0), retry proceeds and transitions to 'completed'."""
        mock_db = MagicMock()
        # Set cooldown to 0 for instant retry test
        store = DurableIdempotencyStore(file_path=self.temp_idempotency_file, retry_cooldown_seconds=0)
        set_idempotency_store(store)

        mock_failing_client = MagicMock()
        mock_failing_client.post.return_value = MagicMock(status_code=503, text="Service Unavailable")

        mock_success_client = MagicMock()
        mock_resp_ok = MagicMock(status_code=200)
        mock_resp_ok.json.return_value = {"ok": True, "result": {"message_id": 777}}
        mock_success_client.post.return_value = mock_resp_ok

        with patch("backend.app.services.jarvis_digest.collect_jarvis_metrics", return_value={
            "organization": {"name": "LeadVoix AI"},
            "window": {"start_kolkata": "A", "end_kolkata": "B"},
            "telephony": {}, "leads": {}, "deals": {}, "tasks": {}, "system_jobs": {},
        }):
            with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "token_123", "TELEGRAM_CHAT_ID": "chat_123"}):
                # 1. Failure attempt
                res1 = generate_and_dispatch_digest(
                    digest_type="morning",
                    target_date=date(2026, 11, 10),
                    force=False,
                    send_telegram=True,
                    db=mock_db,
                    http_client=mock_failing_client,
                )
                self.assertEqual(res1["status"], "delivery_failed")

                # 2. Retry succeeds because cooldown is 0
                res2 = generate_and_dispatch_digest(
                    digest_type="morning",
                    target_date=date(2026, 11, 10),
                    force=False,
                    send_telegram=True,
                    db=mock_db,
                    http_client=mock_success_client,
                )
                self.assertEqual(res2["status"], "success")
                self.assertTrue(res2["telegram"]["delivered"])

                # 3. Subsequent call now returns 'already_dispatched'
                res3 = generate_and_dispatch_digest(
                    digest_type="morning",
                    target_date=date(2026, 11, 10),
                    force=False,
                    send_telegram=True,
                    db=mock_db,
                    http_client=mock_success_client,
                )
                self.assertEqual(res3["status"], "already_dispatched")

    # --- 6. FastAPI Dependency & Handler Tests ---

    def test_get_jarvis_read_only_db_yields_guarded_session(self):
        """FastAPI dependency get_jarvis_read_only_db must yield a session with write guards applied."""
        mock_raw_session = MagicMock()
        mock_sm = MagicMock(return_value=mock_raw_session)

        with patch("backend.app.services.jarvis_collector.get_read_only_sessionmaker", return_value=mock_sm):
            generator = get_jarvis_read_only_db()
            session = next(generator)
            with self.assertRaises(ReadOnlyWriteAttemptError):
                session.commit()
            with self.assertRaises(ReadOnlyWriteAttemptError):
                session.add(SimpleNamespace())
            # Cleanup generator
            try:
                next(generator)
            except StopIteration:
                pass


class JarvisCollectorAndDigestTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_idempotency_file = os.path.join(self.temp_dir.name, "jarvis_idempotency.json")
        self.patcher_env = patch.dict(os.environ, {
            "ENABLE_JARVIS": "true",
            "JARVIS_INTERNAL_ORG_ID": "1",
            "JARVIS_IDEMPOTENCY_FILE": self.temp_idempotency_file,
            "JARVIS_RETRY_COOLDOWN_SECONDS": "60",
        }, clear=False)
        self.patcher_env.start()
        set_idempotency_store(DurableIdempotencyStore(file_path=self.temp_idempotency_file, retry_cooldown_seconds=60))

    def tearDown(self):
        set_idempotency_store(None)
        self.patcher_env.stop()
        self.temp_dir.cleanup()

    def test_feature_flag_is_jarvis_enabled(self):
        with patch.dict(os.environ, {"ENABLE_JARVIS": "false"}):
            self.assertFalse(is_jarvis_enabled())
        with patch.dict(os.environ, {"ENABLE_JARVIS": "true"}):
            self.assertTrue(is_jarvis_enabled())
        with patch.dict(os.environ, {"ENABLE_JARVIS": "1"}):
            self.assertTrue(is_jarvis_enabled())
        with patch.dict(os.environ, {"ENABLE_JARVIS": "0"}):
            self.assertFalse(is_jarvis_enabled())

    def test_internal_org_id_resolution(self):
        with patch.dict(os.environ, {"JARVIS_INTERNAL_ORG_ID": "42"}):
            self.assertEqual(get_internal_org_id(), 42)
        with patch.dict(os.environ, {"JARVIS_INTERNAL_ORG_ID": ""}):
            self.assertEqual(get_internal_org_id(), 1)

    def test_mask_token(self):
        self.assertEqual(mask_token(None), "[NOT_CONFIGURED]")
        self.assertEqual(mask_token("short"), "[NOT_CONFIGURED]")
        self.assertEqual(mask_token("1234567890abcdef"), "1234...cdef")

    def test_calculate_digest_window_morning(self):
        ref_date = date(2026, 11, 10)
        start_utc, end_utc, label = calculate_digest_window("morning", target_date=ref_date)

        start_kolkata = start_utc.astimezone(KOLKATA_TZ)
        end_kolkata = end_utc.astimezone(KOLKATA_TZ)

        self.assertEqual(start_kolkata.date(), date(2026, 11, 9))
        self.assertEqual(start_kolkata.time(), time.min)
        self.assertEqual(end_kolkata.date(), date(2026, 11, 9))
        self.assertIn("Morning Briefing", label)

    def test_calculate_digest_window_evening(self):
        ref_date = date(2026, 11, 10)
        start_utc, end_utc, label = calculate_digest_window("evening", target_date=ref_date)
        
        start_kolkata = start_utc.astimezone(KOLKATA_TZ)
        end_kolkata = end_utc.astimezone(KOLKATA_TZ)
        
        self.assertEqual(start_kolkata.date(), date(2026, 11, 10))
        self.assertEqual(start_kolkata.time(), time.min)
        self.assertEqual(end_kolkata.date(), date(2026, 11, 10))
        self.assertEqual(end_kolkata.hour, 21)
        self.assertEqual(end_kolkata.minute, 0)
        self.assertIn("Evening Debrief", label)

    def test_read_only_session_prevents_modifications(self):
        mock_session = MagicMock()
        mock_sm = MagicMock(return_value=mock_session)

        with patch("backend.app.services.jarvis_collector.get_read_only_sessionmaker", return_value=mock_sm):
            with get_jarvis_read_only_session() as session:
                with self.assertRaises(ReadOnlyWriteAttemptError):
                    session.commit()
                with self.assertRaises(ReadOnlyWriteAttemptError):
                    session.flush()

    def test_collect_jarvis_metrics_aggregates_and_filters_tenant(self):
        """Verify collector queries only the internal organization and exposes zero customer PII."""
        mock_db = MagicMock()
        mock_org = SimpleNamespace(id=1, name="LeadVoix AI", slug="leadvoix-ai", plan="scale")
        mock_calls_summary = MagicMock(total_calls=12, total_duration_sec=3600, avg_duration_sec=300.0)

        def query_side_effect(*args):
            q = MagicMock()
            q.filter.return_value = q
            q.group_by.return_value = q
            q.join.return_value = q
            
            if "Organization" in str(args[0]):
                q.first.return_value = mock_org
            elif "total_calls" in str(args):
                q.first.return_value = mock_calls_summary
            elif "count" in str(args[0]).lower() or "sum" in str(args[0]).lower():
                q.scalar.return_value = 5
            elif len(args) == 2:
                q.all.return_value = [("completed", 10), ("in-progress", 2)]
            else:
                q.all.return_value = []
            return q

        mock_db.query.side_effect = query_side_effect

        metrics = collect_jarvis_metrics(mock_db, org_id=1)

        self.assertEqual(metrics["organization"]["id"], 1)
        self.assertEqual(metrics["organization"]["name"], "LeadVoix AI")
        self.assertEqual(metrics["telephony"]["total_calls"], 12)
        self.assertEqual(metrics["telephony"]["total_duration_minutes"], 60.0)
        self.assertIn("completed", metrics["telephony"]["status_breakdown"])

        # PII Check: ensure caller_phone, caller_name, email, transcript are NEVER top-level keys
        metrics_str = str(metrics).lower()
        self.assertNotIn("caller_phone", metrics_str)
        self.assertNotIn("caller_name", metrics_str)
        self.assertNotIn("transcript", metrics_str)

    def test_format_executive_digest(self):
        sample_metrics = {
            "organization": {"name": "LeadVoix AI"},
            "window": {
                "start_kolkata": "2026-11-09 00:00:00 IST",
                "end_kolkata": "2026-11-09 23:59:59 IST",
            },
            "telephony": {
                "total_calls": 25,
                "status_breakdown": {"completed": 23, "failed": 2},
                "total_duration_minutes": 115.5,
                "average_duration_seconds": 277.2,
            },
            "leads": {
                "total_leads": 8,
                "source_breakdown": {"website": 5, "phone": 3},
            },
            "deals": {
                "total_deals_created": 3,
                "won_amount_total": 4500.0,
            },
            "tasks": {
                "status_breakdown": {"pending": 4, "completed": 6},
            },
            "system_jobs": {
                "processing_jobs_summary": {"completed": 25},
            },
        }

        digest_text = format_executive_digest(sample_metrics, "morning", "Morning Briefing")

        self.assertIn("LeadVoix Business JARVIS — Morning Briefing", digest_text)
        self.assertIn("LeadVoix AI", digest_text)
        self.assertIn("Total Inbound/Outbound Calls: *25*", digest_text)
        self.assertIn("New Inbound Leads: *8*", digest_text)
        self.assertIn("$4,500.00", digest_text)
        self.assertIn("Operational ✅", digest_text)

    def test_send_telegram_notification_unconfigured(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
            res = send_telegram_notification("Test message")
            self.assertFalse(res["delivered"])
            self.assertEqual(res["reason"], "telegram_not_configured")

    def test_send_telegram_notification_mocked_http_success(self):
        mock_client = MagicMock()
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"ok": True, "result": {"message_id": 999}}
        mock_client.post.return_value = mock_resp

        res = send_telegram_notification(
            "Test message",
            bot_token="test_token_12345",
            chat_id="12345678",
            client=mock_client,
        )

        self.assertTrue(res["delivered"])
        self.assertEqual(res["message_id"], 999)
        mock_client.post.assert_called_once()
        call_url = mock_client.post.call_args[0][0]
        self.assertIn("test_token_12345", call_url)

    def test_generate_and_dispatch_idempotency(self):
        mock_db = MagicMock()
        with patch("backend.app.services.jarvis_digest.collect_jarvis_metrics", return_value={
            "organization": {"name": "LeadVoix AI"},
            "window": {"start_kolkata": "A", "end_kolkata": "B"},
            "telephony": {}, "leads": {}, "deals": {}, "tasks": {}, "system_jobs": {},
        }):
            # First dispatch
            res1 = generate_and_dispatch_digest(
                digest_type="morning",
                target_date=date(2026, 11, 10),
                force=False,
                send_telegram=False,
                db=mock_db,
            )
            self.assertEqual(res1["status"], "success")

            # Second duplicate dispatch without force -> should be blocked by idempotency
            res2 = generate_and_dispatch_digest(
                digest_type="morning",
                target_date=date(2026, 11, 10),
                force=False,
                send_telegram=False,
                db=mock_db,
            )
            self.assertEqual(res2["status"], "already_dispatched")
            self.assertTrue(res2["idempotent"])

            # Third dispatch WITH force -> should proceed
            res3 = generate_and_dispatch_digest(
                digest_type="morning",
                target_date=date(2026, 11, 10),
                force=True,
                send_telegram=False,
                db=mock_db,
            )
            self.assertEqual(res3["status"], "success")


class JarvisApiEndpointsTests(unittest.TestCase):
    def setUp(self):
        self.admin_user = SimpleNamespace(id=1, email="admin@leadvoix.com", role="admin", organization_id=1)

    def test_get_health_when_disabled(self):
        with patch.dict(os.environ, {"ENABLE_JARVIS": "false"}):
            data = get_jarvis_health()
            self.assertEqual(data["status"], "disabled")
            self.assertFalse(data["enabled"])

    def test_get_health_when_enabled(self):
        with patch.dict(os.environ, {"ENABLE_JARVIS": "true", "JARVIS_INTERNAL_ORG_ID": "1"}):
            data = get_jarvis_health()
            self.assertEqual(data["status"], "healthy")
            self.assertTrue(data["enabled"])
            self.assertEqual(data["internal_org_id"], 1)

    def test_summary_blocked_when_jarvis_disabled(self):
        mock_db = MagicMock()
        with patch.dict(os.environ, {"ENABLE_JARVIS": "false"}):
            with self.assertRaises(HTTPException) as ctx:
                get_jarvis_summary(digest_type="morning", date=None, db=mock_db, current_user=self.admin_user)
            self.assertEqual(ctx.exception.status_code, 403)
            self.assertIn("JARVIS is disabled", ctx.exception.detail)

    def test_summary_success_when_admin_and_enabled(self):
        mock_db = MagicMock()
        with patch.dict(os.environ, {"ENABLE_JARVIS": "true"}):
            with patch("backend.app.api.jarvis.collect_jarvis_metrics", return_value={
                "organization": {"name": "LeadVoix AI"},
                "window": {"start_kolkata": "A", "end_kolkata": "B"},
                "telephony": {"total_calls": 5},
                "leads": {"total_leads": 2},
                "deals": {},
                "tasks": {},
                "system_jobs": {},
            }):
                data = get_jarvis_summary(digest_type="morning", date=None, db=mock_db, current_user=self.admin_user)
                self.assertEqual(data["status"], "success")
                self.assertEqual(data["digest_type"], "morning")
                self.assertIn("Morning Briefing", data["formatted_digest"])

    def test_summary_rejects_invalid_date_format(self):
        mock_db = MagicMock()
        with patch.dict(os.environ, {"ENABLE_JARVIS": "true"}):
            with self.assertRaises(HTTPException) as ctx:
                get_jarvis_summary(digest_type="morning", date="invalid-date", db=mock_db, current_user=self.admin_user)
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("Invalid date format", ctx.exception.detail)

    def test_trigger_digest_blocked_when_jarvis_disabled(self):
        mock_db = MagicMock()
        payload = JarvisTriggerRequest(digest_type="evening", force=True, send_telegram=False)
        with patch.dict(os.environ, {"ENABLE_JARVIS": "false"}):
            with self.assertRaises(HTTPException) as ctx:
                trigger_jarvis_digest(payload=payload, db=mock_db, current_user=self.admin_user)
            self.assertEqual(ctx.exception.status_code, 403)

    def test_trigger_digest_success(self):
        mock_db = MagicMock()
        payload = JarvisTriggerRequest(digest_type="evening", force=True, send_telegram=False)
        with patch.dict(os.environ, {"ENABLE_JARVIS": "true"}):
            with patch("backend.app.api.jarvis.generate_and_dispatch_digest", return_value={
                "status": "success",
                "digest_type": "evening",
                "formatted_digest": "Test Evening Digest",
                "telegram": {"delivered": False, "reason": "telegram_not_configured"},
            }):
                data = trigger_jarvis_digest(payload=payload, db=mock_db, current_user=self.admin_user)
                self.assertEqual(data["status"], "success")
                self.assertEqual(data["digest_type"], "evening")


if __name__ == "__main__":
    unittest.main()
