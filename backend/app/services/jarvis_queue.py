"""
LeadVoix Business JARVIS — Persistent Task Queue Service
Phase B Core Orchestration

Responsibilities:
- Atomic task claiming using SELECT FOR UPDATE SKIP LOCKED.
- Leased execution with heartbeat and crash recovery.
- Retry with exponential backoff and dead-letter queue (DLQ) transitions.
- Concurrency control across multiple worker instances.
- Comprehensive task attempt auditing.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from backend.app.models.jarvis import JarvisTask, JarvisTaskAttempt


logger = logging.getLogger("leadvoix.jarvis.queue")

DEFAULT_LEASE_SECONDS = 300
DEFAULT_BASE_BACKOFF_SECONDS = 30
MAX_BACKOFF_SECONDS = 3600


class JarvisQueueManager:
    """
    Manages durable task queues, leases, retries, and dead-letter transitions in the 'jarvis' schema.
    """

    @staticmethod
    def enqueue_task(
        db: Session,
        task_type: str,
        payload: Dict[str, Any],
        organization_id: int = 1,
        run_at: Optional[datetime] = None,
        max_attempts: int = 3,
        idempotency_key: Optional[str] = None,
    ) -> JarvisTask:
        """
        Enqueues a new operational task in the persistent queue.
        If idempotency_key is provided and already exists, returns the existing task
        without creating duplicate rows.
        """
        now = datetime.now(timezone.utc)
        target_run_at = run_at or now

        if idempotency_key:
            existing = (
                db.query(JarvisTask)
                .filter(JarvisTask.idempotency_key == idempotency_key)
                .first()
            )
            if existing:
                logger.info(
                    "Task with idempotency_key '%s' already exists (#%s, status: %s). Duplicate suppressed.",
                    idempotency_key,
                    existing.id,
                    existing.status,
                )
                return existing

        task = JarvisTask(
            task_type=task_type,
            idempotency_key=idempotency_key,
            status="pending",
            organization_id=organization_id,
            payload=payload,
            attempts=0,
            max_attempts=max_attempts,
            next_run_at=target_run_at,
            created_at=now,
            updated_at=now,
        )
        try:
            db.add(task)
            db.commit()
            db.refresh(task)
            logger.info("Enqueued JARVIS task #%s (%s) for org #%s", task.id, task_type, organization_id)
            return task
        except Exception as exc:
            db.rollback()
            if idempotency_key:
                existing = (
                    db.query(JarvisTask)
                    .filter(JarvisTask.idempotency_key == idempotency_key)
                    .first()
                )
                if existing:
                    return existing
            raise exc

    @staticmethod
    def claim_next_task(
        db: Session,
        worker_id: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> Optional[JarvisTask]:
        """
        Atomically claims the next eligible task using SELECT FOR UPDATE SKIP LOCKED.
        Prevents multiple workers from grabbing the same task simultaneously.
        """
        now = datetime.now(timezone.utc)
        query = (
            db.query(JarvisTask)
            .filter(
                JarvisTask.status == "pending",
                JarvisTask.next_run_at <= now,
                JarvisTask.attempts < JarvisTask.max_attempts,
            )
            .order_by(JarvisTask.next_run_at.asc(), JarvisTask.id.asc())
            .with_for_update(skip_locked=True)
        )

        task = query.first()
        if not task:
            return None

        claim_token = str(uuid.uuid4())
        task.status = "claimed"
        task.claim_token = claim_token
        task.locked_by = worker_id
        task.locked_at = now
        task.lease_expires_at = now + timedelta(seconds=lease_seconds)
        task.attempts += 1
        task.updated_at = now

        db.commit()
        db.refresh(task)
        logger.info(
            "Worker '%s' claimed task #%s (%s), attempt %s/%s (lease expires in %ss)",
            worker_id,
            task.id,
            task.task_type,
            task.attempts,
            task.max_attempts,
            lease_seconds,
        )
        return task

    @staticmethod
    def record_attempt(
        db: Session,
        task_id: int,
        worker_instance: str,
        attempt_number: int,
        status: str,
        duration_ms: Optional[int] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> JarvisTaskAttempt:
        """Records an execution attempt for auditing and performance tracking."""
        now = datetime.now(timezone.utc)
        attempt = JarvisTaskAttempt(
            task_id=task_id,
            attempt_number=attempt_number,
            worker_instance=worker_instance,
            status=status,
            error_type=error_type,
            error_message=error_message,
            duration_ms=duration_ms,
            started_at=now if status == "started" else now - timedelta(milliseconds=duration_ms or 0),
            finished_at=now if status != "started" else None,
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def complete_task(
        db: Session,
        task_id: int,
        claim_token: str,
    ) -> bool:
        """Marks a task as successfully completed if claim token matches."""
        now = datetime.now(timezone.utc)
        task = db.query(JarvisTask).filter(JarvisTask.id == task_id).first()
        if not task or task.claim_token != claim_token:
            logger.warning(
                "Failed to complete task #%s: claim token mismatch or task missing",
                task_id,
            )
            return False

        task.status = "completed"
        task.claim_token = None
        task.locked_by = None
        task.locked_at = None
        task.lease_expires_at = None
        task.updated_at = now
        db.commit()
        logger.info("Task #%s marked COMPLETED", task_id)
        return True

    @staticmethod
    def fail_task(
        db: Session,
        task_id: int,
        claim_token: str,
        error_message: str,
        base_backoff_seconds: int = DEFAULT_BASE_BACKOFF_SECONDS,
    ) -> bool:
        """
        Transitions a failed task to either retry with exponential backoff or dead_letter.
        """
        now = datetime.now(timezone.utc)
        task = db.query(JarvisTask).filter(JarvisTask.id == task_id).first()
        if not task or task.claim_token != claim_token:
            logger.warning(
                "Failed to update failed state for task #%s: token mismatch",
                task_id,
            )
            return False

        task.last_error = error_message[:2000]
        task.claim_token = None
        task.locked_by = None
        task.locked_at = None
        task.lease_expires_at = None
        task.updated_at = now

        if task.attempts >= task.max_attempts:
            task.status = "dead_letter"
            logger.error(
                "Task #%s reached max attempts (%s/%s). Moved to DEAD_LETTER: %s",
                task_id,
                task.attempts,
                task.max_attempts,
                error_message[:120],
            )
        else:
            # Exponential backoff: base * 2^(attempts - 1)
            backoff_exp = max(0, task.attempts - 1)
            backoff_seconds = min(MAX_BACKOFF_SECONDS, base_backoff_seconds * (2 ** backoff_exp))
            task.status = "pending"
            task.next_run_at = now + timedelta(seconds=backoff_seconds)
            logger.warning(
                "Task #%s failed (attempt %s/%s). Scheduled retry in %ss (at %s)",
                task_id,
                task.attempts,
                task.max_attempts,
                backoff_seconds,
                task.next_run_at.isoformat(),
            )

        db.commit()
        return True

    @staticmethod
    def renew_lease(
        db: Session,
        task_id: int,
        claim_token: str,
        extension_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> bool:
        """Extends the lease duration for an active in-flight task (heartbeat)."""
        now = datetime.now(timezone.utc)
        task = db.query(JarvisTask).filter(JarvisTask.id == task_id).first()
        if not task or task.claim_token != claim_token:
            return False

        task.lease_expires_at = now + timedelta(seconds=extension_seconds)
        task.updated_at = now
        db.commit()
        return True

    @staticmethod
    def reap_expired_leases(
        db: Session,
        now: Optional[datetime] = None,
    ) -> int:
        """
        Reclaims abandoned or crashed tasks whose lease has expired.
        Transitions tasks to pending for retry or dead_letter if max attempts exhausted.
        """
        ref_time = now or datetime.now(timezone.utc)
        expired_tasks = (
            db.query(JarvisTask)
            .filter(
                JarvisTask.status.in_(["claimed", "executing"]),
                JarvisTask.lease_expires_at <= ref_time,
            )
            .with_for_update(skip_locked=True)
            .all()
        )

        reclaimed_count = 0
        for task in expired_tasks:
            logger.warning(
                "Reclaiming abandoned task #%s (locked by '%s', lease expired at %s)",
                task.id,
                task.locked_by,
                task.lease_expires_at,
            )
            task.claim_token = None
            task.locked_by = None
            task.locked_at = None
            task.lease_expires_at = None
            task.updated_at = ref_time

            if task.attempts >= task.max_attempts:
                task.status = "dead_letter"
                task.last_error = f"Lease expired after {task.attempts} attempts without completion."
            else:
                task.status = "pending"
                task.last_error = f"Lease expired while claimed. Reclaimed for retry."
            reclaimed_count += 1

        if reclaimed_count > 0:
            db.commit()
            logger.info("Successfully reclaimed %s expired task(s)", reclaimed_count)

        return reclaimed_count
