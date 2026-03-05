"""
tests/conftest.py
-----------------
pytest configuration — provides an in-memory SQLite DB session fixture
seeded with minimal representative data for fast unit tests.
"""

import sys
import os
import pytest
from datetime import datetime, timedelta

# Make dashboard/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dashboard"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Risk, Control, AuditFinding, User
import bcrypt


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    # Seed minimal data
    r = Risk(
        risk_id="R-01", risk_description="Test risk", asset="Test Asset",
        threat="Test Threat", vulnerability="Test Vuln",
        impact=4, likelihood=4, risk_score=16, risk_level="Critical",
        treatment_status="In Progress", iso_clause="A.9.4", nist_function="Protect",
    )
    session.add(r)
    session.flush()

    c = Control(
        control_id="C-01", control_name="Test Control",
        mapped_risk_id="R-01", control_type="Preventive",
        implementation_status="Partial", effectiveness="Needs Improvement",
        iso_clause="A.9.4", nist_function="Protect",
        risk_level_after_control="High",
    )
    session.add(c)

    f = AuditFinding(
        finding_id="F-01", risk_id="R-01", control_id="C-01",
        title="Test Finding", severity="Critical",
        status="Open", due_date=datetime.utcnow() - timedelta(days=10),
        owner="Test Owner",
    )
    session.add(f)

    u = User(
        username="testadmin",
        hashed_password=bcrypt.hashpw(b"password", bcrypt.gensalt()).decode(),
        role="admin",
    )
    session.add(u)
    session.flush()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
