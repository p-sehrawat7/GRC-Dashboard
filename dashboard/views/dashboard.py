"""
dashboard.py
------------
Main Dashboard page for the GRC Audit Simulation Dashboard.
Renders executive summary, KPIs, and all governance visuals.
This module is only loaded when the user selects "Dashboard" in the sidebar.
"""

import streamlit as st
import pandas as pd

from utils.data_loader import RISK_SCALE, RISK_COLORS
from utils import charts as ch


def render(risk_df: pd.DataFrame, control_df: pd.DataFrame, findings_df: pd.DataFrame):
    """
    Render the full Executive Dashboard page.

    Args:
        risk_df:     Risk register DataFrame.
        control_df:  Control matrix DataFrame.
        findings_df: Audit findings DataFrame.
    """
    # ── Risk Appetite Selector (drives Executive Summary) ──────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚖️ Risk Appetite")
    risk_appetite_level = st.sidebar.selectbox(
        "Organizational Risk Appetite",
        ["Low", "Medium", "High"],
        index=1,
        key="dash_appetite",
    )
    appetite_threshold = RISK_SCALE[risk_appetite_level]
    risks_over_appetite = risk_df[risk_df["risk_numeric"] > appetite_threshold]

    # ── Executive Summary ──────────────────────────────────────────────────
    st.markdown("## 🏢 Executive Summary")

    total_risks        = len(risk_df)
    critical_risks     = len(risk_df[risk_df["risk_level"] == "Critical"])
    total_controls     = len(control_df)
    implemented_ctrl   = len(control_df[control_df["implementation_status"] == "Implemented"])
    coverage_pct       = round((implemented_ctrl / total_controls) * 100, 1) if total_controls else 0
    open_findings      = len(findings_df[findings_df["status"] != "Closed"])
    overdue_findings   = int(findings_df["is_overdue"].sum())
    num_over_appetite  = len(risks_over_appetite)

    # Build insight bullets
    bullets = []
    if num_over_appetite > 0:
        risk_list = ", ".join(risks_over_appetite["risk_id"].tolist())
        bullets.append(
            f"🔴 **{num_over_appetite} risk(s)** exceed the **{risk_appetite_level}** appetite threshold: {risk_list}"
        )
    else:
        bullets.append(f"✅ All risks are within the **{risk_appetite_level}** risk appetite threshold.")

    bullets.append(
        f"🛡️ Control coverage is **{coverage_pct}%** ({implemented_ctrl} of {total_controls} controls fully implemented)."
    )

    if overdue_findings > 0:
        bullets.append(f"⚠️ **{overdue_findings} audit finding(s)** are overdue and require immediate owner action.")
    else:
        bullets.append("✅ No audit findings are currently overdue.")

    if critical_risks > 0:
        bullets.append(
            f"🚨 **{critical_risks} critical risk(s)** remain in the register — escalation and board-level reporting recommended."
        )

    bullets.append(
        f"📋 **{open_findings} finding(s)** are open across {total_controls} controls. "
        f"Focus remediation on Critical and High severity items to reduce residual risk."
    )

    with st.container():
        exec_col1, exec_col2 = st.columns([2, 1])
        with exec_col1:
            for b in bullets:
                st.markdown(f"- {b}")

        with exec_col2:
            if num_over_appetite > 0:
                st.error(f"⚠️ {num_over_appetite} Risk(s) Over Appetite")
            else:
                st.success("✅ Within Risk Appetite")

            if overdue_findings > 0:
                st.warning(f"⏰ {overdue_findings} Overdue Finding(s)")
            else:
                st.success("✅ No Overdue Findings")

            if coverage_pct < 50:
                st.error(f"🛡️ Control Coverage: {coverage_pct}%")
            elif coverage_pct < 80:
                st.warning(f"🛡️ Control Coverage: {coverage_pct}%")
            else:
                st.success(f"🛡️ Control Coverage: {coverage_pct}%")

    st.divider()

    # ── KPI Row 1: Risk ────────────────────────────────────────────────────
    st.markdown("## 📊 Key Risk Indicators")
    high_risks   = len(risk_df[risk_df["risk_level"] == "High"])
    medium_risks = len(risk_df[risk_df["risk_level"] == "Medium"])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🗂️ Total Risks",    total_risks)
    k2.metric("🔴 Critical Risks", critical_risks, delta=f"{critical_risks} requiring action", delta_color="inverse")
    k3.metric("🟠 High Risks",     high_risks)
    k4.metric("🟡 Medium Risks",   medium_risks)

    # ── KPI Row 2: Controls ────────────────────────────────────────────────
    st.markdown("## 🛡️ Control Health Indicators")
    missing_ctrl = len(control_df[control_df["implementation_status"] == "Missing"])
    partial_ctrl = len(control_df[control_df["implementation_status"] == "Partial"])

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("🛡️ Total Controls",      total_controls)
    k6.metric("✅ Implemented",          implemented_ctrl)
    k7.metric("🟠 Partial Controls",    partial_ctrl, delta_color="inverse")
    k8.metric("🔴 Missing Controls",    missing_ctrl, delta=f"-{missing_ctrl} gaps", delta_color="inverse")

    st.divider()

    # ── Risk Visuals Row ───────────────────────────────────────────────────
    st.markdown("## 📈 Risk Analysis")
    r1, r2 = st.columns(2)
    with r1:
        st.plotly_chart(ch.risk_level_pie(risk_df), use_container_width=True)
    with r2:
        st.plotly_chart(ch.risk_heatmap(risk_df), use_container_width=True)

    r3, r4 = st.columns(2)
    with r3:
        st.plotly_chart(ch.treatment_donut(risk_df), use_container_width=True)
    with r4:
        st.plotly_chart(ch.residual_risk_comparison(risk_df, control_df), use_container_width=True)

    # ── Risk Appetite Alert ────────────────────────────────────────────────
    st.markdown("## 🚦 Risk Appetite Monitoring")
    if num_over_appetite > 0:
        st.error(
            f"⚠️ **{num_over_appetite} risk(s)** exceed the defined **{risk_appetite_level}** "
            f"risk appetite. Immediate review required."
        )
        st.dataframe(
            risks_over_appetite[["risk_id", "risk_description", "asset", "risk_level", "treatment_status"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success(f"✅ All risks are within the **{risk_appetite_level}** organisational risk appetite.")

    st.divider()

    # ── Control & Governance Visuals ───────────────────────────────────────
    st.markdown("## 🏛️ Governance & Compliance Coverage")
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(ch.control_status_bar(control_df), use_container_width=True)
    with g2:
        st.plotly_chart(ch.iso_clause_coverage(control_df), use_container_width=True)

    st.plotly_chart(ch.nist_function_coverage(control_df), use_container_width=True)

    st.divider()

    # ── Findings Summary on Dashboard ──────────────────────────────────────
    st.markdown("## 🔍 Audit Findings Snapshot")
    f1, f2 = st.columns([1, 2])
    with f1:
        st.plotly_chart(ch.remediation_gauge(findings_df), use_container_width=True)
    with f2:
        st.plotly_chart(ch.findings_by_severity(findings_df), use_container_width=True)
