"""
tests/test_crud.py
------------------
Tests for CRUD helper functions in dashboard/utils/crud.py
"""

import pytest
from datetime import datetime, timedelta
from database.models import Risk, Control, AuditFinding, AuditLog
from utils.crud import (
    add_risk, update_risk, delete_risk,
    add_control, update_control,
    add_finding, update_finding, close_finding,
    log_action,
)


class TestRiskCRUD:
    def test_add_risk_creates_record(self, db_session):
        data = {
            "risk_id": "R-99", "risk_description": "New test risk",
            "asset": "Asset A", "threat": "Threat A", "vulnerability": "Vuln A",
            "impact": 3, "likelihood": 3, "risk_score": 9,
            "risk_level": "Medium", "treatment_status": "Accepted",
            "iso_clause": "A.5.1", "nist_function": "Identify",
        }
        risk = add_risk(db_session, data, "admin")
        assert risk.risk_id == "R-99"
        assert db_session.query(Risk).filter_by(risk_id="R-99").count() == 1

    def test_add_risk_creates_audit_log(self, db_session):
        initial = db_session.query(AuditLog).count()
        data = {
            "risk_id": "R-98", "risk_description": "Log test risk",
            "asset": "A", "threat": "T", "vulnerability": "V",
            "impact": 2, "likelihood": 2, "risk_score": 4,
            "risk_level": "Low", "treatment_status": "Accepted",
            "iso_clause": "A.5.1", "nist_function": "Identify",
        }
        add_risk(db_session, data, "admin")
        assert db_session.query(AuditLog).count() == initial + 1

    def test_update_risk(self, db_session):
        result = update_risk(db_session, "R-01", {"treatment_status": "Mitigated"}, "admin")
        assert result is not None
        assert result.treatment_status == "Mitigated"

    def test_update_nonexistent_risk_returns_none(self, db_session):
        result = update_risk(db_session, "R-999", {"risk_level": "Low"}, "admin")
        assert result is None

    def test_delete_risk(self, db_session):
        data = {
            "risk_id": "R-97", "risk_description": "Delete me",
            "asset": "A", "threat": "T", "vulnerability": "V",
            "impact": 1, "likelihood": 1, "risk_score": 1,
            "risk_level": "Low", "treatment_status": "Accepted",
            "iso_clause": None, "nist_function": "Identify",
        }
        add_risk(db_session, data, "admin")
        deleted = delete_risk(db_session, "R-97", "admin")
        assert deleted is True
        assert db_session.query(Risk).filter_by(risk_id="R-97").count() == 0

    def test_delete_nonexistent_risk_returns_false(self, db_session):
        result = delete_risk(db_session, "R-000", "admin")
        assert result is False


class TestControlCRUD:
    def test_add_control(self, db_session):
        data = {
            "control_id": "C-99", "control_name": "Test Control 99",
            "mapped_risk_id": "R-01", "control_type": "Detective",
            "implementation_status": "Missing", "effectiveness": "Ineffective",
            "iso_clause": "A.8.15", "nist_function": "Detect",
            "risk_level_after_control": "Critical",
        }
        ctrl = add_control(db_session, data, "admin")
        assert ctrl.control_id == "C-99"

    def test_update_control_status(self, db_session):
        result = update_control(db_session, "C-01",
                                {"implementation_status": "Implemented"}, "admin")
        assert result is not None
        assert result.implementation_status == "Implemented"


class TestFindingCRUD:
    def test_add_finding(self, db_session):
        data = {
            "finding_id": "F-99", "risk_id": "R-01", "control_id": "C-01",
            "title": "Test Finding 99", "severity": "High",
            "status": "Open", "due_date": datetime.utcnow() + timedelta(days=30),
            "owner": "Test Owner",
        }
        finding = add_finding(db_session, data, "auditor")
        assert finding.finding_id == "F-99"

    def test_close_finding(self, db_session):
        result = close_finding(db_session, "F-01", "admin")
        assert result is not None
        assert result.status == "Closed"

    def test_update_finding_last_updated(self, db_session):
        result = update_finding(db_session, "F-01",
                                {"owner": "New Owner"}, "admin")
        assert result.owner == "New Owner"


class TestAuditLog:
    def test_log_action_creates_entry(self, db_session):
        initial = db_session.query(AuditLog).count()
        log_action(db_session, "risks", "R-01", "LOGIN", "admin", "Test detail")
        assert db_session.query(AuditLog).count() == initial + 1

    def test_log_entry_has_correct_fields(self, db_session):
        log_action(db_session, "risks", "R-TEST", "CREATE", "auditor", "detail")
        entry = (db_session.query(AuditLog)
                 .filter_by(record_id="R-TEST", action="CREATE")
                 .first())
        assert entry is not None
        assert entry.username == "auditor"
        assert entry.table_name == "risks"
