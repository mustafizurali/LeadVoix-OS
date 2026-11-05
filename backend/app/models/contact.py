from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String, nullable=False)

    last_name = Column(String, nullable=True)

    email = Column(String, nullable=True)

    phone = Column(String, nullable=True)
    phone_normalized = Column(String(32), nullable=True, index=True)
    phone_extension = Column(String(10), nullable=True)

    company = Column(String, nullable=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    lead_id = Column(
        Integer,
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status = Column(
        String,
        nullable=False,
        default="new",
    )

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
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
        back_populates="contacts",
    )

    deals = relationship(
        "Deal",
        back_populates="contact",
    )

    tasks = relationship(
        "Task",
        back_populates="contact",
    )

    owner = relationship(
        "User",
        foreign_keys=[owner_id],
    )

    company_rel = relationship(
        "Company",
        back_populates="contacts",
        foreign_keys=[company_id],
    )

    lead = relationship(
        "Lead",
        foreign_keys=[lead_id],
    )
