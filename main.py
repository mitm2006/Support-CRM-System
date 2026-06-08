"""
main.py
-------
FastAPI application entry point for the Datastraw CRM.

Responsibilities:
  - Create the FastAPI app with metadata
  - Create all DB tables on startup
  - Mount static file directory and Jinja2 templates
  - Register the /api/tickets router
  - Serve HTML template pages at clean URLs (/, /create, /detail)

Future expansion hooks:
  - Add middleware (CORS, auth, rate-limit) here
  - Register additional routers (e.g., /api/agents, /api/reports)
  - Add lifespan events for startup/shutdown tasks
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import models
from database import engine
from routers import tickets as tickets_router

# Create all database tables on startup (idempotent — safe to run repeatedly)

models.Base.metadata.create_all(bind=engine)


# App instance

app = FastAPI(
    title="Datastraw CRM",
    description="A lightweight customer support ticket management system.",
    version="1.0.0",
    redirect_slashes=False,   # Prevent 307 double-hop on /api/tickets vs /api/tickets/
)


# Static files and templates

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# API router

app.include_router(tickets_router.router, prefix="/api")



# Page routes — serve HTML templates at clean URLs

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    """Dashboard — ticket list page."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/create", response_class=HTMLResponse, include_in_schema=False)
async def create_page(request: Request):
    """New ticket form page."""
    return templates.TemplateResponse(request, "create.html")


@app.get("/detail", response_class=HTMLResponse, include_in_schema=False)
async def detail_page(request: Request):
    """Ticket detail and notes page."""
    return templates.TemplateResponse(request, "detail.html")
