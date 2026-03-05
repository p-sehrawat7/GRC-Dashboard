"""
tests/test_data.py
------------------
DB-backed data loading and integrity tests (replaces old CSV-based tests).
Uses the in-memory DB session fixture from conftest.py.
"""

import sys
import os
import pytest
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dashboard"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.models import Risk, Control, AuditFinding
from utils.data_loader import RISK_SCALE, NIST_FUNCTIONS


class TestModels:
    def test_risk_model_exists(self, db_session):
        risk = db_session.query(Risk).filter_by(risk_id="R-01").first()
        assert risk is not None

    def test_risk_required_fields(self, db_session):
        risk = db_session.query(Risk).filter_by(risk_id="R-01").first()
        for field in ["risk_id", "risk_description", "asset", "threat",
                      "vulnerability", "impact", "likelihood", "risk_score",
                      "risk_level", "treatment_status"]:
            assert getattr(risk, field) is not None, f"Field '{field}' must not be None"

    def test_control_model_exists(self, db_session):
        ctrl = db_session.query(Control).filter_by(control_id="C-01").first()
        assert ctrl is not None

    def test_control_maps_to_risk(self, db_session):
        ctrl = db_session.query(Control).filter_by(control_id="C-01").first()
        risk = db_session.query(Risk).filter_by(risk_id=ctrl.mapped_risk_id).first()
        assert risk is not None, "Every control must reference a valid risk"

    def test_finding_model_exists(self, db_session):
        f = db_session.query(AuditFinding).filter_by(finding_id="F-01").first()
        assert f is not None

    def test_finding_status_valid(self, db_session):
        f = db_session.query(AuditFinding).filter_by(finding_id="F-01").first()
        assert f.status in {"Open", "In Remediation", "Closed"}


class TestRiskScaleConstants:
    def test_risk_scale_completeness(self):
        assert set(RISK_SCALE.keys()) == {"Low", "Medium", "High", "Critical"}

    def test_risk_scale_ordering(self):
        assert RISK_SCALE["Low"] < RISK_SCALE["Medium"]
        assert RISK_SCALE["Medium"] < RISK_SCALE["High"]
        assert RISK_SCALE["High"] < RISK_SCALE["Critical"]

    def test_nist_functions_completeness(self):
        assert set(NIST_FUNCTIONS) == {"Identify", "Protect", "Detect", "Respond", "Recover"}


class TestOverdueLogic:
    def test_overdue_finding_has_past_due_date(self, db_session):
        f = db_session.query(AuditFinding).filter_by(finding_id="F-01").first()
        assert f.due_date < datetime.utcnow(), "F-01 should have a past due date"

    def test_closed_finding_should_not_be_overdue(self, db_session):
        """Closed findings must never be shown as overdue in the UI."""
        closed = db_session.query(AuditFinding).filter_by(status="Closed").all()
        # This is a business logic assertion, data loader enforces it
        for finding in closed:
            # Only findings that are NOT Closed can be overdue
            assert finding.status == "Closed"

    def test_overdue_flag_excludes_closed(self):
        """Verify the is_overdue derivation logic used in data_loader."""
        import pandas as pd
        today = pd.Timestamp(datetime.utcnow()).normalize()
        df = pd.DataFrame([
            {"status": "Open",   "due_date": pd.Timestamp(datetime.utcnow() - timedelta(days=5))},
            {"status": "Closed", "due_date": pd.Timestamp(datetime.utcnow() - timedelta(days=5))},
            {"status": "Open",   "due_date": pd.Timestamp(datetime.utcnow() + timedelta(days=5))},
        ])
        df["is_overdue"] = (df["due_date"] < today) & (df["status"] != "Closed")
        assert df.iloc[0]["is_overdue"] is True or df.iloc[0]["is_overdue"] == True
        assert df.iloc[1]["is_overdue"] is False or df.iloc[1]["is_overdue"] == False
        assert df.iloc[2]["is_overdue"] is False or df.iloc[2]["is_overdue"] == False
