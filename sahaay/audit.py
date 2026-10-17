"""Append-only audit trail logging for operator accountability."""
import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sahaay.models import AuditEvent

def log_audit_event(
    db: Session,
    actor_id: str,
    actor_role: str,
    action: str,
    object_type: str,
    object_id: str,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    ip_address: str = "127.0.0.1"
) -> AuditEvent:
    """Write an immutable audit log entry to the database."""
    event = AuditEvent(
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        object_type=object_type,
        object_id=object_id,
        before_state=before_state,
        after_state=after_state,
        reason=reason,
        ip_address=ip_address,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
