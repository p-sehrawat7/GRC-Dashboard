"""
views/control_matrix.py
-----------------------
Control Matrix page — governance charts, filterable table,
Add Control form (Admin only), CSV and Excel export.
"""

import io
import streamlit as st
import pandas as pd

from utils.filters import control_filters
from utils.crud import add_control
from utils.logger import get_logger
from utils.data_loader import load_control_data
from database.db import get_db
from utils import charts as ch

log = get_logger(__name__)


def render(control_df: pd.DataFrame, username: str = "", role: str = "viewer"):
    st.markdown("## Control Matrix")
    st.markdown(
        "Management controls mapped to **ISO 27001 Annex A** and **NIST CSF**. "
        "Use the sidebar to filter by control type or implementation status."
    )

    filtered_df = control_filters(control_df)

    # ── KPIs ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Controls",  len(filtered_df))
    c2.metric("Implemented",     len(filtered_df[filtered_df["implementation_status"] == "Implemented"]))
    c3.metric("Partial",         len(filtered_df[filtered_df["implementation_status"] == "Partial"]))
    c4.metric("Missing",         len(filtered_df[filtered_df["implementation_status"] == "Missing"]))
    st.divider()

    if filtered_df.empty:
        st.warning("No controls match the selected filters.")
        return

    # ── Charts ─────────────────────────────────────────────────────────────
    st.markdown("### Governance Coverage")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(ch.iso_clause_coverage(filtered_df), use_container_width=True)
    with col2:
        st.plotly_chart(ch.nist_function_coverage(filtered_df), use_container_width=True)
    st.divider()

    # ── Control Table ──────────────────────────────────────────────────────
    st.markdown("### Control Details")

    def color_status(val):
        return {
            "Implemented": "background-color:#C8E6C9;color:#1B5E20;font-weight:bold",
            "Partial":     "background-color:#FFE0B2;color:#E65100;font-weight:bold",
            "Missing":     "background-color:#FFCDD2;color:#B71C1C;font-weight:bold",
        }.get(val, "")

    def color_residual(val):
        return {
            "Critical": "background-color:#FFCDD2;color:#B71C1C;font-weight:bold",
            "High":     "background-color:#FFE0B2;color:#E65100;font-weight:bold",
            "Medium":   "background-color:#FFF9C4;color:#F57F17;font-weight:bold",
            "Low":      "background-color:#C8E6C9;color:#1B5E20;font-weight:bold",
        }.get(val, "")

    display_cols = [
        "control_id", "control_name", "mapped_risk_id", "control_type",
        "implementation_status", "effectiveness", "iso_clause", "nist_function",
        "gap_description", "risk_level_after_control",
    ]
    styled = (
        filtered_df[display_cols].style
        .map(color_status,   subset=["implementation_status"])
        .map(color_residual, subset=["risk_level_after_control"])
        .set_properties(**{"font-size": "13px"})
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Effectiveness Summary ──────────────────────────────────────────────
    st.divider()
    st.markdown("### Effectiveness Overview")
    eff = filtered_df["effectiveness"].value_counts().reset_index()
    eff.columns = ["Effectiveness Rating", "Count"]
    st.dataframe(eff, use_container_width=True, hide_index=True)

    # ── Export ─────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Export")
    ex1, ex2 = st.columns(2)
    with ex1:
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "control_matrix.csv", "text/csv", key="ctrl_csv")
    with ex2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            filtered_df[display_cols].to_excel(w, index=False, sheet_name="Control Matrix")
        st.download_button(
            "Download Excel", buf.getvalue(),
            "control_matrix.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="ctrl_xlsx",
        )

    # ── Add Control Form (Admin only) ──────────────────────────────────────
    if role == "admin":
        st.divider()
        with st.expander("Add New Control", expanded=False):
            with st.form("add_ctrl_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    ctrl_id      = st.text_input("Control ID (e.g. C-41)*")
                    ctrl_name    = st.text_input("Control Name*")
                    mapped_risk  = st.text_input("Mapped Risk ID (e.g. R-01)*")
                    iso_clause   = st.text_input("ISO Clause")
                with col2:
                    ctrl_type   = st.selectbox("Control Type",
                                               ["Preventive", "Detective", "Corrective", "Recovery"])
                    impl_status = st.selectbox("Implementation Status",
                                               ["Implemented", "Partial", "Missing"])
                    effectiveness = st.selectbox("Effectiveness",
                                                 ["Effective", "Needs Improvement", "Ineffective"])
                    nist_func   = st.selectbox("NIST Function",
                                               ["Identify", "Protect", "Detect", "Respond", "Recover"])
                    residual    = st.selectbox("Residual Risk Level",
                                               ["Low", "Medium", "High", "Critical"])
                ctrl_desc   = st.text_area("Control Description")
                gap_desc    = st.text_area("Gap Description")
                evidence    = st.text_input("Evidence")
                submitted   = st.form_submit_button("Add Control")

                if submitted:
                    missing = [f for f, v in [
                        ("Control ID", ctrl_id), ("Control Name", ctrl_name),
                        ("Mapped Risk ID", mapped_risk)
                    ] if not v.strip()]
                    if missing:
                        st.error(f"Required fields missing: {', '.join(missing)}")
                    else:
                        try:
                            with get_db() as db:
                                add_control(db, {
                                    "control_id": ctrl_id.strip(),
                                    "control_name": ctrl_name.strip(),
                                    "control_description": ctrl_desc.strip(),
                                    "mapped_risk_id": mapped_risk.strip(),
                                    "control_type": ctrl_type,
                                    "implementation_status": impl_status,
                                    "effectiveness": effectiveness,
                                    "iso_clause": iso_clause.strip() or None,
                                    "nist_function": nist_func,
                                    "risk_level_after_control": residual,
                                    "gap_description": gap_desc.strip(),
                                    "evidence": evidence.strip(),
                                }, username)
                            load_control_data.clear()
                            log.info(f"Control {ctrl_id} created by {username}")
                            st.success(f"Control {ctrl_id} added successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to add control: {e}")
