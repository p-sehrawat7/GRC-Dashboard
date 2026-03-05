"""
dashboard/utils/data_loader.py
-------------------------------
Database-backed data loading functions for the GRC Audit Simulation Dashboard.
Public API is identical to the old CSV-based loader so all page modules work unchanged.
"""

import pandas as pd
import streamlit as st
from datetime import datetime

from database.db import get_db, init_db
from database.models import Risk, Control, AuditFinding

# ─── Colour / Scale constants (unchanged) ─────────────────────────────────────
RISK_SCALE = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}

RISK_COLORS = {
    "Critical": "#D32F2F",
    "High":     "#F57C00",
    "Medium":   "#FBC02D",
    "Low":      "#388E3C",
}

CONTROL_COLORS = {
    "Implemented": "#388E3C",
    "Partial":     "#F57C00",
    "Missing":     "#D32F2F",
}

NIST_FUNCTIONS = ["Identify", "Protect", "Detect", "Respond", "Recover"]

NIST_COLORS = {
    "Identify": "#1565C0",
    "Protect":  "#2E7D32",
    "Detect":   "#F57F17",
    "Respond":  "#6A1B9A",
    "Recover":  "#00838F",
}


def _ensure_db():
    """Initialise database tables on first access (idempotent)."""
    init_db()


@st.cache_data(show_spinner=False, ttl=30)
def load_risk_data() -> pd.DataFrame:
    """Return risks table as a DataFrame with derived risk_numeric column."""
    _ensure_db()
    # Build the list of dicts INSIDE the session so ORM attributes are
    # read while the DB connection is still open (avoids DetachedInstanceError)
    with get_db() as db:
        rows = db.query(Risk).all()
        if not rows:
            raise ValueError("Risk table is empty. Run: python database/seed.py")
        records = [{
            "risk_id":          r.risk_id,
            "risk_description": r.risk_description,
            "asset":            r.asset,
            "threat":           r.threat,
            "vulnerability":    r.vulnerability,
            "impact":           r.impact,
            "likelihood":       r.likelihood,
            "risk_score":       r.risk_score,
            "risk_level":       r.risk_level,
            "treatment_status": r.treatment_status,
            "iso_clause":       r.iso_clause,
            "nist_function":    r.nist_function,
        } for r in rows]

    df = pd.DataFrame(records)
    df["risk_numeric"] = df["risk_level"].map(RISK_SCALE)
    return df


@st.cache_data(show_spinner=False, ttl=30)
def load_control_data() -> pd.DataFrame:
    """Return controls table as a DataFrame."""
    _ensure_db()
    with get_db() as db:
        rows = db.query(Control).all()
        if not rows:
            raise ValueError("Controls table is empty. Run: python database/seed.py")
        records = [{
            "control_id":               r.control_id,
            "control_name":             r.control_name,
            "control_description":      r.control_description,
            "mapped_risk_id":           r.mapped_risk_id,
            "control_type":             r.control_type,
            "implementation_status":    r.implementation_status,
            "effectiveness":            r.effectiveness,
            "evidence":                 r.evidence,
            "gap_description":          r.gap_description,
            "risk_level_after_control": r.risk_level_after_control,
            "iso_clause":               r.iso_clause,
            "nist_function":            r.nist_function,
        } for r in rows]

    return pd.DataFrame(records)


@st.cache_data(show_spinner=False, ttl=30)
def load_audit_findings() -> pd.DataFrame:
    """Return audit findings table as a DataFrame with is_overdue derived column."""
    _ensure_db()
    with get_db() as db:
        rows = db.query(AuditFinding).all()
        if not rows:
            raise ValueError("Audit findings table is empty. Run: python database/seed.py")
        records = [{
            "finding_id":   r.finding_id,
            "risk_id":      r.risk_id,
            "control_id":   r.control_id,
            "title":        r.title,
            "severity":     r.severity,
            "status":       r.status,
            "due_date":     pd.Timestamp(r.due_date),
            "owner":        r.owner,
            "last_updated": pd.Timestamp(r.last_updated) if r.last_updated else None,
            "description":  r.description,
        } for r in rows]

    df = pd.DataFrame(records)
    today = pd.Timestamp(datetime.utcnow()).normalize()
    df["is_overdue"] = (df["due_date"] < today) & (df["status"] != "Closed")
    return df
