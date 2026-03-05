"""
database/db.py
--------------
Database engine, session factory, and initialisation helpers.
DATABASE_URL can be overridden via a .env file:
    DATABASE_URL=postgresql+psycopg2://user:pass@host/dbname
Defaults to a local SQLite file: backend/grc.db
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from dotenv import load_dotenv

from database.models import Base

load_dotenv()

# ── Connection URL ────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_DB = f"sqlite:///{os.path.join(_BASE_DIR, 'backend', 'grc.db')}"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

# ── Engine ────────────────────────────────────────────────────────────────────
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Session:
    """Context manager that yields a DB session and handles commit/rollback."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
