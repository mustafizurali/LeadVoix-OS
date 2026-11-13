"""
LeadVoix Business JARVIS — Immutable Operational Audit Ledger
Phase B Core Safeguard

Responsibilities:
- Append-only recording of all JARVIS actions, task state transitions, and founder approvals.
- Zero update or delete operations exposed.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.models.jarvis import JarvisAuditLog


logger = logging.getLogger("leadvoix.jarvis.audit")

DEFAULT_STALE_HEARTBEAT_THRESHOLD_SECONDS = 90


def record_audit_event(
    db: Session,
    event_type: str,
    details: Dict[str, Any],
    actor: str = "jarvis_worker",
    organization_id: int = 1,
) -> JarvisAuditLog:
    """
    Appends an immutable audit record to jarvis.audit_logs.
    """
    now = datetime.now(timezone.utc)
    log_entry = JarvisAuditLog(
        event_type=event_type,
        actor=actor,
        organization_id=organization_id,
        details=details,
        created_at=now,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    logger.debug("Recorded JARVIS audit event: %s by %s", event_type, actor)
    return log_entry


def record_worker_heartbeat(
    db: Session,
    worker_id: str,
    status: str = "running",
    details: Optional[Dict[str, Any]] = None,
    organization_id: int = 1,
) -> JarvisAuditLog:
    """
    Appends a persistent worker heartbeat event to jarvis.audit_logs.
    Includes worker identity, operational status, and telemetry.
    """
    merged_details = {
        "worker_id": worker_id,
        "status": status,
        **(details or {}),
    }
    return record_audit_event(
        db,
        event_type="WORKER_HEARTBEAT",
        details=merged_details,
        actor=worker_id,
        organization_id=organization_id,
    )


def record_worker_lifecycle(
    db: Session,
    worker_id: str,
    event_type: str,
    details: Optional[Dict[str, Any]] = None,
    organization_id: int = 1,
) -> JarvisAuditLog:
    """
    Appends a persistent worker lifecycle event (WORKER_STARTED, WORKER_STOPPED, WORKER_ERROR).
    """
    merged_details = {
        "worker_id": worker_id,
        **(details or {}),
    }
    return record_audit_event(
        db,
        event_type=event_type,
        details=merged_details,
        actor=worker_id,
        organization_id=organization_id,
    )


def get_latest_worker_heartbeat(
    db: Session,
    worker_id: Optional[str] = None,
    organization_id: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    Retrieves the most recent worker heartbeat or lifecycle record from jarvis.audit_logs.
    Strictly SELECT-only query safe for read-only sessions.
    """
    query = (
        db.query(JarvisAuditLog)
        .filter(
            JarvisAuditLog.organization_id == organization_id,
            JarvisAuditLog.event_type.in_(["WORKER_HEARTBEAT", "WORKER_STARTED", "WORKER_STOPPED"]),
        )
    )
    if worker_id:
        query = query.filter(JarvisAuditLog.actor == worker_id)

    log_entry = query.order_by(JarvisAuditLog.created_at.desc(), JarvisAuditLog.id.desc()).first()
    if not log_entry:
        return None

    created_at = log_entry.created_at
    if created_at and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return {
        "id": log_entry.id,
        "event_type": log_entry.event_type,
        "actor": log_entry.actor,
        "details": log_entry.details or {},
        "created_at": created_at,
        "timestamp": created_at.isoformat() if created_at else None,
    }


def evaluate_worker_health(
    heartbeat_record: Optional[Dict[str, Any]],
    now: Optional[datetime] = None,
    stale_threshold_seconds: int = DEFAULT_STALE_HEARTBEAT_THRESHOLD_SECONDS,
) -> Tuple[str, Dict[str, Any]]:
    """
    Evaluates whether the worker is running, stale, stopped, or unavailable.
    Returns:
        (worker_status: str, metadata: Dict[str, Any])
        Possible statuses: "running", "stale", "stopped", "unavailable"
    """
    if not heartbeat_record:
        return "unavailable", {
            "status": "unavailable",
            "worker_id": None,
            "last_heartbeat": None,
            "details": None,
        }

    ref_time = now or datetime.now(timezone.utc)
    event_type = heartbeat_record.get("event_type")
    actor = heartbeat_record.get("actor")
    created_at = heartbeat_record.get("created_at")
    details = heartbeat_record.get("details") or {}

    if event_type == "WORKER_STOPPED":
        return "stopped", {
            "status": "stopped",
            "worker_id": actor,
            "last_heartbeat": created_at.isoformat() if created_at else None,
            "details": details,
        }

    if created_at:
        elapsed = (ref_time - created_at).total_seconds()
        if elapsed > stale_threshold_seconds:
            return "stale", {
                "status": "stale",
                "worker_id": actor,
                "last_heartbeat": created_at.isoformat(),
                "seconds_since_heartbeat": int(elapsed),
                "stale_threshold_seconds": stale_threshold_seconds,
                "details": details,
            }

    return "running", {
        "status": "running",
        "worker_id": actor,
        "last_heartbeat": created_at.isoformat() if created_at else None,
        "seconds_since_heartbeat": int((ref_time - created_at).total_seconds()) if created_at else 0,
        "details": details,
    }
