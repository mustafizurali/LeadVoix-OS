import argparse
import logging
import os
import signal
import socket
import sys
import threading
import uuid
from typing import Callable, Optional

from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal, engine
from backend.app.services.call_processing_worker import (
    WorkerOutcome,
    run_worker_cycle,
    reap_stale_dead_letter_jobs,
)

logger = logging.getLogger("leadvoix.worker")


class CallProcessingWorker:
    """
    Dedicated persistent background worker for LeadVoix AI Voice-to-CRM automation.
    Continuously polls the call_processing_jobs table, executes AI intelligence analysis,
    updates CRM entities, creates follow-up tasks, automates deal pipelines, and manages
    job leases, retries, and dead-letter transitions independently of webhooks.
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        poll_interval: Optional[float] = None,
        job_type: str = "call_intelligence",
        lease_seconds: int = 300,
        heartbeat_interval_seconds: float = 30.0,
        max_cycles: Optional[int] = None,
        db_factory: Callable[[], Session] = SessionLocal,
    ):
        hostname = socket.gethostname() or "worker"
        pid = os.getpid()
        random_suffix = uuid.uuid4().hex[:6]

        self.worker_id = (
            worker_id
            or os.getenv("WORKER_ID")
            or f"call-worker-{hostname}-{pid}-{random_suffix}"
        )

        raw_poll = (
            poll_interval
            if poll_interval is not None
            else float(os.getenv("WORKER_POLL_INTERVAL_SECONDS", "5.0"))
        )
        self.poll_interval = max(0.1, float(raw_poll))

        self.job_type = job_type or os.getenv("WORKER_JOB_TYPE", "call_intelligence")
        self.lease_seconds = int(os.getenv("WORKER_LEASE_SECONDS", str(lease_seconds)))
        self.heartbeat_interval_seconds = float(
            os.getenv("WORKER_HEARTBEAT_INTERVAL_SECONDS", str(heartbeat_interval_seconds))
        )
        self.max_cycles = max_cycles
        self.db_factory = db_factory

        self.stop_event = threading.Event()
        self.cycles_completed = 0
        self.jobs_processed = 0

    def register_signal_handlers(self) -> None:
        """Registers OS signal handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self._handle_signal)
            except (ValueError, AttributeError) as exc:
                logger.debug("Signal %s could not be registered: %s", sig, exc)

        # On Windows, register SIGBREAK if available
        if hasattr(signal, "SIGBREAK"):
            try:
                signal.signal(signal.SIGBREAK, self._handle_signal)
            except (ValueError, AttributeError):
                pass

    def _handle_signal(self, signum: int, frame) -> None:
        sig_name = (
            signal.Signals(signum).name
            if hasattr(signal, "Signals") and signum in signal.Signals._value2member_map_
            else str(signum)
        )
        logger.info(
            "Worker '%s' received shutdown signal (%s). Initiating graceful termination...",
            self.worker_id,
            sig_name,
        )
        self.stop()

    def stop(self) -> None:
        """Signals the worker loop to stop after the current cycle."""
        self.stop_event.set()

    def reap_dead_letters(self) -> int:
        """Scans for expired jobs that exceeded max_attempts and moves them to dead_letter."""
        db = self.db_factory()
        try:
            return reap_stale_dead_letter_jobs(db, job_type=self.job_type)
        except Exception as exc:
            logger.warning("Error reaping dead letter jobs: %s", type(exc).__name__)
            return 0
        finally:
            db.close()

    def run_once(self) -> WorkerOutcome:
        """
        Executes a single claim-and-process cycle.
        Returns the resulting WorkerOutcome.
        """
        try:
            outcome = run_worker_cycle(
                worker_id=self.worker_id,
                db_factory=self.db_factory,
                job_type=self.job_type,
                lease_seconds=self.lease_seconds,
                heartbeat_interval_seconds=self.heartbeat_interval_seconds,
            )

            if outcome == WorkerOutcome.SUCCESS:
                self.jobs_processed += 1
                logger.info("Worker '%s' successfully completed job cycle.", self.worker_id)
            elif outcome == WorkerOutcome.ALREADY_PROCESSED:
                self.jobs_processed += 1
                logger.info(
                    "Worker '%s' completed job cycle: job was already processed.",
                    self.worker_id,
                )
            elif outcome == WorkerOutcome.EMPTY_TRANSCRIPT:
                self.jobs_processed += 1
                logger.info(
                    "Worker '%s' completed job cycle: empty transcript handled.",
                    self.worker_id,
                )
            elif outcome == WorkerOutcome.RETRYABLE_FAILURE:
                logger.warning(
                    "Worker '%s' encountered retryable failure. Job rescheduled with backoff.",
                    self.worker_id,
                )
            elif outcome == WorkerOutcome.PERMANENT_FAILURE:
                logger.error(
                    "Worker '%s' encountered permanent failure. Job moved to dead-letter.",
                    self.worker_id,
                )
            elif outcome == WorkerOutcome.FENCE_LOST:
                logger.warning(
                    "Worker '%s' fence lost (lease expired or reclaimed). Changes rolled back safely.",
                    self.worker_id,
                )
            elif outcome == WorkerOutcome.NO_JOB_AVAILABLE:
                logger.debug("Worker '%s' found no eligible jobs.", self.worker_id)

            return outcome

        except Exception as exc:
            logger.error(
                "Worker '%s' encountered unexpected exception during execution cycle: %s",
                self.worker_id,
                type(exc).__name__,
            )
            return WorkerOutcome.RETRYABLE_FAILURE

    def run(self) -> None:
        """
        Main worker polling loop. Runs continuously until stop_event is set
        or max_cycles is reached.
        """
        logger.info(
            "LeadVoix persistent worker starting [worker_id=%s, pid=%s, poll_interval=%.1fs, job_type=%s, lease_seconds=%ss]",
            self.worker_id,
            os.getpid(),
            self.poll_interval,
            self.job_type,
            self.lease_seconds,
        )

        try:
            while not self.stop_event.is_set():
                outcome = self.run_once()
                self.cycles_completed += 1

                if self.max_cycles is not None and self.cycles_completed >= self.max_cycles:
                    logger.info(
                        "Worker '%s' reached max_cycles limit (%s). Terminating loop.",
                        self.worker_id,
                        self.max_cycles,
                    )
                    break

                if self.stop_event.is_set():
                    break

                # If no job was available, sleep for the full poll interval (interruptible)
                if outcome == WorkerOutcome.NO_JOB_AVAILABLE:
                    self.stop_event.wait(self.poll_interval)
                else:
                    # If a job was processed or failed, yield briefly to check for immediately pending jobs
                    drain_pause = min(0.1, self.poll_interval)
                    self.stop_event.wait(drain_pause)

        finally:
            logger.info(
                "LeadVoix persistent worker '%s' stopping. Cycles completed: %s, Jobs processed: %s.",
                self.worker_id,
                self.cycles_completed,
                self.jobs_processed,
            )
            self._cleanup()

    def _cleanup(self) -> None:
        """Safely cleans up database connection pools and resources on shutdown."""
        try:
            if hasattr(engine, "dispose"):
                engine.dispose()
                logger.info("Worker '%s' database connection pool disposed safely.", self.worker_id)
        except Exception as exc:
            logger.warning("Error disposing database engine on worker shutdown: %s", exc)


def main() -> None:
    """CLI entrypoint for running the standalone worker process."""
    parser = argparse.ArgumentParser(
        description="LeadVoix OS Persistent Call Processing Background Worker"
    )
    parser.add_argument(
        "--worker-id",
        type=str,
        default=None,
        help="Unique identifier for this worker instance (defaults to auto-generated ID)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=None,
        help="Queue polling interval in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--job-type",
        type=str,
        default="call_intelligence",
        help="Job type to process (default: call_intelligence)",
    )
    parser.add_argument(
        "--lease-seconds",
        type=int,
        default=300,
        help="Job lease lock duration in seconds (default: 300)",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        help="Maximum polling cycles to execute before exiting (useful for testing or batch recycling)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    worker = CallProcessingWorker(
        worker_id=args.worker_id,
        poll_interval=args.poll_interval,
        job_type=args.job_type,
        lease_seconds=args.lease_seconds,
        max_cycles=args.max_cycles,
    )

    worker.register_signal_handlers()

    try:
        worker.run()
    except Exception as exc:
        logger.critical("Fatal worker exception: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
