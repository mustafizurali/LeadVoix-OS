from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.database import Base


class Activity(Base):
    """
    Operational activity history model.
    Captures customer touchpoints (calls, emails, sms, notes, tasks, stage transitions).
    Preserves entity-level ON DELETE SET NULL behavior so operational audit trail
    is retained if child CRM records are deleted.
    """
    __tablename__ = "activities"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    activity_type = Column(
        String(50),
        nullable=False,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    content = Column(
        Text,
        nullable=True,
    )

    metadata_json = Column(
        Text,
        nullable=True,
    )

    # Entity pointers with safe non-destructive SET NULL behavior
    lead_id = Column(
        Integer,
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    deal_id = Column(
        Integer,
        ForeignKey("deals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    agent_call_id = Column(
        Integer,
        ForeignKey("agent_calls.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    organization = relationship(
        "Organization",
    )

    lead = relationship(
        "Lead",
        foreign_keys=[lead_id],
    )

    contact = relationship(
        "Contact",
        foreign_keys=[contact_id],
    )

    deal = relationship(
        "Deal",
        foreign_keys=[deal_id],
    )

    agent_call = relationship(
        "AgentCall",
        foreign_keys=[agent_call_id],
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
    )
