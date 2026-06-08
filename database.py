"""
database.py
-----------
SQLAlchemy database engine setup, session factory, and the get_db()
dependency used by all FastAPI route handlers.

Designed for future expansion:
  - Swap SQLALCHEMY_DATABASE_URL to PostgreSQL/MySQL by changing one line.
  - add_engine_kwargs can be extended (e.g., pool_size, max_overflow).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Connection URL — SQLite for MVP, easily swapped for Postgres in production

SQLALCHEMY_DATABASE_URL = "sqlite:///./crm.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # Required for SQLite when used with FastAPI's threading model
    connect_args={"check_same_thread": False},
)

# Session factory — autocommit/autoflush off for explicit transaction control
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Shared declarative base for all ORM models
Base = declarative_base()



# FastAPI dependency: yields a DB session and always closes it after use

def get_db():
    """Provide a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
