"""Test Location Recovery service, candidate extraction, and manual gazetteer search.
Reference: Prompt Section 8, Section 13
"""
import pytest
from sqlalchemy.orm import Session
from sahaay.database import SessionLocal, init_database
from sahaay.models import Incident
from sahaay.services.location_service import (
    get_incidents_needing_location_recovery,
    get_location_recovery_details,
    confirm_candidate_location,
    manual_search_gazetteer
)

@pytest.fixture
def db_session():
    init_database()
    db = SessionLocal()
    yield db
    db.close()

def test_gazetteer_manual_search():
    # Test locality search
    results = manual_search_gazetteer("Rohini")
    assert len(results) > 0
    top = results[0]
    assert "rohini" in top["text"].lower()
    assert top["lat"] is not None
    assert top["lon"] is not None

    # Test landmark search
    hosp_results = manual_search_gazetteer("AIIMS")
    assert len(hosp_results) > 0
    assert "aiims" in hosp_results[0]["text"].lower()

    # Test pincode search
    pin_results = manual_search_gazetteer("110005")
    assert len(pin_results) > 0

def test_confirm_candidate_location(db_session: Session):
    # Retrieve an incident or create test incident
    inc = db_session.query(Incident).first()
    if inc:
        original_loc = inc.location_text
        updated = confirm_candidate_location(
            db=db_session,
            incident_id=inc.id,
            location_text="Sector 15 Rohini",
            latitude=28.7215,
            longitude=77.1310,
            actor_id="OP1042",
            location_type="locality"
        )
        assert updated.location_text == "Sector 15 Rohini"
        assert updated.location_confidence == 1.0
        assert updated.location_source == "operator_confirmed"
