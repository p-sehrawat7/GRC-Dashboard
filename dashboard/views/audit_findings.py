"""
views/audit_findings.py
-----------------------
Audit Findings page — severity charts, overdue tracker, remediation gauge,
Log Finding form (Admin + Auditor), Close Finding (Admin + Auditor),
CSV, Excel, and PDF executive summary export.
"""

import io
import datetime
import streamlit as st
import pandas as pd

from utils.filters import findings_filters
from utils.crud import add_finding, close_finding
from utils.logger import get_logger
from utils.data_loader import load_audit_findings
from database.db import get_db
from utils import charts as ch

log = get_logger(__name__)


# ── PDF builder ───────────────────────────────────────────────────────────────

def _build_pdf(risk_df, control_df, findings_df) -> bytes:
    today        = datetime.date.today().strftime("%d %B %Y")
    total_risks  = len(risk_df)
    critical     = len(risk_df[risk_df["risk_level"] == "Critical"])
    impl_ctrl    = len(control_df[control_df["implementation_status"] == "Implemented"])
    coverage     = round(impl_ctrl / len(control_df) * 100, 1) if len(control_df) else 0
    open_find    = len(findings_df[findings_df["status"] != "Closed"])
    overdue      = int(findings_df["is_overdue"].sum())
    closed       = len(findings_df[findings_df["status"] == "Closed"])
    remediation  = round(closed / len(findings_df) * 100, 1) if len(findings_df) else 0

    try:
        from fpdf import FPDF

        class GrcPDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 14)
                self.set_text_color(30, 58, 95)
                self.cell(0, 10, "GRC Audit Simulation Dashboard - Executive Summary",
                          new_x="LMARGIN", new_y="NEXT", align="C")
                self.set_font("Helvetica", "", 9)
                self.set_text_color(100, 100, 100)
                self.cell(0, 6, f"Generated: {today}   -   ISO 27001 & NIST CSF",
                          new_x="LMARGIN", new_y="NEXT", align="C")
                self.ln(4)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10,
                          f"Page {self.page_no()}   -   Confidential - For Internal Use Only",
                          align="C")

        pdf = GrcPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        def section(title):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(30, 58, 95)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 8, f"  {title}", new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)

        def kv(label, value):
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(70, 7, label + ":")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, str(value), new_x="LMARGIN", new_y="NEXT")

        section("Risk Summary")
        kv("Total Risks",    total_risks)
        kv("Critical Risks", critical)
        kv("High Risks",     len(risk_df[risk_df["risk_level"] == "High"]))
        kv("Medium Risks",   len(risk_df[risk_df["risk_level"] == "Medium"]))
        kv("Low Risks",      len(risk_df[risk_df["risk_level"] == "Low"]))
        pdf.ln(4)

        section("Control Coverage")
        kv("Total Controls", len(control_df))
        kv("Implemented",    impl_ctrl)
        kv("Partial",        len(control_df[control_df["implementation_status"] == "Partial"]))
        kv("Missing",        len(control_df[control_df["implementation_status"] == "Missing"]))
        kv("Coverage",       f"{coverage}%")
        pdf.ln(4)

        section("Audit Findings")
        kv("Total Findings",       len(findings_df))
        kv("Open",                 open_find)
        kv("Overdue",              overdue)
        kv("Closed",               closed)
        kv("Remediation Progress", f"{remediation}%")
        pdf.ln(4)

        section("Key Recommendations")
        recs = [
            "1. Enforce MFA immediately on all privileged admin accounts (R-01, C-01).",
            "2. Deploy an EDR solution to all endpoints to close detection gap (R-05, C-08).",
            "3. Initiate formal vendor risk assessments before third-party onboarding (R-06, C-09).",
            "4. Implement a SIEM/log monitoring platform for threat detection (R-15, C-05).",
            "5. Complete security awareness training for all staff within 30 days (R-03, C-06).",
            "6. Formally approve and communicate the Information Security Policy (R-04, C-04).",
            "7. Close critical public exposure findings immediately (R-16, R-19, R-22).",
        ]
        pdf.set_font("Helvetica", "", 10)
        for r in recs:
            pdf.multi_cell(0, 6, r)
            pdf.ln(1)

        return bytes(pdf.output())

    except ImportError:
        lines = [
            "GRC AUDIT SIMULATION DASHBOARD - EXECUTIVE SUMMARY",
            f"Generated: {today}", "",
            "RISK SUMMARY",
            f"  Total Risks  : {total_risks}",
            f"  Critical     : {critical}", "",
            "CONTROL COVERAGE",
            f"  Total        : {len(control_df)}",
            f"  Implemented  : {impl_ctrl}",
            f"  Coverage     : {coverage}%", "",
            "AUDIT FINDINGS",
            f"  Open         : {open_find}",
            f"  Overdue      : {overdue}",
            f"  Remediation  : {remediation}%",
        ]
        return "\n".join(lines).encode("utf-8")


# ── Main render ───────────────────────────────────────────────────────────────

def render(risk_df, control_df, findings_df: pd.DataFrame,
           username: str = "", role: str = "viewer"):

    st.markdown("## Audit Findings")
    st.markdown(
        "Track open findings, remediation progress, and overdue items. "
        "Use sidebar filters to focus your review."
    )

    filtered_df, _ = findings_filters(findings_df)

    # ── KPIs ───────────────────────────────────────────────────────────────
    total     = len(filtered_df)
    open_f    = len(filtered_df[filtered_df["status"] != "Closed"])
    overdue_f = int(filtered_df["is_overdue"].sum())
    closed_f  = len(filtered_df[filtered_df["status"] == "Closed"])
    rem_pct   = round(closed_f / total * 100, 1) if total else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total",        total)
    k2.metric("Open",         open_f)
    k3.metric("Overdue",      overdue_f,
              delta=f"{overdue_f} past due" if overdue_f else None,
              delta_color="inverse")
    k4.metric("Closed",       closed_f)
    k5.metric("Remediation",  f"{rem_pct}%")
    st.divider()

    if filtered_df.empty:
        st.warning("No findings match the selected filters.")
        return

    # ── Charts ─────────────────────────────────────────────────────────────
    st.markdown("### Findings Analysis")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(ch.findings_by_severity(filtered_df), use_container_width=True)
    with c2:
        st.plotly_chart(ch.findings_status_donut(filtered_df), use_container_width=True)

    g1, g2 = st.columns([1, 2])
    with g1:
        st.plotly_chart(ch.remediation_gauge(filtered_df), use_container_width=True)
    with g2:
        st.plotly_chart(ch.overdue_findings_bar(filtered_df), use_container_width=True)
    st.divider()

    # ── Overdue Findings ───────────────────────────────────────────────────
    overdue_rows = filtered_df[filtered_df["is_overdue"]]
    if not overdue_rows.empty:
        st.markdown("### Overdue Findings")
        st.error(f"**{len(overdue_rows)} finding(s)** are past their due date.")
        st.dataframe(
            overdue_rows[["finding_id", "title", "severity", "owner",
                          "due_date", "status"]].sort_values("due_date"),
            use_container_width=True, hide_index=True,
        )
        st.divider()

    # ── Full Findings Table ────────────────────────────────────────────────
    st.markdown("### All Findings Detail")

    def color_sev(val):
        return {
            "Critical": "background-color:#FFCDD2;color:#B71C1C;font-weight:bold",
            "High":     "background-color:#FFE0B2;color:#E65100;font-weight:bold",
            "Medium":   "background-color:#FFF9C4;color:#F57F17;font-weight:bold",
            "Low":      "background-color:#C8E6C9;color:#1B5E20;font-weight:bold",
        }.get(val, "")

    def color_status(val):
        return {
            "Open":            "background-color:#FFCDD2;color:#B71C1C;",
            "In Remediation":  "background-color:#FFE0B2;color:#E65100;",
            "Closed":          "background-color:#C8E6C9;color:#1B5E20;",
        }.get(val, "")

    display_cols = [
        "finding_id", "title", "risk_id", "control_id",
        "severity", "status", "due_date", "owner", "last_updated", "is_overdue",
    ]
    disp = filtered_df[display_cols].copy()
    disp["due_date"]     = disp["due_date"].dt.strftime("%d %b %Y")
    disp["last_updated"] = disp["last_updated"].dt.strftime("%d %b %Y")

    styled = (
        disp.style
        .map(color_sev,    subset=["severity"])
        .map(color_status, subset=["status"])
        .set_properties(**{"font-size": "13px"})
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Export ─────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Export")
    ex1, ex2, ex3 = st.columns(3)

    with ex1:
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "audit_findings.csv",
                           "text/csv", key="find_csv")
    with ex2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            filtered_df[display_cols].to_excel(w, index=False, sheet_name="Audit Findings")
        st.download_button(
            "Download Excel", buf.getvalue(), "audit_findings.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="find_xlsx",
        )
    with ex3:
        with st.spinner("Generating PDF..."):
            pdf_bytes = _build_pdf(risk_df, control_df, findings_df)
        is_pdf = isinstance(pdf_bytes, bytes) and pdf_bytes[:4] == b"%PDF"
        st.download_button(
            "Download Executive Summary (PDF)" if is_pdf else "Download Summary (TXT)",
            pdf_bytes,
            "grc_executive_summary.pdf" if is_pdf else "grc_executive_summary.txt",
            "application/pdf" if is_pdf else "text/plain",
            key="exec_pdf",
        )

    # ── Log New Finding (Admin + Auditor) ──────────────────────────────────
    if role in ("admin", "auditor"):
        st.divider()
        with st.expander("Log New Finding", expanded=False):
            all_risks = sorted(findings_df["risk_id"].unique().tolist())
            with st.form("add_finding_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    fid      = st.text_input("Finding ID (e.g. F-41)*")
                    title    = st.text_input("Title*")
                    risk_id  = st.selectbox("Linked Risk ID*", all_risks)
                    ctrl_id  = st.text_input("Linked Control ID*")
                    owner    = st.text_input("Owner*")
                with col2:
                    severity = st.selectbox("Severity", ["Critical", "High", "Medium", "Low"])
                    status   = st.selectbox("Status", ["Open", "In Remediation", "Closed"])
                    due_date = st.date_input("Due Date", value=datetime.date.today()
                                            + datetime.timedelta(days=30))
                desc = st.text_area("Description")
                submitted = st.form_submit_button("Log Finding")

                if submitted:
                    missing = [f for f, v in [
                        ("Finding ID", fid), ("Title", title),
                        ("Control ID", ctrl_id), ("Owner", owner)
                    ] if not v.strip()]
                    if missing:
                        st.error(f"Required fields missing: {', '.join(missing)}")
                    else:
                        try:
                            with get_db() as db:
                                add_finding(db, {
                                    "finding_id": fid.strip(),
                                    "risk_id":    risk_id,
                                    "control_id": ctrl_id.strip(),
                                    "title":      title.strip(),
                                    "severity":   severity,
                                    "status":     status,
                                    "due_date":   datetime.datetime.combine(
                                                      due_date, datetime.time()),
                                    "owner":      owner.strip(),
                                    "description": desc.strip(),
                                }, username)
                            load_audit_findings.clear()
                            log.info(f"Finding {fid} created by {username}")
                            st.success(f"Finding {fid} logged successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to log finding: {e}")

        # ── Close Finding ──────────────────────────────────────────────────
        with st.expander("Close a Finding", expanded=False):
            open_ids = filtered_df[filtered_df["status"] != "Closed"]["finding_id"].tolist()
            if not open_ids:
                st.info("No open findings to close.")
            else:
                with st.form("close_finding_form", clear_on_submit=True):
                    fid_to_close = st.selectbox("Select Finding to Close", open_ids)
                    confirmed    = st.form_submit_button("Mark as Closed")
                    if confirmed:
                        try:
                            with get_db() as db:
                                close_finding(db, fid_to_close, username)
                            load_audit_findings.clear()
                            log.info(f"Finding {fid_to_close} closed by {username}")
                            st.success(f"Finding {fid_to_close} marked as Closed.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to close finding: {e}")
