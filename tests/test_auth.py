"""Test authentication, password security, and role permissions."""
import pytest
from sahaay.auth import hash_password, verify_password
from sahaay.permissions import has_permission, can_access_page, ROLES

def test_password_hashing_and_verification():
    raw = "operator_secret_2026"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_role_permissions_matrix():
    # Operator can view queue and override urgency, but cannot approve repeat links
    assert has_permission("operator", "view_live_queue") is True
    assert has_permission("operator", "confirm_override_urgency") is True
    assert has_permission("operator", "approve_undo_repeat_links") is False

    # Supervisor can approve repeat links and export audit log
    assert has_permission("supervisor", "approve_undo_repeat_links") is True
    assert has_permission("supervisor", "export_audit_log") is True

    # Linguist can edit lexicon
    assert has_permission("linguist", "edit_lexicon") is True
    assert has_permission("linguist", "view_live_queue") is False

    # Admin can change thresholds and manage users
    assert has_permission("admin", "change_thresholds_models") is True
    assert has_permission("admin", "manage_users") is True

def test_page_access_control():
    assert can_access_page("operator", "triage") is True
    assert can_access_page("linguist", "triage") is False
    assert can_access_page("linguist", "lexicon") is True
    assert can_access_page("admin", "admin") is True
    assert can_access_page("operator", "admin") is False
