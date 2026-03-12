"""
database/migrate_add_resolved.py
---------------------------------
One-time migration: drops all tables and recreates them with the updated
treatment_status Enum that includes 'Resolved', then re-seeds the database.

Run:
    cd d:/grc-dashboard
    .venv/Scripts/python database/migrate_add_resolved.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import engine, Base
from database import models  # noqa: F401 — registers all models
from database.seed import seed

print("⚠️  Dropping all tables to apply Enum migration...")
Base.metadata.drop_all(bind=engine)
print("✅  Tables dropped.")

print("🔨 Recreating tables with updated schema...")
Base.metadata.create_all(bind=engine)
print("✅  Tables recreated.")

print("🌱 Re-seeding database...")
seed()
print("✅  Migration complete — 'Resolved' status is now available.")
