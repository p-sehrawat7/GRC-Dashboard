"""
filters.py
----------
Reusable Streamlit sidebar filter widgets for each data domain.
Each function returns a filtered DataFrame based on user selections.
"""

import streamlit as st
import pandas as pd
from typing import Tuple


def risk_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Render sidebar multi-select filters for the Risk Register and return filtered df.

    Args:
        df: Full risk register DataFrame.

    Returns:
        Filtered DataFrame based on user selections.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Risk Filters")

    # Asset filter
    assets = sorted(df["asset"].dropna().unique().tolist())
    selected_assets = st.sidebar.multiselect(
        "Filter by Asset", options=assets, default=assets, key="risk_asset"
    )

    # Risk Level filter
    levels = ["Critical", "High", "Medium", "Low"]
    selected_levels = st.sidebar.multiselect(
        "Filter by Risk Level", options=levels, default=levels, key="risk_level_filter"
    )

    # Treatment Status filter — fixed order so "Resolved" always appears
    all_statuses = ["Resolved", "Mitigated", "In Progress", "Accepted", "Transferred", "Avoided"]
    statuses = [s for s in all_statuses if s in df["treatment_status"].dropna().unique()] + \
               [s for s in df["treatment_status"].dropna().unique() if s not in all_statuses]
    selected_statuses = st.sidebar.multiselect(
        "Filter by Treatment Status", options=statuses, default=statuses, key="risk_treatment"
    )

    # NIST Function filter
    nist_funcs = sorted(df["nist_function"].dropna().unique().tolist())
    selected_nist = st.sidebar.multiselect(
        "Filter by NIST Function", options=nist_funcs, default=nist_funcs, key="risk_nist"
    )

    filtered = df[
        df["asset"].isin(selected_assets) &
        df["risk_level"].isin(selected_levels) &
        df["treatment_status"].isin(selected_statuses) &
        df["nist_function"].isin(selected_nist)
    ]
    return filtered


def control_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Render sidebar multi-select filters for the Control Matrix and return filtered df.

    Args:
        df: Full control matrix DataFrame.

    Returns:
        Filtered DataFrame based on user selections.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Control Filters")

    # Control Type filter
    ctypes = sorted(df["control_type"].dropna().unique().tolist())
    selected_types = st.sidebar.multiselect(
        "Filter by Control Type", options=ctypes, default=ctypes, key="ctrl_type"
    )

    # Implementation Status filter
    impl_statuses = ["Implemented", "Partial", "Missing"]
    selected_impl = st.sidebar.multiselect(
        "Filter by Implementation Status", options=impl_statuses,
        default=impl_statuses, key="ctrl_impl"
    )

    # NIST Function filter
    nist_funcs = sorted(df["nist_function"].dropna().unique().tolist())
    selected_nist = st.sidebar.multiselect(
        "Filter by NIST Function", options=nist_funcs, default=nist_funcs, key="ctrl_nist"
    )

    filtered = df[
        df["control_type"].isin(selected_types) &
        df["implementation_status"].isin(selected_impl) &
        df["nist_function"].isin(selected_nist)
    ]
    return filtered


def findings_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """
    Render sidebar filters for the Audit Findings module.

    Args:
        df: Full audit findings DataFrame.

    Returns:
        Tuple of (filtered DataFrame, show_overdue_only flag).
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Findings Filters")

    # Severity filter
    severities = ["Critical", "High", "Medium", "Low"]
    selected_sev = st.sidebar.multiselect(
        "Filter by Severity", options=severities, default=severities, key="find_sev"
    )

    # Status filter
    statuses = sorted(df["status"].dropna().unique().tolist())
    selected_status = st.sidebar.multiselect(
        "Filter by Status", options=statuses, default=statuses, key="find_status"
    )

    # Owner filter
    owners = sorted(df["owner"].dropna().unique().tolist())
    selected_owners = st.sidebar.multiselect(
        "Filter by Owner", options=owners, default=owners, key="find_owner"
    )

    # Overdue toggle
    show_overdue = st.sidebar.checkbox("Show Overdue Only", value=False, key="find_overdue")

    filtered = df[
        df["severity"].isin(selected_sev) &
        df["status"].isin(selected_status) &
        df["owner"].isin(selected_owners)
    ]

    if show_overdue:
        filtered = filtered[filtered["is_overdue"] == True]

    return filtered, show_overdue
