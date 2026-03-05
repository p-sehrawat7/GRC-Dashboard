"""
database/models.py
------------------
SQLAlchemy ORM models for the GRC Audit Simulation Dashboard.
Tables: risks, controls, audit_findings, audit_log, users
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Risk(Base):
    __tablename__ = "risks"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    risk_id           = Column(String(20), unique=True, nullable=False, index=True)
    risk_description  = Column(Text, nullable=False)
    asset             = Column(String(100), nullable=False)
    threat            = Column(String(100), nullable=False)
    vulnerability     = Column(Text, nullable=False)
    impact            = Column(Integer, nullable=False)          # 1–5
    likelihood        = Column(Integer, nullable=False)          # 1–5
    risk_score        = Column(Integer, nullable=False)          # impact * likelihood
    risk_level        = Column(
        Enum("Low", "Medium", "High", "Critical", name="risk_level_enum"),
        nullable=False,
    )
    treatment_status  = Column(
        Enum("In Progress", "Mitigated", "Accepted", "Transferred", "Avoided",
             name="treatment_status_enum"),
        nullable=False,
    )
    iso_clause        = Column(String(20))
    nist_function     = Column(
        Enum("Identify", "Protect", "Detect", "Respond", "Recover",
             name="nist_function_enum"),
    )
    created_at        = Column(DateTime, default=datetime.utcnow)
    updated_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by        = Column(String(80), default="system")

    controls  = relationship("Control",      back_populates="risk", cascade="all, delete-orphan")
    findings  = relationship("AuditFinding", back_populates="risk", cascade="all, delete-orphan")


class Control(Base):
    __tablename__ = "controls"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    control_id            = Column(String(20), unique=True, nullable=False, index=True)
    control_name          = Column(String(200), nullable=False)
    control_description   = Column(Text)
    mapped_risk_id        = Column(String(20), ForeignKey("risks.risk_id"), nullable=False)
    control_type          = Column(
        Enum("Preventive", "Detective", "Corrective", "Recovery",
             name="control_type_enum"),
        nullable=False,
    )
    implementation_status = Column(
        Enum("Implemented", "Partial", "Missing", name="impl_status_enum"),
        nullable=False,
    )
    effectiveness         = Column(
        Enum("Effective", "Needs Improvement", "Ineffective", name="effectiveness_enum"),
        nullable=False,
    )
    evidence              = Column(Text)
    gap_description       = Column(Text)
    risk_level_after_control = Column(
        Enum("Low", "Medium", "High", "Critical", name="residual_risk_enum"),
    )
    iso_clause            = Column(String(20))
    nist_function         = Column(
        Enum("Identify", "Protect", "Detect", "Respond", "Recover",
             name="nist_func_ctrl_enum"),
    )
    created_at            = Column(DateTime, default=datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by            = Column(String(80), default="system")

    risk = relationship("Risk", back_populates="controls")


class AuditFinding(Base):
    __tablename__ = "audit_findings"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    finding_id   = Column(String(20), unique=True, nullable=False, index=True)
    risk_id      = Column(String(20), ForeignKey("risks.risk_id"), nullable=False)
    control_id   = Column(String(20), nullable=False)
    title        = Column(String(200), nullable=False)
    severity     = Column(
        Enum("Critical", "High", "Medium", "Low", name="severity_enum"),
        nullable=False,
    )
    status       = Column(
        Enum("Open", "In Remediation", "Closed", name="finding_status_enum"),
        nullable=False,
    )
    due_date     = Column(DateTime, nullable=False)
    owner        = Column(String(100), nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    description  = Column(Text)
    created_at   = Column(DateTime, default=datetime.utcnow)
    created_by   = Column(String(80), default="system")

    risk = relationship("Risk", back_populates="findings")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    table_name  = Column(String(50), nullable=False)
    record_id   = Column(String(50), nullable=False)
    action      = Column(String(20), nullable=False)   # CREATE / UPDATE / DELETE / LOGIN
    username    = Column(String(80), nullable=False)
    timestamp   = Column(DateTime, default=datetime.utcnow)
    detail      = Column(Text)


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    username        = Column(String(80), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role            = Column(
        Enum("admin", "auditor", "viewer", name="role_enum"),
        nullable=False,
        default="viewer",
    )
    created_at      = Column(DateTime, default=datetime.utcnow)
