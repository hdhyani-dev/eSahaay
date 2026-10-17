"""Test immutable audit log creation, role permissions, and persistence.
Reference: Prompt Section 6.L, Section 13
"""
import pytest
from sqlalchemy.orm import Session
from sahaay.database import SessionLocal, init_database
from sahaay.models import AuditEvent, Incident
from sahaay.audit import log_audit_event
from sahaay.permissions import has_permission, can_access_page

@pytest.fixture
def db_session():
    init_database()
    db = SessionLocal()
    yield db
    db.close()

def test_audit_event_logging(db_session: Session):
    event = log_audit_event(
        db=db_session,
        actor_id="OP1042",
        actor_role="operator",
        action="TEST_ACTION",
        object_type="incident",
        object_id="TEST-INC-999",
        before_state={"status": "active"},
        after_state={"status": "resolved"},
        reason="Unit test verification"
    )
    assert event.id is not None
    assert event.actor_id == "OP1042"
    assert event.action == "TEST_ACTION"

    # Verify query
    saved = db_session.query(AuditEvent).filter(AuditEvent.id == event.id).first()
    assert saved is not None
    assert saved.reason == "Unit test verification"

    # Clean up test event
    db_session.delete(saved)
    db_session.commit()

def test_role_permissions_matrix():
    # Operator can view queue, cannot approve lexicon
    assert has_permission("operator", "view_live_queue") is True
    assert has_permission("operator", "approve_lexicon") is False

    # Admin can approve lexicon and manage users
    assert has_permission("admin", "approve_lexicon") is True
    assert has_permission("admin", "manage_users") is True

    # Page access rules
    assert can_access_page("operator", "triage") is True
    assert can_access_page("operator", "admin") is False
    assert can_access_page("admin", "admin") is True
    assert can_access_page("judge", "eval") is True
