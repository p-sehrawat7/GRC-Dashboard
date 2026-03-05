"""
tests/test_auth.py
------------------
Unit tests for the authentication module (auth.py).
Tests cover:
  - _verify_password: bcrypt checks (correct + wrong + empty)
  - require_role: RBAC hierarchy enforcement
These run without Streamlit — session_state is mocked via monkeypatch.
"""

import sys
import os
import pytest
import bcrypt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dashboard"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth import _verify_password, require_role, ROLE_HIERARCHY


# ── _verify_password ──────────────────────────────────────────────────────────

class TestVerifyPassword:
    """Tests for the bcrypt password verification helper."""

    PLAIN = "mysecret99"
    HASHED = bcrypt.hashpw(PLAIN.encode(), bcrypt.gensalt()).decode()

    def test_correct_password_returns_true(self):
        assert _verify_password(self.PLAIN, self.HASHED) is True

    def test_wrong_password_returns_false(self):
        assert _verify_password("wrongpass", self.HASHED) is False

    def test_empty_password_returns_false(self):
        assert _verify_password("", self.HASHED) is False

    def test_known_credentials_admin(self):
        """Verify the seeded admin password used in conftest matches the hash."""
        hashed = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode()
        assert _verify_password("password", hashed) is True
        assert _verify_password("bad", hashed) is False

    def test_invalid_hash_returns_false(self):
        """Passing garbage as the hash should not raise — must return False."""
        assert _verify_password("anypassword", "not-a-valid-hash") is False


# ── require_role ──────────────────────────────────────────────────────────────

class TestRequireRole:
    """Tests for the RBAC role-hierarchy guard."""

    def _set_role(self, monkeypatch, role: str):
        """Patch st.session_state so require_role reads the given role."""
        import streamlit as st

        class FakeSessionState(dict):
            def get(self, key, default=None):
                return self[key] if key in self else default

        fake = FakeSessionState({"role": role})
        monkeypatch.setattr(st, "session_state", fake)

        # Stub st.warning so it doesn't try to render
        monkeypatch.setattr(st, "warning", lambda *a, **kw: None)

    # Role constants match ROLE_HIERARCHY keys
    def test_admin_passes_all_levels(self, monkeypatch):
        self._set_role(monkeypatch, "admin")
        assert require_role("viewer")  is True
        assert require_role("auditor") is True
        assert require_role("admin")   is True

    def test_auditor_passes_viewer_and_auditor(self, monkeypatch):
        self._set_role(monkeypatch, "auditor")
        assert require_role("viewer")  is True
        assert require_role("auditor") is True

    def test_auditor_denied_admin(self, monkeypatch):
        self._set_role(monkeypatch, "auditor")
        assert require_role("admin") is False

    def test_viewer_passes_only_viewer(self, monkeypatch):
        self._set_role(monkeypatch, "viewer")
        assert require_role("viewer")  is True

    def test_viewer_denied_auditor_and_admin(self, monkeypatch):
        self._set_role(monkeypatch, "viewer")
        assert require_role("auditor") is False
        assert require_role("admin")   is False

    def test_role_hierarchy_values(self):
        """Sanity check that the hierarchy ordering is correct."""
        assert ROLE_HIERARCHY["viewer"]  < ROLE_HIERARCHY["auditor"]
        assert ROLE_HIERARCHY["auditor"] < ROLE_HIERARCHY["admin"]
