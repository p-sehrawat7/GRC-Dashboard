"""
dashboard/utils/crud.py
-----------------------
Pure-Python CRUD helpers over SQLAlchemy session.
No Streamlit dependency — safe to use in tests.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from database.models import Risk, Control, AuditFinding, AuditLog


# ── Audit logging ─────────────────────────────────────────────────────────────

def log_action(db: Session, table: str, record_id: str,
               action: str, username: str, detail: str = "") -> None:
    db.add(AuditLog(
        table_name=table, record_id=record_id,
        action=action, username=username,
        timestamp=datetime.utcnow(), detail=detail,
    ))


# ── Risk CRUD ─────────────────────────────────────────────────────────────────

def add_risk(db: Session, data: dict, username: str) -> Risk:
    risk = Risk(**data, created_by=username)
    db.add(risk)
    db.flush()
    log_action(db, "risks", risk.risk_id, "CREATE", username)
    return risk


def update_risk(db: Session, risk_id: str, data: dict, username: str) -> Optional[Risk]:
    risk = db.query(Risk).filter(Risk.risk_id == risk_id).first()
    if not risk:
        return None
    for k, v in data.items():
        setattr(risk, k, v)
    risk.updated_at = datetime.utcnow()
    log_action(db, "risks", risk_id, "UPDATE", username, str(data))
    return risk


def delete_risk(db: Session, risk_id: str, username: str) -> bool:
    risk = db.query(Risk).filter(Risk.risk_id == risk_id).first()
    if not risk:
        return False
    db.delete(risk)
    log_action(db, "risks", risk_id, "DELETE", username)
    return True


# ── Control CRUD ──────────────────────────────────────────────────────────────

def add_control(db: Session, data: dict, username: str) -> Control:
    ctrl = Control(**data, created_by=username)
    db.add(ctrl)
    db.flush()
    log_action(db, "controls", ctrl.control_id, "CREATE", username)
    return ctrl


def update_control(db: Session, control_id: str, data: dict, username: str) -> Optional[Control]:
    ctrl = db.query(Control).filter(Control.control_id == control_id).first()
    if not ctrl:
        return None
    for k, v in data.items():
        setattr(ctrl, k, v)
    ctrl.updated_at = datetime.utcnow()
    log_action(db, "controls", control_id, "UPDATE", username, str(data))
    return ctrl


# ── AuditFinding CRUD ─────────────────────────────────────────────────────────

def add_finding(db: Session, data: dict, username: str) -> AuditFinding:
    finding = AuditFinding(**data, created_by=username)
    db.add(finding)
    db.flush()
    log_action(db, "audit_findings", finding.finding_id, "CREATE", username)
    return finding


def update_finding(db: Session, finding_id: str, data: dict, username: str) -> Optional[AuditFinding]:
    finding = db.query(AuditFinding).filter(AuditFinding.finding_id == finding_id).first()
    if not finding:
        return None
    for k, v in data.items():
        setattr(finding, k, v)
    finding.last_updated = datetime.utcnow()
    log_action(db, "audit_findings", finding_id, "UPDATE", username, str(data))
    return finding


def close_finding(db: Session, finding_id: str, username: str) -> Optional[AuditFinding]:
    return update_finding(db, finding_id, {"status": "Closed"}, username)
