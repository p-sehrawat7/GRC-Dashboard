"""
tests/test_exports.py
---------------------
Tests for PDF and Excel export helpers.
"""

import io
import pytest
import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def sample_risk_df():
    return pd.DataFrame([{
        "risk_id": "R-01", "risk_description": "Test", "asset": "A",
        "threat": "T", "vulnerability": "V", "impact": 4, "likelihood": 4,
        "risk_score": 16, "risk_level": "Critical",
        "treatment_status": "In Progress", "iso_clause": "A.9.4",
        "nist_function": "Protect", "risk_numeric": 4,
    }])


@pytest.fixture
def sample_control_df():
    return pd.DataFrame([{
        "control_id": "C-01", "control_name": "Test Control",
        "mapped_risk_id": "R-01", "control_type": "Preventive",
        "implementation_status": "Partial", "effectiveness": "Needs Improvement",
        "iso_clause": "A.9.4", "nist_function": "Protect",
        "risk_level_after_control": "High",
    }])


@pytest.fixture
def sample_findings_df():
    today = datetime.utcnow()
    return pd.DataFrame([
        {"finding_id": "F-01", "risk_id": "R-01", "control_id": "C-01",
         "title": "Test Finding", "severity": "Critical", "status": "Open",
         "due_date": pd.Timestamp(today - timedelta(days=10)),
         "owner": "Team A", "last_updated": pd.Timestamp(today),
         "is_overdue": True},
        {"finding_id": "F-02", "risk_id": "R-01", "control_id": "C-01",
         "title": "Closed Finding", "severity": "Medium", "status": "Closed",
         "due_date": pd.Timestamp(today - timedelta(days=30)),
         "owner": "Team B", "last_updated": pd.Timestamp(today),
         "is_overdue": False},
    ])


class TestPDFExport:
    def test_pdf_returns_bytes(self, sample_risk_df, sample_control_df, sample_findings_df):
        from views.audit_findings import _build_pdf
        result = _build_pdf(sample_risk_df, sample_control_df, sample_findings_df)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_pdf_starts_with_pdf_header(self, sample_risk_df, sample_control_df, sample_findings_df):
        from views.audit_findings import _build_pdf
        result = _build_pdf(sample_risk_df, sample_control_df, sample_findings_df)
        assert result[:4] == b"%PDF", "PDF output must start with %PDF magic bytes"

    def test_pdf_non_zero_size(self, sample_risk_df, sample_control_df, sample_findings_df):
        from views.audit_findings import _build_pdf
        result = _build_pdf(sample_risk_df, sample_control_df, sample_findings_df)
        assert len(result) > 1000, "PDF should be at least 1 KB"


class TestExcelExport:
    def test_excel_risk_register(self, sample_risk_df):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            sample_risk_df.to_excel(w, index=False, sheet_name="Risk Register")
        buf.seek(0)
        loaded = pd.read_excel(buf, sheet_name="Risk Register")
        assert "risk_id" in loaded.columns
        assert len(loaded) == 1

    def test_excel_control_matrix(self, sample_control_df):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            sample_control_df.to_excel(w, index=False, sheet_name="Control Matrix")
        buf.seek(0)
        loaded = pd.read_excel(buf, sheet_name="Control Matrix")
        assert "control_id" in loaded.columns

    def test_excel_findings_sheet_name(self, sample_findings_df):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            sample_findings_df.to_excel(w, index=False, sheet_name="Audit Findings")
        buf.seek(0)
        import openpyxl
        wb = openpyxl.load_workbook(buf)
        assert "Audit Findings" in wb.sheetnames

    def test_excel_findings_overdue_column(self, sample_findings_df):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            sample_findings_df.to_excel(w, index=False, sheet_name="Findings")
        buf.seek(0)
        loaded = pd.read_excel(buf, sheet_name="Findings")
        assert "is_overdue" in loaded.columns

    def test_excel_output_is_bytes(self, sample_risk_df):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            sample_risk_df.to_excel(w, index=False, sheet_name="Sheet1")
        assert len(buf.getvalue()) > 0
