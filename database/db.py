"""
database/db.py
--------------
Database engine, session factory, and initialisation helpers.
DATABASE_URL can be overridden via a .env file:
    DATABASE_URL=postgresql+psycopg2://user:pass@host/dbname
Defaults to a local SQLite file: backend/grc.db
"""

import os
import sys
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
    """
    Create all tables if they do not already exist, then auto-seed
    default users and GRC data if the database is empty.

    This ensures Streamlit Cloud deployments work on first boot
    without requiring grc.db to be committed to the repository.
    """
    Base.metadata.create_all(bind=engine)
    _auto_seed_if_empty()


def _auto_seed_if_empty() -> None:
    """Seed the database with default data if no users exist yet."""
    db = SessionLocal()
    try:
        from database.models import User  # noqa: PLC0415
        if db.query(User).count() == 0:
            # Add the project root to sys.path so database.seed is importable
            _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if _project_root not in sys.path:
                sys.path.insert(0, _project_root)
            from database.seed import seed  # noqa: PLC0415
            seed()
    except Exception as exc:  # noqa: BLE001
        # Seeding failure is non-fatal — app boots, login will show an error
        print(f"[auto-seed] warning: {exc}")
    finally:
        db.close()


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
