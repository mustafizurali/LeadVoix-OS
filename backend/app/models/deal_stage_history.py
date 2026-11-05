from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.database import Base


class DealStageHistory(Base):
    __tablename__ = "deal_stage_history"

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

    deal_id = Column(
        Integer,
        ForeignKey("deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_stage_id = Column(
        Integer,
        ForeignKey("pipeline_stages.id", ondelete="SET NULL"),
        nullable=True,
    )

    to_stage_id = Column(
        Integer,
        ForeignKey("pipeline_stages.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    entered_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    exited_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    duration_seconds = Column(
        Integer,
        nullable=True,
    )

    changed_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    entry_type = Column(
        String(30),
        nullable=False,
        default="transition",
    )

    is_verified_transition = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    organization = relationship(
        "Organization",
    )

    deal = relationship(
        "Deal",
        backref="stage_history",
    )

    from_stage = relationship(
        "PipelineStage",
        foreign_keys=[from_stage_id],
    )

    to_stage = relationship(
        "PipelineStage",
        foreign_keys=[to_stage_id],
    )

    changed_by = relationship(
        "User",
        foreign_keys=[changed_by_user_id],
    )
