"""
app.py
------
GRC Audit Simulation Dashboard — Main Entry Point
Aligned with ISO 27001 & NIST CSF

Run with:
    streamlit run dashboard/app.py
    (from the d:/grc-dashboard directory)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

# ── Page Configuration (must be first Streamlit call) ─────────────────────────
st.set_page_config(
    page_title="GRC Audit Simulation Dashboard",
    page_icon="assets/favicon.ico" if os.path.exists(
        os.path.join(os.path.dirname(__file__), "assets", "favicon.ico")) else None,
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth import login_gate, logout, require_role
from utils.data_loader import load_risk_data, load_control_data, load_audit_findings
import views.dashboard      as pg_dashboard
import views.risk_register  as pg_risk
import views.control_matrix as pg_control
import views.audit_findings as pg_findings

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s;
}
[data-testid="metric-container"]:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E3A5F 0%, #162d4a 100%);
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown div,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] .stButton button { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stRadio label { font-weight: 600; font-size: 14px; }

/* ── Form inputs — ensure visible dark-text on white background ── */
.stTextInput input,
.stTextArea textarea,
.stSelectbox select,
.stNumberInput input {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 6px !important;
}
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stSlider label,
.stNumberInput label,
.stForm label,
.stForm p,
div[data-testid="stForm"] label {
    color: #1e293b !important;
    font-weight: 500 !important;
}
/* Expander — collapsed state: white background, navy border */
details {
    background: #ffffff !important;
    border: 1.5px solid #1E3A5F !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
/* Expander collapsed summary text */
details > summary {
    background: #f8fafc !important;
    border-radius: 8px;
    padding: 10px 14px;
    cursor: pointer;
}
details > summary p,
details > summary span {
    color: #1E3A5F !important;
    font-weight: 700 !important;
    font-size: 15px !important;
}
/* Expander open — navy header + blue-tinted body */
details[open] > summary {
    background: #1E3A5F !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 10px 14px;
}
details[open] > summary p,
details[open] > summary span {
    color: #ffffff !important;
    font-weight: 700 !important;
}
details[open] {
    background: #EFF6FF !important;
    border-left: 4px solid #1E3A5F !important;
    border-radius: 0 8px 8px 0 !important;
}


/* ── Section headers ── */
h1 { color: #1E3A5F; font-weight: 700; }
h2 { color: #1E3A5F; font-weight: 700; padding-top: 0.4rem !important; }
h3 { color: #1E3A5F; font-weight: 600; }

/* ── Data table ── */
.stDataFrame { font-size: 13px; border-radius: 8px; }

/* ── Dividers ── */
hr { margin: 0.8rem 0; border-color: #e2e8f0; }

/* ── Buttons (nav buttons) ── */
.stButton > button {
    background: #1E3A5F !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}
.stButton > button:hover { background: #2a5080 !important; color: #ffffff !important; }

/* ── Form submit buttons ── */
[data-testid="stFormSubmitButton"] > button {
    background: #1E3A5F !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    width: 100%;
}
[data-testid="stFormSubmitButton"] > button p,
[data-testid="stFormSubmitButton"] > button span {
    color: #ffffff !important;
    font-weight: 700 !important;
}
[data-testid="stFormSubmitButton"] > button:hover { background: #2a5080 !important; }
[data-testid="stFormSubmitButton"] > button:hover p { color: #ffffff !important; }


/* ── Download buttons ── */
[data-testid="stDownloadButton"] > button {
    background: #1E3A5F; color: white; border: none;
    border-radius: 6px; font-weight: 600;
}
[data-testid="stDownloadButton"] > button:hover { background: #2a5080; }

/* ── Forms ── */
[data-testid="stForm"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
}

/* ── Status badges (expanders) ── */
.stExpander { border: 1px solid #e2e8f0 !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Authentication ─────────────────────────────────────────────────────────────
username, role = login_gate()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:4px;
            padding:12px 0;border-bottom:2px solid #1E3A5F">
    <div style="background:#1E3A5F;color:white;padding:8px 14px;border-radius:8px;
                font-size:1.1rem;font-weight:700;letter-spacing:0.05em">GRC</div>
    <div>
        <div style="font-size:1.5rem;font-weight:700;color:#1E3A5F;line-height:1">
            Audit Simulation Dashboard
        </div>
        <div style="color:#64748b;font-size:0.85rem;margin-top:2px">
            ISO 27001 &amp; NIST CSF &nbsp;&bull;&nbsp; Risk Management &nbsp;&bull;&nbsp;
            Control Assessment &nbsp;&bull;&nbsp; Audit Findings
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div style="text-align:center;padding:12px 0 8px 0">
    <div style="font-size:1.6rem;font-weight:800;letter-spacing:0.08em">GRC</div>
    <div style="font-size:0.75rem;opacity:0.75">v3.0 &bull; ISO 27001 &bull; NIST CSF</div>
    <div style="margin-top:8px;padding:4px 10px;background:rgba(255,255,255,0.15);
                border-radius:6px;font-size:0.8rem">
        {username} &nbsp;&bull;&nbsp; <em>{role}</em>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.markdown("### Navigation")

page = st.sidebar.radio(
    "Select Page",
    ["Dashboard", "Risk Register", "Control Matrix", "Audit Findings"],
    key="main_nav",
)
st.sidebar.divider()
if st.sidebar.button("Sign Out", key="signout"):
    logout()

st.sidebar.markdown(
    "<div style='font-size:0.7rem;opacity:0.6;text-align:center;margin-top:8px'>"
    "GRC Simulation &copy; 2026 | Portfolio Use Only</div>",
    unsafe_allow_html=True,
)

# ── Data Loading ──────────────────────────────────────────────────────────────
try:
    risk_df     = load_risk_data()
    control_df  = load_control_data()
    findings_df = load_audit_findings()
except (FileNotFoundError, ValueError) as e:
    st.error(f"Data error: {e}  \nRun `python database/seed.py` to populate the database.")
    st.stop()

# ── Page Routing ──────────────────────────────────────────────────────────────
if page == "Dashboard":
    pg_dashboard.render(risk_df, control_df, findings_df)

elif page == "Risk Register":
    pg_risk.render(risk_df, username=username, role=role)

elif page == "Control Matrix":
    pg_control.render(control_df, username=username, role=role)

elif page == "Audit Findings":
    pg_findings.render(risk_df, control_df, findings_df, username=username, role=role)