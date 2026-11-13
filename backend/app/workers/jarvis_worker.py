"""
LeadVoix Business JARVIS — Dedicated 24/7 Background Orchestrator Worker
Phase B Core Architecture

Responsibilities:
- Runs in an isolated OS process completely separate from call_worker.py.
- Polls and processes persistent tasks from jarvis.jarvis_tasks.
- Enforces atomic task claiming using SELECT FOR UPDATE SKIP LOCKED.
- Handles automated morning briefings (08:00 IST) and evening debriefs (21:00 IST).
- Reclaims abandoned and expired task leases for crash and restart recovery.
- Responsive to emergency kill switches and OS signals (SIGINT, SIGTERM, SIGBREAK).
- Bounded database connection handling with context-managed sessions.
- Exposes health metrics and heartbeat telemetry.
"""

import argparse
from datetime import datetime, time, timedelta, timezone
import logging
import os
import signal
import socket
import sys
import threading
import time as pytime
from typing import Any, Callable, Dict, Optional
import uuid

from sqlalchemy.orm import Session

from backend.app.models.jarvis import JarvisTask
from backend.app.services.jarvis_audit import (
    record_audit_event,
    record_worker_heartbeat,
    record_worker_lifecycle,
)
from backend.app.services.jarvis_collector import (
    DEFAULT_TIMEZONE_NAME,
    InvalidTimezoneConfigurationError,
    KOLKATA_TZ,
    get_internal_org_id,
    get_jarvis_operational_session,
    get_jarvis_read_only_session,
    get_jarvis_timezone,
)
from backend.app.services.jarvis_digest import (
    generate_and_dispatch_digest,
    is_jarvis_enabled,
)
from backend.app.services.jarvis_queue import JarvisQueueManager


logger = logging.getLogger("leadvoix.jarvis.worker")


def is_kill_switch_active() -> bool:
    """Returns True if the emergency kill switch is activated or JARVIS is disabled."""
    raw_switch = os.getenv("JARVIS_KILL_SWITCH", "false").strip().lower()
    if raw_switch in ("true", "1", "yes", "on"):
        return True
    return not is_jarvis_enabled()


class JarvisOrchestratorWorker:
    """
    Dedicated 24/7 background orchestrator for LeadVoix Business JARVIS.
    Independent from call_worker.py.
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        poll_interval: Optional[float] = None,
        lease_seconds: int = 300,
        max_cycles: Optional[int] = None,
        db_factory: Optional[Callable[[], Session]] = None,
        timezone_name: Optional[str] = None,
        heartbeat_interval: Optional[float] = None,
    ):
        hostname = socket.gethostname() or "host"
        pid = os.getpid()
        random_suffix = uuid.uuid4().hex[:6]

        self.worker_id = (
            worker_id
            or os.getenv("JARVIS_WORKER_ID")
            or f"jarvis-worker-{hostname}-{pid}-{random_suffix}"
        )

        raw_poll = (
            poll_interval
            if poll_interval is not None
            else float(os.getenv("JARVIS_POLL_INTERVAL_SECONDS", "5.0"))
        )
        self.poll_interval = max(0.1, float(raw_poll))
        self.lease_seconds = int(os.getenv("JARVIS_LEASE_SECONDS", str(lease_seconds)))
        self.max_cycles = max_cycles
        self.custom_db_factory = db_factory

        raw_hb = (
            heartbeat_interval
            if heartbeat_interval is not None
            else float(os.getenv("JARVIS_HEARTBEAT_INTERVAL_SECONDS", "30.0"))
        )
        self.heartbeat_interval = max(0.1, float(raw_hb))
        self.last_db_heartbeat: Optional[datetime] = None

        # Timezone configuration: fails closed on invalid timezone
        self.timezone_name = timezone_name or os.getenv("JARVIS_TIMEZONE", DEFAULT_TIMEZONE_NAME)
        self.timezone = get_jarvis_timezone(self.timezone_name)

        # In-memory tracking of scheduled task keys to avoid repeated queries within same calendar day
        self._scheduled_keys: set[str] = set()

        self.stop_event = threading.Event()
        self.cycles_completed = 0
        self.tasks_processed = 0
        self.last_heartbeat: Optional[datetime] = None
        self.last_reap_time: Optional[datetime] = None
        self.start_time = datetime.now(timezone.utc)

    def register_signal_handlers(self) -> None:
        """Registers OS signal handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self._handle_signal)
            except (ValueError, AttributeError) as exc:
                logger.debug("Signal %s could not be registered: %s", sig, exc)

        if hasattr(signal, "SIGBREAK"):
            try:
                signal.signal(signal.SIGBREAK, self._handle_signal)
            except (ValueError, AttributeError):
                pass

    def _handle_signal(self, signum: int, frame: Any) -> None:
        sig_name = (
            signal.Signals(signum).name
            if hasattr(signal, "Signals") and signum in signal.Signals._value2member_map_
            else str(signum)
        )
        logger.info(
            "Worker '%s' received termination signal (%s). Initiating graceful shutdown...",
            self.worker_id,
            sig_name,
        )
        self.stop()

    def stop(self) -> None:
        """Signals the worker loop to stop after the current cycle."""
        self.stop_event.set()

    def get_session(self):
        """Yields an operational database session with bounded connection lifecycle."""
        if self.custom_db_factory is not None:
            return self.custom_db_factory()
        return get_jarvis_operational_session()

    def get_health(self) -> Dict[str, Any]:
        """Returns runtime diagnostic metrics for health checks."""
        now = datetime.now(timezone.utc)
        uptime_seconds = int((now - self.start_time).total_seconds())
        kill_active = is_kill_switch_active()

        return {
            "worker_id": self.worker_id,
            "status": "stopped" if self.stop_event.is_set() else ("halted_kill_switch" if kill_active else "running"),
            "kill_switch_active": kill_active,
            "uptime_seconds": uptime_seconds,
            "cycles_completed": self.cycles_completed,
            "tasks_processed": self.tasks_processed,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "last_db_heartbeat": self.last_db_heartbeat.isoformat() if self.last_db_heartbeat else None,
            "poll_interval": self.poll_interval,
            "heartbeat_interval": self.heartbeat_interval,
            "lease_seconds": self.lease_seconds,
            "timezone": getattr(self.timezone, "key", str(self.timezone)),
        }

    def check_and_enqueue_scheduled_briefings(
        self,
        db: Session,
        ref_now: Optional[datetime] = None,
    ) -> list[str]:
        """
        Evaluates current wall clock against configured JARVIS_TIMEZONE and enqueues automated briefings:
        - Morning Briefing: scheduled for 08:00 local time
        - Evening Debrief: scheduled for 21:00 local time

        Features:
        - Configurable timezone (defaults to Asia/Kolkata).
        - Idempotent catch-up: if current time is past the briefing time today (e.g. past 08:00 or past 21:00)
          and the task has not been enqueued today, enqueues it safely.
        - Deduplication across workers and worker restarts using durable task idempotency keys.
        """
        now_local = ref_now if ref_now is not None else datetime.now(self.timezone)
        if now_local.tzinfo is None:
            now_local = now_local.replace(tzinfo=self.timezone)
        else:
            now_local = now_local.astimezone(self.timezone)

        today_date = now_local.date()
        today_str = today_date.strftime("%Y-%m-%d")
        org_id = get_internal_org_id()

        # Prune memory cache of scheduled keys from previous days
        self._scheduled_keys = {k for k in self._scheduled_keys if today_str in k}

        enqueued_types: list[str] = []

        # 1. Morning Briefing: Due at or after 08:00 local time
        morning_time = time(8, 0, 0)
        if now_local.time() >= morning_time:
            morning_key = f"digest_morning:{org_id}:{today_str}"
            if morning_key not in self._scheduled_keys:
                task = self._ensure_scheduled_task(db, "digest_morning", org_id, today_str, morning_key)
                self._scheduled_keys.add(morning_key)
                if task:
                    enqueued_types.append("digest_morning")

        # 2. Evening Debrief: Due at or after 21:00 local time
        evening_time = time(21, 0, 0)
        if now_local.time() >= evening_time:
            evening_key = f"digest_evening:{org_id}:{today_str}"
            if evening_key not in self._scheduled_keys:
                task = self._ensure_scheduled_task(db, "digest_evening", org_id, today_str, evening_key)
                self._scheduled_keys.add(evening_key)
                if task:
                    enqueued_types.append("digest_evening")

        return enqueued_types

    def _ensure_scheduled_task(
        self,
        db: Session,
        task_type: str,
        org_id: int,
        date_str: str,
        idempotency_key: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Enqueues task with unique idempotency_key if it does not already exist.
        Returns the new JarvisTask if enqueued, or None if already existing.
        """
        key = idempotency_key or f"{task_type}:{org_id}:{date_str}"
        existing = (
            db.query(JarvisTask)
            .filter(JarvisTask.idempotency_key == key)
            .first()
        )
        if existing:
            logger.info("Scheduled task %s already exists (#%s, status: %s). Duplicate suppressed.", key, existing.id, existing.status)
            return None

        payload = {"digest_type": "morning" if "morning" in task_type else "evening", "date": date_str}
        task = JarvisQueueManager.enqueue_task(
            db,
            task_type=task_type,
            idempotency_key=key,
            payload=payload,
            organization_id=org_id,
            max_attempts=3,
        )
        logger.info(
            "Auto-scheduled %s for %s (org #%s, key=%s, status=%s)",
            task_type,
            date_str,
            org_id,
            key,
            getattr(task, "status", "unknown"),
        )
        return task

    def execute_task(self, db: Session, task) -> bool:
        """
        Dispatches an operational task to the appropriate service handler.
        """
        task_type = task.task_type
        payload = task.payload or {}
        digest_type = payload.get("digest_type", "custom")
        target_date_str = payload.get("date")
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date() if target_date_str else None

        logger.info("Executing task #%s (%s)", task.id, task_type)

        if task_type in ("digest_morning", "digest_evening", "digest_custom"):
            result = generate_and_dispatch_digest(
                digest_type=digest_type,
                target_date=target_date,
                force=False,
                send_telegram=True,
                operational_db=db,
            )
            if result.get("status") in ("success", "already_dispatched"):
                return True
            else:
                raise RuntimeError(f"Digest dispatch returned non-success status: {result.get('status')}")

        elif task_type == "health_check":
            logger.info("Processed health check task #%s", task.id)
            return True

        else:
            logger.warning("Unrecognized task_type '%s' for task #%s", task_type, task.id)
            return True

    def run_cycle(self) -> Dict[str, Any]:
        """
        Executes a single operational worker cycle:
        1. Checks kill switch.
        2. Updates heartbeat.
        3. Periodically reaps expired leases (restart recovery).
        4. Auto-enqueues scheduled briefings.
        5. Atomically claims and processes next task.
        """
        self.last_heartbeat = datetime.now(timezone.utc)
        self.cycles_completed += 1

        if is_kill_switch_active():
            logger.warning("JARVIS Kill Switch is active. Skipping task execution cycle.")
            return {"outcome": "killed_or_disabled", "tasks_processed": 0}

        tasks_processed_in_cycle = 0

        # Scoped operational session
        with self.get_session() as db:
            # 1. Periodic persistent heartbeat
            now = datetime.now(timezone.utc)
            if self.last_db_heartbeat is None or (now - self.last_db_heartbeat).total_seconds() >= self.heartbeat_interval:
                try:
                    record_worker_heartbeat(
                        db,
                        worker_id=self.worker_id,
                        status="running",
                        details={
                            "uptime_seconds": int((now - self.start_time).total_seconds()),
                            "cycles_completed": self.cycles_completed,
                            "tasks_processed": self.tasks_processed,
                            "kill_switch_active": is_kill_switch_active(),
                            "poll_interval": self.poll_interval,
                            "lease_seconds": self.lease_seconds,
                            "timezone": getattr(self.timezone, "key", str(self.timezone)),
                        },
                        organization_id=get_internal_org_id(),
                    )
                    self.last_db_heartbeat = now
                except Exception as exc:
                    logger.debug("Failed to record worker heartbeat: %s", exc)

            # 2. Periodic lease reaping (every 60s)
            if self.last_reap_time is None or (now - self.last_reap_time).total_seconds() > 60:
                try:
                    reaped = JarvisQueueManager.reap_expired_leases(db, now=now)
                    if reaped > 0:
                        record_audit_event(
                            db,
                            event_type="LEASE_RECOVERY",
                            details={"reclaimed_tasks": reaped, "worker_id": self.worker_id},
                            actor=self.worker_id,
                        )
                except Exception as exc:
                    logger.debug("Lease reaping error: %s", exc)
                self.last_reap_time = now

            # 3. Check scheduled briefings
            try:
                self.check_and_enqueue_scheduled_briefings(db)
            except Exception as exc:
                logger.debug("Scheduled briefing enqueue error: %s", exc)

            # 3. Claim next task
            task = None
            try:
                task = JarvisQueueManager.claim_next_task(db, self.worker_id, lease_seconds=self.lease_seconds)
            except Exception as exc:
                logger.error("Error claiming next task: %s", exc)

            if task:
                start_t = pytime.perf_counter()
                attempt = task.attempts
                JarvisQueueManager.record_attempt(
                    db,
                    task_id=task.id,
                    worker_instance=self.worker_id,
                    attempt_number=attempt,
                    status="started",
                )
                try:
                    success = self.execute_task(db, task)
                    duration_ms = int((pytime.perf_counter() - start_t) * 1000)
                    if success:
                        JarvisQueueManager.complete_task(db, task.id, task.claim_token)
                        JarvisQueueManager.record_attempt(
                            db,
                            task_id=task.id,
                            worker_instance=self.worker_id,
                            attempt_number=attempt,
                            status="succeeded",
                            duration_ms=duration_ms,
                        )
                        record_audit_event(
                            db,
                            event_type="TASK_COMPLETED",
                            details={"task_id": task.id, "task_type": task.task_type, "duration_ms": duration_ms},
                            actor=self.worker_id,
                        )
                        tasks_processed_in_cycle += 1
                        self.tasks_processed += 1
                except Exception as exc:
                    duration_ms = int((pytime.perf_counter() - start_t) * 1000)
                    error_msg = f"{type(exc).__name__}: {str(exc)}"
                    logger.error("Task #%s failed with error: %s", task.id, error_msg)
                    JarvisQueueManager.fail_task(db, task.id, task.claim_token, error_message=error_msg)
                    JarvisQueueManager.record_attempt(
                        db,
                        task_id=task.id,
                        worker_instance=self.worker_id,
                        attempt_number=attempt,
                        status="failed",
                        error_type=type(exc).__name__,
                        error_message=error_msg,
                        duration_ms=duration_ms,
                    )
                    record_audit_event(
                        db,
                        event_type="TASK_FAILED",
                        details={"task_id": task.id, "error": error_msg, "duration_ms": duration_ms},
                        actor=self.worker_id,
                    )

        return {"outcome": "completed", "tasks_processed": tasks_processed_in_cycle}

    def run(self) -> None:
        """
        Starts the continuous worker loop until stopped or max_cycles reached.
        """
        logger.info(
            "Starting 24/7 JARVIS Orchestrator Worker '%s' (poll_interval=%ss, lease=%ss, heartbeat=%ss)",
            self.worker_id,
            self.poll_interval,
            self.lease_seconds,
            self.heartbeat_interval,
        )
        self.register_signal_handlers()

        # Record persistent worker startup
        try:
            with self.get_session() as db:
                record_worker_lifecycle(
                    db,
                    worker_id=self.worker_id,
                    event_type="WORKER_STARTED",
                    details={
                        "pid": os.getpid(),
                        "poll_interval": self.poll_interval,
                        "heartbeat_interval": self.heartbeat_interval,
                        "lease_seconds": self.lease_seconds,
                        "timezone": getattr(self.timezone, "key", str(self.timezone)),
                    },
                    organization_id=get_internal_org_id(),
                )
        except Exception as exc:
            logger.debug("Failed to record worker startup: %s", exc)

        try:
            while not self.stop_event.is_set():
                if self.max_cycles is not None and self.cycles_completed >= self.max_cycles:
                    logger.info("Worker reached max_cycles limit (%s). Terminating.", self.max_cycles)
                    break

                try:
                    cycle_result = self.run_cycle()
                    # If no tasks processed, sleep for poll_interval
                    if cycle_result.get("tasks_processed", 0) == 0:
                        self.stop_event.wait(self.poll_interval)
                except Exception as exc:
                    logger.error("Unhandled exception in worker cycle: %s", exc, exc_info=True)
                    try:
                        with self.get_session() as db:
                            record_worker_lifecycle(
                                db,
                                worker_id=self.worker_id,
                                event_type="WORKER_ERROR",
                                details={"error": f"{type(exc).__name__}: {str(exc)}"},
                                organization_id=get_internal_org_id(),
                            )
                    except Exception:
                        pass
                    self.stop_event.wait(self.poll_interval)
        finally:
            # Record persistent worker shutdown
            try:
                with self.get_session() as db:
                    record_worker_lifecycle(
                        db,
                        worker_id=self.worker_id,
                        event_type="WORKER_STOPPED",
                        details={
                            "uptime_seconds": int((datetime.now(timezone.utc) - self.start_time).total_seconds()),
                            "cycles_completed": self.cycles_completed,
                            "tasks_processed": self.tasks_processed,
                        },
                        organization_id=get_internal_org_id(),
                    )
            except Exception as exc:
                logger.debug("Failed to record worker shutdown: %s", exc)

        logger.info(
            "JARVIS Worker '%s' shut down cleanly. Cycles: %s, Tasks processed: %s",
            self.worker_id,
            self.cycles_completed,
            self.tasks_processed,
        )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )
    parser = argparse.ArgumentParser(description="LeadVoix Business JARVIS 24/7 Orchestrator Worker")
    parser.add_argument("command", nargs="?", default="process", help="Worker execution mode (default: process)")
    parser.add_argument("--worker-id", type=str, help="Custom identifier for this worker instance")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="Polling interval in seconds when idle")
    parser.add_argument("--heartbeat-interval", type=float, default=30.0, help="Heartbeat persistence interval in seconds")
    parser.add_argument("--max-cycles", type=int, default=None, help="Terminate after N cycles (for testing)")
    parser.add_argument("--once", action="store_true", help="Run exactly one cycle and exit")
    parser.add_argument("--timezone", type=str, default=None, help="Configured timezone (e.g. Asia/Kolkata, UTC, America/New_York)")
    args = parser.parse_args()

    max_cycles = 1 if args.once else args.max_cycles
    worker = JarvisOrchestratorWorker(
        worker_id=args.worker_id,
        poll_interval=args.poll_interval,
        heartbeat_interval=args.heartbeat_interval,
        max_cycles=max_cycles,
        timezone_name=args.timezone,
    )
    worker.run()


if __name__ == "__main__":
    main()
