# Datastraw CRM

A lightweight customer support ticket management system built with **FastAPI**, **SQLite**, and **Tailwind CSS**, deployed on **Railway**.

---

## Live URL

> 🔗 https://web-production-2ee9c7.up.railway.app/

---

## Features

| Feature | Status |
|---------|--------|
| Create ticket with auto-generated TKT-ID | ✅ |
| List all tickets in a responsive dashboard | ✅ |
| Live search (name, email, ID, subject, description) | ✅ |
| Filter by Open / In Progress / Closed | ✅ |
| View full ticket detail | ✅ |
| Update ticket status via dropdown | ✅ |
| Add agent notes to a ticket (bonus) | ✅ |
| Mobile-responsive layout | ✅ |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy ORM |
| Database | SQLite (file-based, ephemeral on Railway) |
| Templates | Jinja2 |
| Frontend | HTML5, Tailwind CSS (CDN), Vanilla JS |
| Deployment | Railway.app |

---

## Project Structure

```
Support-CRM-System/
├── routers/
│   └── tickets.py      # REST API endpoints (/api/tickets)
├── static/js/
│   ├── tickets.js      # Dashboard: search, filter, table render
│   ├── create.js       # New ticket form logic
│   └── detail.js       # Detail view: notes, status updates
├── templates/
│   ├── index.html      # Support dashboard (ticket list)
│   ├── create.html     # New ticket form
│   └── detail.html     # Ticket detail + notes timeline
├── database.py         # SQLAlchemy engine + get_db() helper
├── models.py           # ORM models: Ticket, Note
├── schemas.py          # Pydantic schemas (request/response)
├── main.py             # FastAPI app entry point
├── Procfile            # Railway deployment
├── requirements.txt    # Python dependencies
└── .env.example        # Environment variable template
```

---

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/Support-CRM-System.git
cd datastraw-crm

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the development server
uvicorn main:app --reload

# 5. Open in browser
# http://localhost:8000          ← Dashboard
# http://localhost:8000/docs     ← Interactive API docs (Swagger)
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/tickets` | Create a new ticket |
| `GET`  | `/api/tickets` | List tickets (filter & search) |
| `GET`  | `/api/tickets/{id}` | Get ticket detail + notes |
| `PUT`  | `/api/tickets/{id}` | Update status / add note |

### Query Parameters (GET /api/tickets)

| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Searches name, email, subject, description, TKT-NNN |
| `status` | string | Filter: `Open` \| `In Progress` \| `Closed` |

---

## Design Decisions

- **Auto-increment IDs**: The `tickets.id` primary key is assigned by SQLite atomically, preventing any race conditions. The `TKT-NNN` display ID is derived as a Python property — no extra column.
- **Notes FK**: The `notes` table references `tickets.id` (integer FK) for efficient indexing and easy future joins.
- **Monolith pattern**: FastAPI serves both HTML pages and the REST API in one process — keeps Railway deployment dead simple.

---

## Known Limitations (MVP)

- SQLite data resets on Railway redeploy (ephemeral disk). For persistent data, swap to Railway's PostgreSQL plugin.
- No authentication — all users have full access. Auth can be added as FastAPI middleware.
- No pagination — fine for the assessment volume, slots exist in the code to add it.

---

