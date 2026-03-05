"""
charts.py
---------
All Plotly chart-building functions for the GRC Audit Simulation Dashboard.
Each function accepts a DataFrame and returns a Plotly Figure object.
Charts are decoupled from Streamlit layout logic for testability and reuse.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_loader import (
    RISK_COLORS, CONTROL_COLORS, NIST_COLORS, RISK_SCALE
)

CHART_HEIGHT = 420


# ─── Risk Charts ──────────────────────────────────────────────────────────────

def risk_level_pie(df: pd.DataFrame) -> go.Figure:
    """
    Donut chart showing distribution of risks by risk level.

    Args:
        df: Risk register DataFrame.

    Returns:
        Plotly Figure.
    """
    counts = df["risk_level"].value_counts().reset_index()
    counts.columns = ["Risk Level", "Count"]

    fig = px.pie(
        counts,
        names="Risk Level",
        values="Count",
        hole=0.45,
        color="Risk Level",
        color_discrete_map=RISK_COLORS,
        title="Risk Level Distribution",
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(
        height=CHART_HEIGHT,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(t=40, b=60),
    )
    return fig


def risk_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Heatmap of risk counts at each Impact × Likelihood intersection.

    Args:
        df: Risk register DataFrame.

    Returns:
        Plotly Figure (imshow).
    """
    pivot = df.pivot_table(
        index="impact",
        columns="likelihood",
        values="risk_score",
        aggfunc="count",
        fill_value=0,
    )

    fig = px.imshow(
        pivot,
        text_auto=True,
        color_continuous_scale="Reds",
        labels={"x": "Likelihood", "y": "Impact", "color": "Risk Count"},
        title="Risk Heatmap (Impact × Likelihood)",
    )
    fig.update_layout(
        height=CHART_HEIGHT,
        xaxis_title="Likelihood",
        yaxis_title="Impact",
        margin=dict(t=40),
    )
    return fig


def treatment_donut(df: pd.DataFrame) -> go.Figure:
    """
    Donut chart showing Risk Treatment Strategy breakdown.

    Args:
        df: Risk register DataFrame.

    Returns:
        Plotly Figure.
    """
    counts = df["treatment_status"].value_counts().reset_index()
    counts.columns = ["Treatment Strategy", "Count"]

    color_map = {
        "Mitigated":   "#388E3C",
        "In Progress": "#F57C00",
        "Accepted":    "#1565C0",
        "Transferred": "#7B1FA2",
        "Avoided":     "#546E7A",
    }

    fig = px.pie(
        counts,
        names="Treatment Strategy",
        values="Count",
        hole=0.5,
        color="Treatment Strategy",
        color_discrete_map=color_map,
        title="Risk Treatment Strategy",
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(
        height=CHART_HEIGHT,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(t=40, b=60),
    )
    return fig


def residual_risk_comparison(risk_df: pd.DataFrame, control_df: pd.DataFrame) -> go.Figure:
    """
    Grouped bar chart comparing inherent risk level vs residual risk level
    after controls for each risk ID.

    Args:
        risk_df: Risk register DataFrame.
        control_df: Control matrix DataFrame.

    Returns:
        Plotly Figure.
    """
    merged = pd.merge(
        risk_df,
        control_df[["mapped_risk_id", "risk_level_after_control"]].drop_duplicates("mapped_risk_id"),
        left_on="risk_id",
        right_on="mapped_risk_id",
        how="left",
    )

    merged["inherent_score"] = merged["risk_level"].map(RISK_SCALE)
    merged["residual_score"] = merged["risk_level_after_control"].map(RISK_SCALE)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=merged["risk_id"],
        y=merged["inherent_score"],
        name="Inherent Risk",
        marker_color="#D32F2F",
        text=merged["risk_level"],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        x=merged["risk_id"],
        y=merged["residual_score"],
        name="Residual Risk",
        marker_color="#388E3C",
        text=merged["risk_level_after_control"],
        textposition="outside",
    ))
    fig.update_layout(
        title="Residual Risk – Before vs After Controls",
        barmode="group",
        height=CHART_HEIGHT,
        yaxis=dict(tickvals=[1, 2, 3, 4], ticktext=["Low", "Medium", "High", "Critical"]),
        xaxis_title="Risk ID",
        yaxis_title="Risk Level",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        margin=dict(t=40, b=80),
    )
    return fig


# ─── Control Charts ───────────────────────────────────────────────────────────

def control_status_bar(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart of control implementation status counts.

    Args:
        df: Control matrix DataFrame.

    Returns:
        Plotly Figure.
    """
    counts = df["implementation_status"].value_counts().reset_index()
    counts.columns = ["Status", "Count"]

    fig = px.bar(
        counts,
        x="Count",
        y="Status",
        orientation="h",
        color="Status",
        color_discrete_map=CONTROL_COLORS,
        text="Count",
        title="Control Implementation Status",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=CHART_HEIGHT,
        showlegend=False,
        margin=dict(t=40),
        xaxis_title="Number of Controls",
    )
    return fig


def iso_clause_coverage(df: pd.DataFrame) -> go.Figure:
    """
    Grouped bar chart showing ISO 27001 clause coverage by implementation status.

    Args:
        df: Control matrix DataFrame.

    Returns:
        Plotly Figure.
    """
    grouped = (
        df.groupby(["iso_clause", "implementation_status"])
        .size()
        .reset_index(name="Count")
    )
    fig = px.bar(
        grouped,
        x="iso_clause",
        y="Count",
        color="implementation_status",
        barmode="group",
        color_discrete_map=CONTROL_COLORS,
        title="ISO 27001 Clause Coverage",
        labels={"iso_clause": "ISO 27001 Clause", "Count": "Controls"},
    )
    fig.update_layout(
        height=CHART_HEIGHT,
        xaxis_title="ISO 27001 Clause",
        yaxis_title="Number of Controls",
        legend_title="Status",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        margin=dict(t=40, b=80),
    )
    return fig


def nist_function_coverage(df: pd.DataFrame) -> go.Figure:
    """
    Stacked bar chart showing control counts per NIST CSF function,
    broken down by implementation status.

    Args:
        df: Control matrix DataFrame (risk or control df with nist_function column).

    Returns:
        Plotly Figure.
    """
    nist_order = ["Identify", "Protect", "Detect", "Respond", "Recover"]
    grouped = (
        df.groupby(["nist_function", "implementation_status"])
        .size()
        .reset_index(name="Count")
    )

    # Ensure all NIST functions appear
    fig = px.bar(
        grouped,
        x="nist_function",
        y="Count",
        color="implementation_status",
        barmode="stack",
        color_discrete_map=CONTROL_COLORS,
        category_orders={"nist_function": nist_order},
        title="NIST CSF Function Coverage",
        labels={"nist_function": "NIST CSF Function", "Count": "Controls"},
    )
    fig.update_layout(
        height=CHART_HEIGHT,
        xaxis_title="NIST CSF Function",
        yaxis_title="Number of Controls",
        legend_title="Status",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        margin=dict(t=40, b=80),
    )
    return fig


# ─── Audit Findings Charts ────────────────────────────────────────────────────

def findings_by_severity(df: pd.DataFrame) -> go.Figure:
    """
    Bar chart of open audit findings grouped by severity.

    Args:
        df: Audit findings DataFrame (filtered to open if desired).

    Returns:
        Plotly Figure.
    """
    sev_order = ["Critical", "High", "Medium", "Low"]
    counts = (
        df[df["status"] != "Closed"]["severity"]
        .value_counts()
        .reindex(sev_order, fill_value=0)
        .reset_index()
    )
    counts.columns = ["Severity", "Count"]

    fig = px.bar(
        counts,
        x="Severity",
        y="Count",
        color="Severity",
        color_discrete_map=RISK_COLORS,
        text="Count",
        title="Open Findings by Severity",
        category_orders={"Severity": sev_order},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=CHART_HEIGHT,
        showlegend=False,
        margin=dict(t=40),
        yaxis_title="Count",
    )
    return fig


def findings_status_donut(df: pd.DataFrame) -> go.Figure:
    """
    Donut chart showing the distribution of findings by status.

    Args:
        df: Audit findings DataFrame.

    Returns:
        Plotly Figure.
    """
    status_colors = {
        "Open":          "#D32F2F",
        "In Remediation":"#F57C00",
        "Closed":        "#388E3C",
    }
    counts = df["status"].value_counts().reset_index()
    counts.columns = ["Status", "Count"]

    fig = px.pie(
        counts,
        names="Status",
        values="Count",
        hole=0.5,
        color="Status",
        color_discrete_map=status_colors,
        title="Findings by Status",
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(
        height=CHART_HEIGHT,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(t=40, b=60),
    )
    return fig


def remediation_gauge(df: pd.DataFrame) -> go.Figure:
    """
    Gauge chart showing remediation progress (% of findings Closed).

    Args:
        df: Audit findings DataFrame.

    Returns:
        Plotly Figure (indicator gauge).
    """
    total   = len(df)
    closed  = len(df[df["status"] == "Closed"])
    pct     = round((closed / total) * 100, 1) if total > 0 else 0

    color = "#388E3C" if pct >= 70 else ("#F57C00" if pct >= 40 else "#D32F2F")

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        title={"text": "Remediation Progress (% Closed)", "font": {"size": 16}},
        number={"suffix": "%", "font": {"size": 36}},
        delta={"reference": 70, "increasing": {"color": "#388E3C"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar":  {"color": color},
            "steps": [
                {"range": [0,   40], "color": "#FFCDD2"},
                {"range": [40,  70], "color": "#FFE0B2"},
                {"range": [70, 100], "color": "#C8E6C9"},
            ],
            "threshold": {
                "line": {"color": "#1565C0", "width": 3},
                "thickness": 0.75,
                "value": 70,
            },
        },
    ))
    fig.update_layout(height=280, margin=dict(t=40, b=20, l=30, r=30))
    return fig


def overdue_findings_bar(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart showing overdue findings by owner.

    Args:
        df: Audit findings DataFrame with is_overdue column.

    Returns:
        Plotly Figure.
    """
    overdue = df[df["is_overdue"] == True]

    if overdue.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="✅ No overdue findings!",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, color="#388E3C"),
        )
        fig.update_layout(height=200, margin=dict(t=40))
        return fig

    by_owner = overdue["owner"].value_counts().reset_index()
    by_owner.columns = ["Owner", "Overdue Count"]

    fig = px.bar(
        by_owner,
        x="Overdue Count",
        y="Owner",
        orientation="h",
        color_discrete_sequence=["#D32F2F"],
        text="Overdue Count",
        title="Overdue Findings by Owner",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=CHART_HEIGHT,
        showlegend=False,
        margin=dict(t=40),
        xaxis_title="Overdue Findings",
    )
    return fig
