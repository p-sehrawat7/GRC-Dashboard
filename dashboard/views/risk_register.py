"""
views/risk_register.py
----------------------
Risk Register page — filterable table, score chart, ISO/NIST breakdown,
Add Risk form (Admin + Auditor), CSV and Excel export.
"""

import io
import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import RISK_COLORS, load_risk_data
from utils.filters import risk_filters
from utils.crud import add_risk
from utils.logger import get_logger
from database.db import get_db

log = get_logger(__name__)


def render(risk_df: pd.DataFrame, username: str = "", role: str = "viewer"):
    st.markdown("## Risk Register")
    st.markdown(
        "Full list of identified risks aligned to **ISO 27001** and **NIST CSF**. "
        "Use the sidebar filters to drill down by asset, level, or treatment status."
    )

    # ── Sidebar Filters ────────────────────────────────────────────────────
    filtered_df = risk_filters(risk_df)

    # ── Summary KPIs ───────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Shown",  len(filtered_df))
    c2.metric("Critical",     len(filtered_df[filtered_df["risk_level"] == "Critical"]))
    c3.metric("High",         len(filtered_df[filtered_df["risk_level"] == "High"]))
    c4.metric("In Progress",  len(filtered_df[filtered_df["treatment_status"] == "In Progress"]))
    st.divider()

    if filtered_df.empty:
        st.warning("No risks match the selected filters. Adjust the sidebar criteria.")
        return

    # ── Risk Score Chart ───────────────────────────────────────────────────
    score_df = (
        filtered_df.groupby(["risk_id", "risk_level"])["risk_score"]
        .first().reset_index().sort_values("risk_score", ascending=False)
    )
    fig = px.bar(
        score_df, x="risk_id", y="risk_score", color="risk_level",
        color_discrete_map=RISK_COLORS,
        title="Risk Score by Risk ID",
        labels={"risk_id": "Risk ID", "risk_score": "Risk Score"},
        text="risk_score",
        category_orders={"risk_level": ["Critical", "High", "Medium", "Low"]},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=360, margin=dict(t=40, b=20), showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    st.divider()

    # ── Colour-coded Table ─────────────────────────────────────────────────
    def color_risk(val):
        return {
            "Critical": "background-color:#FFCDD2;color:#B71C1C;font-weight:bold",
            "High":     "background-color:#FFE0B2;color:#E65100;font-weight:bold",
            "Medium":   "background-color:#FFF9C4;color:#F57F17;font-weight:bold",
            "Low":      "background-color:#C8E6C9;color:#1B5E20;font-weight:bold",
        }.get(val, "")

    display_cols = [
        "risk_id", "risk_description", "asset", "threat",
        "risk_level", "treatment_status", "iso_clause", "nist_function",
        "impact", "likelihood", "risk_score",
    ]
    styled = (
        filtered_df[display_cols].style
        .map(color_risk, subset=["risk_level"])
        .set_properties(**{"font-size": "13px"})
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── ISO / NIST Breakdown ───────────────────────────────────────────────
    st.divider()
    st.markdown("### Risk Breakdown")
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("**By ISO 27001 Clause**")
        iso_t = (
            filtered_df.groupby("iso_clause")["risk_id"].count()
            .reset_index().rename(columns={"risk_id": "Risk Count"})
            .sort_values("Risk Count", ascending=False)
        )
        st.dataframe(iso_t, use_container_width=True, hide_index=True)
    with b2:
        st.markdown("**By NIST CSF Function**")
        nist_t = (
            filtered_df.groupby("nist_function")["risk_id"].count()
            .reset_index().rename(columns={"risk_id": "Risk Count"})
            .sort_values("Risk Count", ascending=False)
        )
        st.dataframe(nist_t, use_container_width=True, hide_index=True)

    # ── Export ─────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Export")
    ex1, ex2 = st.columns(2)
    with ex1:
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "risk_register.csv", "text/csv", key="risk_csv")
    with ex2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            filtered_df[display_cols].to_excel(w, index=False, sheet_name="Risk Register")
        st.download_button(
            "Download Excel", buf.getvalue(),
            "risk_register.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="risk_xlsx",
        )

    # ── Add New Risk Form (Admin + Auditor) ────────────────────────────────
    if role in ("admin", "auditor"):
        st.divider()
        with st.expander("Add New Risk", expanded=False):

            # ── Guidance panel ─────────────────────────────────────────────
            st.markdown("""
<div style="background:#EFF6FF;border-left:4px solid #1E3A5F;padding:12px 16px;
            border-radius:0 8px 8px 0;margin-bottom:16px;color:#1e293b">
<strong style="color:#1E3A5F;font-size:14px">Field Reference Guide</strong>
<table style="font-size:13px;margin-top:8px;width:100%;border-collapse:collapse">
<tr style="border-bottom:1px solid #cbd5e1">
  <td style="padding:4px 8px 4px 0;font-weight:600;width:160px">Risk Level</td>
  <td style="padding:4px 0">Low &nbsp;&bull;&nbsp; Medium &nbsp;&bull;&nbsp; High &nbsp;&bull;&nbsp; Critical</td>
</tr>
<tr style="border-bottom:1px solid #cbd5e1">
  <td style="padding:4px 8px 4px 0;font-weight:600">Treatment Status</td>
  <td style="padding:4px 0">In Progress &nbsp;&bull;&nbsp; Mitigated &nbsp;&bull;&nbsp; Accepted &nbsp;&bull;&nbsp; Transferred &nbsp;&bull;&nbsp; Avoided</td>
</tr>
<tr style="border-bottom:1px solid #cbd5e1">
  <td style="padding:4px 8px 4px 0;font-weight:600">NIST Function</td>
  <td style="padding:4px 0">Identify &nbsp;&bull;&nbsp; Protect &nbsp;&bull;&nbsp; Detect &nbsp;&bull;&nbsp; Respond &nbsp;&bull;&nbsp; Recover</td>
</tr>
<tr style="border-bottom:1px solid #cbd5e1">
  <td style="padding:4px 8px 4px 0;font-weight:600">ISO 27001 Clause</td>
  <td style="padding:4px 0">e.g. A.9.4 (Access Control) &nbsp;&bull;&nbsp; A.8.7 (Malware) &nbsp;&bull;&nbsp; A.5.1 (Policies)</td>
</tr>
<tr>
  <td style="padding:4px 8px 4px 0;font-weight:600">Risk Score</td>
  <td style="padding:4px 0">Impact (1–5) &times; Likelihood (1–5) &mdash; auto-calculated (max 25)</td>
</tr>
</table>
</div>
""", unsafe_allow_html=True)

            with st.form("add_risk_form", clear_on_submit=True):
                st.markdown("**Identification**")
                col1, col2 = st.columns(2)

                with col1:
                    risk_id = st.text_input(
                        "Risk ID *",
                        placeholder="e.g. R-41",
                        help="Unique identifier. Match the existing R-NN numbering.",
                    )
                    asset = st.text_input(
                        "Asset *",
                        placeholder="e.g. Customer Financial Data",
                        help="System, dataset, process, or person that is at risk.",
                    )
                    threat = st.text_input(
                        "Threat *",
                        placeholder="e.g. External Attacker",
                        help="The threat actor or event (e.g. Ransomware, Insider Misuse, Accidental Disclosure).",
                    )
                    iso_clause = st.text_input(
                        "ISO 27001 Clause",
                        placeholder="e.g. A.9.4  (optional)",
                        help="Relevant Annex A clause. Leave blank if unknown.",
                    )

                with col2:
                    risk_level = st.selectbox(
                        "Risk Level *",
                        ["Low", "Medium", "High", "Critical"],
                        index=2,
                        help="Low = score 1–6 | Medium = 7–12 | High = 13–18 | Critical = 19–25",
                    )
                    treatment = st.selectbox(
                        "Treatment Status *",
                        ["In Progress", "Mitigated", "Accepted", "Transferred", "Avoided"],
                        help=(
                            "In Progress = controls being implemented  |  "
                            "Mitigated = controls applied and working  |  "
                            "Accepted = risk accepted by management  |  "
                            "Transferred = insured or outsourced  |  "
                            "Avoided = activity/asset removed"
                        ),
                    )
                    nist_func = st.selectbox(
                        "NIST CSF Function *",
                        ["Identify", "Protect", "Detect", "Respond", "Recover"],
                        index=1,
                        help=(
                            "Identify = Know assets & gaps  |  "
                            "Protect = Safeguards  |  "
                            "Detect = Monitoring  |  "
                            "Respond = Incident response  |  "
                            "Recover = Recovery planning"
                        ),
                    )
                    st.markdown("**Risk Score (Impact × Likelihood)**")
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        impact = st.slider(
                            "Impact  (1=Negligible → 5=Catastrophic)",
                            min_value=1, max_value=5, value=3,
                        )
                    with sc2:
                        likelihood = st.slider(
                            "Likelihood  (1=Rare → 5=Almost Certain)",
                            min_value=1, max_value=5, value=3,
                        )
                    score = impact * likelihood
                    score_color = (
                        "#D32F2F" if score >= 19 else
                        "#F57C00" if score >= 13 else
                        "#FBC02D" if score >= 7  else
                        "#388E3C"
                    )
                    st.markdown(
                        f"<div style='padding:6px 12px;border-radius:6px;background:{score_color};"
                        f"color:white;font-weight:700;text-align:center;font-size:15px'>"
                        f"Risk Score: {score} / 25</div>",
                        unsafe_allow_html=True,
                    )

                st.markdown("**Details**")
                vulnerability = st.text_area(
                    "Vulnerability *",
                    placeholder="e.g. No MFA enforced on admin accounts",
                    help="The specific weakness or control gap that could be exploited.",
                    height=70,
                )
                description = st.text_area(
                    "Risk Description *",
                    placeholder=(
                        "e.g. Unauthorised access to customer PII due to absence of MFA "
                        "on privileged admin accounts."
                    ),
                    help="One or two sentences describing the full risk scenario.",
                    height=70,
                )

                submitted = st.form_submit_button(
                    "Add Risk to Register", use_container_width=True
                )

                if submitted:
                    missing = [f for f, v in [
                        ("Risk ID", risk_id), ("Asset", asset), ("Threat", threat),
                        ("Vulnerability", vulnerability), ("Risk Description", description)
                    ] if not v.strip()]
                    if missing:
                        st.error(f"Required fields missing: {', '.join(missing)}")
                    else:
                        try:
                            with get_db() as db:
                                add_risk(db, {
                                    "risk_id":          risk_id.strip(),
                                    "risk_description": description.strip(),
                                    "asset":            asset.strip(),
                                    "threat":           threat.strip(),
                                    "vulnerability":    vulnerability.strip(),
                                    "impact":           impact,
                                    "likelihood":       likelihood,
                                    "risk_score":       impact * likelihood,
                                    "risk_level":       risk_level,
                                    "treatment_status": treatment,
                                    "iso_clause":       iso_clause.strip() or None,
                                    "nist_function":    nist_func,
                                }, username)
                            load_risk_data.clear()
                            log.info(f"Risk {risk_id} created by {username}")
                            st.success(f"Risk **{risk_id}** added successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to add risk: {e}")
