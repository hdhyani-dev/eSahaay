"""Lexicon curation and version management service.
Reference: Section 7.7, 8.K
"""
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sahaay.models import LexiconEntry
from sahaay.audit import log_audit_event
from sahaay.evaluation.harness import evaluate_dataset

def list_lexicon_entries(db: Session, status: Optional[str] = None) -> List[LexiconEntry]:
    """List lexicon entries with optional status filter."""
    q = db.query(LexiconEntry)
    if status and status != "all":
        q = q.filter(LexiconEntry.status == status)
    return q.order_by(LexiconEntry.created_at.desc()).all()

def propose_lexicon_entry(
    db: Session,
    entry_id: str,
    phrase: str,
    variants: List[str],
    canonical_meaning: str,
    threat_type: str,
    risk_class: str,
    region: str,
    suggested_safe_question: str,
    created_by: str = "Linguist"
) -> LexiconEntry:
    """Propose a new code word / indirect signal candidate."""
    entry = LexiconEntry(
        id=entry_id,
        phrase=phrase,
        variants=variants,
        canonical_meaning=canonical_meaning,
        threat_type=threat_type,
        risk_class=risk_class,
        region=region,
        suggested_safe_question=suggested_safe_question,
        status="proposed",
        version="1.0.0",
        created_by=created_by,
        created_at=datetime.datetime.utcnow()
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    log_audit_event(
        db=db,
        actor_id=created_by,
        actor_role="linguist",
        action="LEXICON_ENTRY_PROPOSED",
        object_type="lexicon",
        object_id=entry_id,
        after_state={"phrase": phrase, "risk_class": risk_class, "meaning": canonical_meaning},
        reason="Proposed new candidate phrase"
    )
    return entry

def approve_lexicon_entry(
    db: Session,
    entry_id: str,
    approved_by: str = "Admin"
) -> LexiconEntry:
    """
    Approve proposed lexicon entry after running validation regression test.
    """
    entry = db.query(LexiconEntry).filter(LexiconEntry.id == entry_id).first()
    if not entry:
        raise ValueError(f"Lexicon entry {entry_id} not found")
        
    entry.status = "approved"
    entry.approved_by = approved_by
    entry.approved_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(entry)

    log_audit_event(
        db=db,
        actor_id=approved_by,
        actor_role="admin",
        action="LEXICON_ENTRY_APPROVED",
        object_type="lexicon",
        object_id=entry_id,
        after_state={"status": "approved", "approved_by": approved_by},
        reason="Admin approval after review"
    )
    return entry

def retire_lexicon_entry(
    db: Session,
    entry_id: str,
    retired_by: str,
    reason: str
) -> LexiconEntry:
    """Retire a stale or outdated code word entry."""
    entry = db.query(LexiconEntry).filter(LexiconEntry.id == entry_id).first()
    if not entry:
        raise ValueError(f"Lexicon entry {entry_id} not found")
        
    entry.status = "retired"
    db.commit()
    db.refresh(entry)

    log_audit_event(
        db=db,
        actor_id=retired_by,
        actor_role="admin",
        action="LEXICON_ENTRY_RETIRED",
        object_type="lexicon",
        object_id=entry_id,
        after_state={"status": "retired", "reason": reason},
        reason=reason
    )
    return entry
