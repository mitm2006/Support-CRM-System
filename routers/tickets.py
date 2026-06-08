"""
routers/tickets.py
------------------
All REST API endpoints for the Datastraw CRM ticket system.

Endpoints:
  POST   /api/tickets             — Create a new ticket
  GET    /api/tickets             — List tickets (filterable by status & search)
  GET    /api/tickets/{id}        — Get full ticket detail with notes
  PUT    /api/tickets/{id}        — Update status and/or add a note

Design for expansion:
  - Add DELETE /api/tickets/{id} or PATCH endpoints without restructuring.
  - Add pagination via `skip` / `limit` query params — slots already noted.
  - Auth middleware can be injected as an additional `Depends()` on the router.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from models import Note, Ticket
from schemas import (
    TicketCreate,
    TicketCreated,
    TicketDetail,
    TicketListItem,
    TicketUpdate,
    TicketUpdated,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _get_ticket_or_404(ticket_id: int, db: Session) -> Ticket:
    """Fetch ticket by integer PK; raise 404 if not found."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with id={ticket_id} not found.",
        )
    return ticket


# ---------------------------------------------------------------------------
# POST /api/tickets — Create Ticket
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=TicketCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket",
)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)) -> TicketCreated:
    """
    Create a new ticket. The database assigns the auto-incrementing `id`
    atomically — no race conditions on concurrent inserts.
    """
    ticket = Ticket(
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        subject=payload.subject,
        description=payload.description,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return TicketCreated(
        id=ticket.id,
        ticket_id=ticket.ticket_id,
        created_at=ticket.created_at,
    )


# ---------------------------------------------------------------------------
# GET /api/tickets — List Tickets
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=list[TicketListItem],
    summary="List all tickets with optional search and status filter",
)
def list_tickets(
    search: str | None = Query(None, description="Search name, email, subject, description, or TKT-NNN"),
    filter_status: str | None = Query(None, alias="status", description="Filter by: Open | In Progress | Closed"),
    # Pagination slots — ready for future use
    # skip: int = Query(0, ge=0),
    # limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[TicketListItem]:
    """
    Returns list of tickets. Supports:
      - Full-text search across name, email, subject, description
      - Parsing "TKT-NNN" or plain number to search by ID
      - Status filter
    """
    query = db.query(Ticket)

    # Status filter
    if filter_status:
        valid = {"Open", "In Progress", "Closed"}
        if filter_status not in valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status. Must be one of: {sorted(valid)}",
            )
        query = query.filter(Ticket.status == filter_status)

    # Search filter
    if search:
        # Support "TKT-001" → search by id=1
        numeric_id = None
        cleaned = search.strip().upper()
        if cleaned.startswith("TKT-"):
            try:
                numeric_id = int(cleaned[4:])
            except ValueError:
                pass
        elif search.strip().isdigit():
            numeric_id = int(search.strip())

        conditions = [
            Ticket.customer_name.ilike(f"%{search}%"),
            Ticket.customer_email.ilike(f"%{search}%"),
            Ticket.subject.ilike(f"%{search}%"),
            Ticket.description.ilike(f"%{search}%"),
        ]
        if numeric_id is not None:
            conditions.append(Ticket.id == numeric_id)

        query = query.filter(or_(*conditions))

    tickets = query.order_by(Ticket.created_at.desc()).all()

    return [
        TicketListItem(
            id=t.id,
            ticket_id=t.ticket_id,
            customer_name=t.customer_name,
            customer_email=t.customer_email,
            subject=t.subject,
            status=t.status,
            created_at=t.created_at,
        )
        for t in tickets
    ]


# ---------------------------------------------------------------------------
# GET /api/tickets/{id} — Ticket Detail
# ---------------------------------------------------------------------------
@router.get(
    "/{ticket_id}",
    response_model=TicketDetail,
    summary="Get full ticket detail including notes",
)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> TicketDetail:
    """Fetch a single ticket by integer ID with all associated notes."""
    ticket = _get_ticket_or_404(ticket_id, db)

    return TicketDetail(
        id=ticket.id,
        ticket_id=ticket.ticket_id,
        customer_name=ticket.customer_name,
        customer_email=ticket.customer_email,
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        notes=[
            {"id": n.id, "note_text": n.note_text, "created_at": n.created_at}
            for n in ticket.notes
        ],
    )


# ---------------------------------------------------------------------------
# PUT /api/tickets/{id} — Update Ticket
# ---------------------------------------------------------------------------
@router.put(
    "/{ticket_id}",
    response_model=TicketUpdated,
    summary="Update ticket status and/or add a note",
)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
) -> TicketUpdated:
    """
    Update ticket status and/or append a new note.
    At least one of `status` or `note_text` must be provided.
    """
    ticket = _get_ticket_or_404(ticket_id, db)

    if payload.status:
        ticket.status = payload.status

    if payload.note_text and payload.note_text.strip():
        note = Note(
            ticket_ref=ticket.id,
            note_text=payload.note_text.strip(),
        )
        db.add(note)

    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)

    return TicketUpdated(success=True, updated_at=ticket.updated_at)
