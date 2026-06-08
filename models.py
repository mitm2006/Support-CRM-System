"""
models.py
---------
SQLAlchemy ORM model definitions for the Datastraw CRM.

Tables:
  - tickets : Core support ticket record
  - notes   : Agent notes linked to a ticket (1:N)

Design Notes:
  - `tickets.id` is the auto-incrementing PK — the DB assigns it atomically,
    eliminating any read-then-write race condition.
  - The human-readable `ticket_id` (e.g., "TKT-001") is a Python property
    derived from `id` at runtime — no extra column, no concurrency risk.
  - `notes.ticket_ref` is an integer FK to `tickets.id` for fast indexing.
  - Future tables (e.g., Agent, Category, AuditLog) can FK to `tickets.id`
    using the same pattern.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)



# Ticket model

class Ticket(Base):
    __tablename__ = "tickets"

    # Primary key — auto-incremented by SQLite; safe under concurrent inserts
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    customer_name  = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False, index=True)
    subject        = Column(String(500), nullable=False)
    description    = Column(Text, nullable=True)

    # Constrained to: "Open" | "In Progress" | "Closed"
    status = Column(String(20), nullable=False, default="Open", index=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    # Relationship to notes — cascade delete for referential integrity
    notes = relationship(
        "Note",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="Note.created_at",
    )

    
    # Computed human-readable ticket identifier — derived from PK, no DB column
    
    @property
    def ticket_id(self) -> str:
        """Return formatted ticket ID, e.g., 'TKT-001'."""
        return f"TKT-{self.id:03d}"

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} status={self.status!r}>"



# Note model

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Integer FK to tickets.id — reliable, fast, no string matching needed
    ticket_ref = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)

    note_text  = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # Back-reference to parent ticket
    ticket = relationship("Ticket", back_populates="notes")

    def __repr__(self) -> str:
        return f"<Note id={self.id} ticket_ref={self.ticket_ref}>"
