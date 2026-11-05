from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


class CallProcessingJob(Base):
    __tablename__ = "call_processing_jobs"

    id = Column(
        Integer,
        primary_key=True,
    )

    agent_call_id = Column(
        Integer,
        ForeignKey("agent_calls.id", ondelete="CASCADE"),
        nullable=False,
    )

    job_type = Column(
        String(50),
        nullable=False,
        default="call_intelligence",
        server_default="call_intelligence",
    )

    status = Column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    attempts = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    max_attempts = Column(
        Integer,
        nullable=False,
        default=3,
        server_default="3",
    )

    claim_token = Column(
        String(36),
        nullable=True,
        index=True,
    )

    locked_by = Column(
        String(100),
        nullable=True,
    )

    locked_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    lease_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    next_run_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    last_error = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    call = relationship(
        "AgentCall",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'dead_letter')",
            name="ck_call_processing_jobs_status",
        ),
        CheckConstraint(
            "attempts >= 0",
            name="ck_call_processing_jobs_attempts",
        ),
        CheckConstraint(
            "max_attempts > 0",
            name="ck_call_processing_jobs_max_attempts",
        ),
        CheckConstraint(
            "(status = 'processing' AND claim_token IS NOT NULL AND lease_expires_at IS NOT NULL) OR (status != 'processing')",
            name="ck_call_processing_jobs_processing_state",
        ),
        UniqueConstraint(
            "agent_call_id",
            name="uq_call_processing_jobs_agent_call_id",
        ),
        Index(
            "ix_call_processing_jobs_claim",
            "status",
            "next_run_at",
            "lease_expires_at",
        ),
    )
