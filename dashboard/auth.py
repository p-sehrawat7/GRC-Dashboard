"""
dashboard/auth.py
-----------------
Enterprise authentication module — bcrypt login, role hierarchy, RBAC guard.

Default credentials (change in production):
    admin   / admin123  → role: admin
    auditor / audit123  → role: auditor
    viewer  / view123   → role: viewer
"""

import streamlit as st
import bcrypt
from database.db import get_db, init_db
from database.models import User
from utils.logger import get_logger

log = get_logger(__name__)

ROLE_HIERARCHY = {"viewer": 0, "auditor": 1, "admin": 2}


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def login_gate() -> tuple[str, str]:
    """
    Renders a clean enterprise login page and blocks until authenticated.
    Returns (username, role) on success.
    """
    init_db()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.role = ""

    if st.session_state.authenticated:
        return st.session_state.username, st.session_state.role

    # ── Login page CSS ─────────────────────────────────────────────────────────
    # Strategy: style .block-container as the white card so all Streamlit
    # widgets (which always land inside that container) are visually enclosed.
    # The outer page background is set on stAppViewContainer.
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

*, html, body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

/* ── Page background ── */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
    background-color: #F4F6F9 !important;
}

/* Hide all chrome */
[data-testid="stHeader"]         { display: none !important; }
[data-testid="stToolbar"]        { display: none !important; }
[data-testid="stDecoration"]     { display: none !important; }
[data-testid="stStatusWidget"]   { display: none !important; }
[data-testid="stMainMenuButton"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* ── The block-container IS the login card ── */
/* By styling it directly every Streamlit widget inside is visually enclosed. */
[data-testid="stAppViewContainer"] > .main > div:first-child > div:first-child > div {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
    padding: 5vh 16px 5vh;
    box-sizing: border-box;
}

.block-container {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.09) !important;
    padding: 40px 36px 32px !important;
    max-width: 420px !important;
    width: 100% !important;
    margin: auto !important;
    align-self: flex-start;
    margin-top: 10vh !important;
}

/* ── Brand row ── */
.login-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
}
.brand-badge {
    width: 38px;
    height: 38px;
    background: #1E3A5F;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.70rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.06em;
    flex-shrink: 0;
    line-height: 1;
}
.brand-title {
    font-size: 0.90rem;
    font-weight: 700;
    color: #1E293B;
    line-height: 1.2;
    margin: 0;
}
.brand-meta {
    font-size: 0.67rem;
    color: #94A3B8;
    font-weight: 400;
    margin: 2px 0 0;
}

/* ── Divider ── */
.login-divider {
    border: none;
    border-top: 1px solid #E2E8F0;
    margin: 0 0 20px;
}

/* ── Heading ── */
.login-heading {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0F172A;
    margin: 0 0 4px;
    line-height: 1.3;
}
.login-subheading {
    font-size: 0.81rem;
    color: #64748B;
    margin: 0 0 20px;
    line-height: 1.5;
}

/* ── Input fields ── */
[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    box-shadow: none !important;
}
[data-testid="stForm"] > div {
    gap: 0 !important;
}
.stTextInput > div > div > input {
    background: #F8FAFC !important;
    border: 1.5px solid #E2E8F0 !important;
    color: #0F172A !important;
    border-radius: 6px !important;
    font-size: 14px !important;
    padding: 10px 12px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    outline: none !important;
    width: 100%;
    box-sizing: border-box;
}
.stTextInput > div > div > input:focus {
    border-color: #1E3A5F !important;
    background: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.12) !important;
}
.stTextInput > div > div > input::placeholder { color: #CBD5E1 !important; }
.stTextInput label {
    color: #374151 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}

/* ── Remember me ── */
.stCheckbox label p,
.stCheckbox span {
    font-size: 13px !important;
    color: #475569 !important;
    font-weight: 400 !important;
}

/* ── Sign In button ── */
[data-testid="stFormSubmitButton"] > button {
    background: #1E3A5F !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 11px 0 !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: background 0.15s ease !important;
    margin-top: 4px !important;
    letter-spacing: 0.01em !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: #2A4F7C !important;
}
[data-testid="stFormSubmitButton"] > button p,
[data-testid="stFormSubmitButton"] > button span {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* ── Error / alert ── */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    margin-top: 8px !important;
    font-size: 13px !important;
}

/* ── Security notice ── */
.security-notice {
    text-align: center;
    font-size: 0.71rem;
    color: #94A3B8;
    margin-top: 14px;
    line-height: 1.5;
    padding-bottom: 4px;
}

/* ── Footer (below card) ── */
.login-footer-wrap {
    max-width: 420px;
    margin: 16px auto 0;
    text-align: center;
}
.login-footer-text {
    font-size: 0.69rem;
    color: #9BB0C1;
    letter-spacing: 0.01em;
}
</style>
""", unsafe_allow_html=True)

    # ── Brand + headings (inside card, above the form) ──────────────────────
    st.markdown("""
<div class="login-brand">
    <div class="brand-badge">GRC</div>
    <div>
        <p class="brand-title">Enterprise GRC Dashboard</p>
        <p class="brand-meta">ISO 27001 &bull; NIST CSF &bull; v3.0</p>
    </div>
</div>
<hr class="login-divider">
<p class="login-heading">Sign in to continue</p>
<p class="login-subheading">Enter your credentials to access the platform.</p>
""", unsafe_allow_html=True)

    # ── Form (Streamlit renders this inside .block-container = inside the card) ──
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        st.checkbox("Remember me", key="remember_me")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

    # Security notice — still inside the card (inside .block-container)
    st.markdown(
        '<div class="security-notice">'
        "Access to this system is monitored and logged."
        "</div>",
        unsafe_allow_html=True,
    )

    # Footer — outside the card in spirit but physically still in block-container;
    # visual separation achieved by top margin and lighter colour.
    st.markdown(
        '<div class="login-footer-wrap">'
        '<span class="login-footer-text">&copy; 2026 GRC Enterprise Platform</span>'
        "</div>",
        unsafe_allow_html=True,
    )

    if submitted:
        hashed_pw = None
        user_role = None
        with get_db() as db:
            user = db.query(User).filter(User.username == username).first()
            if user:
                hashed_pw = user.hashed_password
                user_role = user.role

        if hashed_pw and _verify_password(password, hashed_pw):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.role = user_role
            log.info(f"LOGIN success: {username} ({user_role})")
            st.rerun()
        else:
            log.warning(f"LOGIN failed: {username}")
            st.error(
                "Invalid credentials. Please contact your system administrator."
            )

    st.stop()
    return "", ""




def logout() -> None:
    """Clear authentication state and rerun."""
    log.info(f"LOGOUT: {st.session_state.get('username', 'unknown')}")
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()


def require_role(min_role: str) -> bool:
    """
    Returns True if the current user meets or exceeds the required role.
    Displays an access-denied warning and returns False otherwise.
    """
    current = st.session_state.get("role", "viewer")
    if ROLE_HIERARCHY.get(current, 0) >= ROLE_HIERARCHY.get(min_role, 0):
        return True
    st.warning(
        f"Access restricted. This action requires **{min_role}** role or above. "
        f"Your current role is **{current}**."
    )
    return False
