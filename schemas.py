"""
schemas.py
----------
Pydantic v2 request/response schemas for the Datastraw CRM API.

Each schema is documented with its intended use:
  - TicketCreate    : POST /api/tickets  — inbound
  - TicketUpdate    : PUT  /api/tickets/{id} — inbound
  - NoteOut         : Embedded note in responses
  - TicketListItem  : GET  /api/tickets  — lightweight list view
  - TicketDetail    : GET  /api/tickets/{id} — full detail view
  - TicketCreated   : POST response (201)
  - TicketUpdated   : PUT  response (200)

Design notes:
  - `ticket_id` is always the formatted "TKT-NNN" string, built from the
    ORM model's @property — never stored as a DB column.
  - All datetime fields are serialised as ISO-8601 strings via `model_config`.
  - Future schemas (e.g., AgentOut, CategoryOut) can be added without
    touching existing schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


# Shared config — applied to all ORM-backed models

class _CRMBase(BaseModel):
    model_config = {"from_attributes": True}



# Note schemas

class NoteOut(_CRMBase):
    id: int
    note_text: str
    created_at: datetime



# Ticket — inbound schemas

class TicketCreate(BaseModel):
    customer_name:  str   = Field(..., min_length=1, max_length=255, examples=["Rahul Sharma"])
    customer_email: EmailStr = Field(..., examples=["rahul@example.com"])
    subject:        str   = Field(..., min_length=1, max_length=500, examples=["Order not received"])
    description:    Optional[str] = Field(None, examples=["I placed order #1234 five days ago..."])


class TicketUpdate(BaseModel):
    status:    Optional[str] = Field(None, examples=["In Progress"])
    note_text: Optional[str] = Field(None, examples=["Escalated to warehouse team."])

    VALID_STATUSES: ClassVar[set[str]] = {"Open", "In Progress", "Closed"}

    @model_validator(mode="after")
    def at_least_one_field(self) -> "TicketUpdate":
        if self.status is None and self.note_text is None:
            raise ValueError("At least one of 'status' or 'note_text' must be provided.")
        if self.status is not None and self.status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{self.status}'. Must be one of: {sorted(self.VALID_STATUSES)}"
            )
        return self



# Ticket — outbound schemas

class TicketListItem(_CRMBase):
    """Lightweight representation used in the ticket list dashboard."""
    id:            int
    ticket_id:     str          # derived from @property on ORM model
    customer_name: str
    customer_email: str
    subject:       str
    status:        str
    created_at:    datetime


class TicketDetail(_CRMBase):
    """Full ticket representation including all notes."""
    id:             int
    ticket_id:      str
    customer_name:  str
    customer_email: str
    subject:        str
    description:    Optional[str]
    status:         str
    created_at:     datetime
    updated_at:     datetime
    notes:          list[NoteOut] = []



# Action response schemas

class TicketCreated(BaseModel):
    """Response body for a successfully created ticket (201)."""
    id:         int
    ticket_id:  str
    created_at: datetime


class TicketUpdated(BaseModel):
    """Response body for a successfully updated ticket (200)."""
    success:    bool = True
    updated_at: datetime
