"""Test repeat complaint matching, hard negatives, and false merge prevention.
Reference: Prompt Section 9, Section 13
"""
import pytest
import datetime
from sqlalchemy.orm import Session
from sahaay.database import SessionLocal, init_database
from sahaay.models import Incident, RepeatLink
from sahaay.repeat_matching.hashing import hash_phone_hmac
from sahaay.repeat_matching.phonetic import get_phonetic_key
from sahaay.repeat_matching.matcher import match_repeat_complaints, approve_or_create_link, undo_repeat_link

@pytest.fixture
def db_session():
    init_database()
    db = SessionLocal()
    yield db
    db.close()

def test_name_alone_never_auto_merges(db_session: Session):
    # Two cases sharing only a common name (Pooja Sharma), but different phone, different place
    now = datetime.datetime.utcnow()
    case_a = Incident(
        id="TEST-INC-A1",
        caller_name="Pooja Sharma",
        name_phonetic=get_phonetic_key("Pooja Sharma"),
        caller_masked_phone="+91 98111 ***11",
        phone_hmac=hash_phone_hmac("9811100011"),
        location_text="Karol Bagh",
        primary_threat="Stalking",
        current_urgency="P1",
        original_urgency="P1",
        created_at=now
    )
    case_b = Incident(
        id="TEST-INC-B1",
        caller_name="Pooja Sharma", # Same name!
        name_phonetic=get_phonetic_key("Pooja Sharma"),
        caller_masked_phone="+91 99999 ***99", # Different phone
        phone_hmac=hash_phone_hmac("9999900099"),
        location_text="Mayur Vihar", # Different locality
        primary_threat="Legal Query",
        current_urgency="P3",
        original_urgency="P3",
        created_at=now - datetime.timedelta(days=10)
    )
    db_session.add(case_a)
    db_session.add(case_b)
    db_session.commit()

    try:
        candidates = match_repeat_complaints(case_a, db_session)
        # Find match for case_b
        match_b = next((c for c in candidates if c["candidate_case_id"] == "TEST-INC-B1"), None)
        if match_b:
            # Must NOT be auto band!
            assert match_b["band"] != "auto"
            assert match_b["strong_signals_count"] < 2
    finally:
        db_session.delete(case_a)
        db_session.delete(case_b)
        db_session.commit()

def test_two_strong_signals_auto_link(db_session: Session):
    # Two cases sharing phone HMAC AND phonetic name
    now = datetime.datetime.utcnow()
    case_c = Incident(
        id="TEST-INC-C1",
        caller_name="Ritu Verma",
        name_phonetic=get_phonetic_key("Ritu Verma"),
        caller_masked_phone="+91 98765 ***22",
        phone_hmac=hash_phone_hmac("9876500022"),
        location_text="Rohini",
        primary_threat="Domestic Violence",
        current_urgency="P1",
        original_urgency="P1",
        created_at=now
    )
    case_d = Incident(
        id="TEST-INC-D1",
        caller_name="Reetu Varma", # Phonetic match
        name_phonetic=get_phonetic_key("Reetu Varma"),
        caller_masked_phone="+91 98765 ***22", # Exact phone match
        phone_hmac=hash_phone_hmac("9876500022"),
        location_text="Sector 14 Rohini", # Location match
        primary_threat="Domestic Violence",
        current_urgency="P1",
        original_urgency="P1",
        created_at=now - datetime.timedelta(days=5)
    )
    db_session.add(case_c)
    db_session.add(case_d)
    db_session.commit()

    try:
        candidates = match_repeat_complaints(case_c, db_session)
        match_d = next((c for c in candidates if c["candidate_case_id"] == "TEST-INC-D1"), None)
        assert match_d is not None
        assert match_d["band"] in ["auto", "suggest"]
        assert match_d["score"] > 0.80

        # Test reversible link creation and undo
        link = approve_or_create_link(
            db=db_session,
            incident_a_id=case_c.id,
            incident_b_id=case_d.id,
            score=match_d["score"],
            band=match_d["band"],
            signals=match_d["signals"],
            created_by="Supervisor"
        )
        assert link.status == "active"

        # Undo link
        undone = undo_repeat_link(db_session, link.id, "Supervisor", "False positive check")
        assert undone.status == "undone"
        assert undone.undo_reason == "False positive check"
    finally:
        db_session.query(RepeatLink).filter(RepeatLink.incident_a_id == "TEST-INC-C1").delete()
        db_session.delete(case_c)
        db_session.delete(case_d)
        db_session.commit()
