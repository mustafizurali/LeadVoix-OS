from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    provider = Column(
        String,
        nullable=False,
        default="razorpay",
    )

    provider_subscription_id = Column(
        String,
        nullable=True,
        unique=True,
        index=True,
    )

    plan = Column(
        String,
        nullable=False,
    )

    status = Column(
        String,
        nullable=False,
        default="created",
    )

    current_period_start = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    current_period_end = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancel_at_period_end = Column(
      Boolean,
      nullable=False,
      default=False,
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

    organization = relationship(
        "Organization",
        back_populates="subscriptions",
    )