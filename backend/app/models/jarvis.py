"""
LeadVoix Business JARVIS — Phase B Operational Models
Isolated Schema: 'jarvis'

Tables:
- jarvis.jarvis_tasks            — Durable, concurrent, leased task queue
- jarvis.dispatch_idempotency    — Distributed multi-instance idempotency registry
- jarvis.task_attempts           — Execution audit log for worker runs
- jarvis.approval_records        — Founder human-in-the-loop authorization gates
- jarvis.audit_logs              — Immutable append-only operational ledger
"""

import uuid
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)

from backend.app.db.database import Base


class JarvisTask(Base):
    """
    Durable task queue supporting atomic claiming with SELECT FOR UPDATE SKIP LOCKED,
    lease-based heartbeat, retry with exponential backoff, and dead-letter queue.
    """
    __tablename__ = "jarvis_tasks"
    __table_args__ = (
        Index("ix_jarvis_tasks_claim", "status", "next_run_at", "lease_expires_at"),
        {"schema": "jarvis"},
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    task_type = Column(String(50), nullable=False, index=True)
    idempotency_key = Column(String(150), nullable=True, unique=True, index=True)
    status = Column(String(30), nullable=False, default="pending", index=True)
    organization_id = Column(Integer, nullable=False, default=1, index=True)
    payload = Column(JSON, nullable=False, default=dict)

    claim_token = Column(String(36), nullable=True, index=True)
    locked_by = Column(String(100), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    last_error = Column(Text, nullable=True)

    next_run_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())


class JarvisDispatchIdempotency(Base):
    """
    Multi-instance distributed idempotency registry.
    Guarantees two-phase dispatch reservation (in_flight -> completed / failed / crash_window_recovery)
    surviving restarts across multiple containers.
    """
    __tablename__ = "dispatch_idempotency"
    __table_args__ = (
        Index("ix_jarvis_dispatch_lookup", "organization_id", "digest_type", "window_date"),
        {"schema": "jarvis"},
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organization_id = Column(Integer, nullable=False, index=True)
    digest_type = Column(String(50), nullable=False)
    window_date = Column(Date, nullable=False)
    idempotency_key = Column(String(150), nullable=False, unique=True, index=True)

    status = Column(String(30), nullable=False, default="in_flight", index=True)
    claim_token = Column(String(36), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    telegram_message_id = Column(BigInteger().with_variant(Integer, "sqlite"), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    last_error = Column(JSON, nullable=True)
    cooldown_until = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class JarvisTaskAttempt(Base):
    """
    Individual execution history for a task attempt by a worker instance.
    """
    __tablename__ = "task_attempts"
    __table_args__ = (
        {"schema": "jarvis"},
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    task_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("jarvis.jarvis_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number = Column(Integer, nullable=False, default=1)
    worker_instance = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False)  # started, succeeded, failed
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)


class JarvisApprovalRecord(Base):
    """
    Cryptographically signed, expiring, replay-protected approval request for high-risk autonomous operations.
    """
    __tablename__ = "approval_records"
    __table_args__ = (
        Index("ix_jarvis_approval_status", "status", "expires_at"),
        {"schema": "jarvis"},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(BigInteger().with_variant(Integer, "sqlite"), nullable=True, index=True)
    action_type = Column(String(100), nullable=False, index=True)
    risk_tier = Column(String(20), nullable=False, default="high")  # low, medium, high, critical
    status = Column(String(30), nullable=False, default="pending", index=True)  # pending, approved, rejected, expired

    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    payload_preview = Column(JSON, nullable=False, default=dict)
    requested_by = Column(String(100), nullable=False, default="jarvis_autonomous_engine")
    responded_by = Column(String(100), nullable=True)

    requested_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)


class JarvisAuditLog(Base):
    """
    Immutable, append-only operational audit log for all JARVIS activities.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_jarvis_audit_created_at", "created_at"),
        Index("ix_jarvis_audit_event_type", "event_type"),
        {"schema": "jarvis"},
    )

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False, index=True)
    actor = Column(String(100), nullable=False, default="jarvis_worker")
    organization_id = Column(Integer, nullable=False, default=1, index=True)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
