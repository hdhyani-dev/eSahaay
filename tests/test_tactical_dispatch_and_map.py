"""Unit tests for tactical dispatch movement, response escalation, and Folium map builders."""
import pytest
from sqlalchemy.orm import Session
from sahaay.database import SessionLocal, init_database
from sahaay.models import ResponseUnit, Incident, DispatchAssignment
from sahaay.dispatch.assignment import assign_unit_to_incident
from sahaay.dispatch.simulation import (
    step_assignment_simulation,
    reset_unit_to_base,
    advance_unit_towards_incident,
    escalate_unit_response
)
from sahaay.ui.dispatch_map import (
    build_dispatch_tactical_map,
    build_fleet_overview_map,
    generate_unit_tactical_acknowledgment,
    TACTICAL_PRESET_DIRECTIVES
)

@pytest.fixture
def db():
    init_database()
    session = SessionLocal()
    yield session
    session.close()

def test_advance_unit_towards_incident(db: Session):
    incident = db.query(Incident).filter(Incident.latitude.isnot(None)).first()
    unit = db.query(ResponseUnit).filter(ResponseUnit.status == "available").first()
    assert incident is not None
    assert unit is not None

    assignment = assign_unit_to_incident(db, incident.id, unit.id, "OPTest")
    initial_dist = assignment.distance_km

    try:
        # Advance unit 35% towards incident
        res = advance_unit_towards_incident(db, assignment.id, step_fraction=0.35, actor_id="OPTest")
        assert res["status"] == "en_route"
        assert res["unit_status"] == "en_route"
        assert res["distance_km"] < initial_dist
        assert not res["arrived"]

        # Advance unit multiple times until arrival
        for _ in range(10):
            res_adv = advance_unit_towards_incident(db, assignment.id, step_fraction=0.6, actor_id="OPTest")
            if res_adv["arrived"]:
                break

        assert res_adv["arrived"] is True
        assert res_adv["status"] == "arrived"
        assert res_adv["distance_km"] == 0.0
        assert res_adv["eta_minutes"] == 0.0

    finally:
        reset_unit_to_base(db, unit.id)
        db.query(DispatchAssignment).filter(DispatchAssignment.id == assignment.id).delete()
        db.commit()

def test_escalate_unit_response(db: Session):
    incident = db.query(Incident).first()
    unit = db.query(ResponseUnit).filter(ResponseUnit.status == "available").first()
    assignment = assign_unit_to_incident(db, incident.id, unit.id, "OPTest")

    try:
        res = escalate_unit_response(db, assignment.id, code_3=True, speed_boost=25.0, actor_id="OPTest")
        assert res["speed_kmh"] >= 72.0
    finally:
        reset_unit_to_base(db, unit.id)
        db.query(DispatchAssignment).filter(DispatchAssignment.id == assignment.id).delete()
        db.commit()

def test_tactical_acknowledgment_generator():
    ack = generate_unit_tactical_acknowledgment("Ambulance ALS-01", "ALS-01", "", "CODE_3")
    assert "Code 3" in ack
    assert "ALS-01" in ack

    ack_custom = generate_unit_tactical_acknowledgment("Police PCR-14", "PCR-14", "Victim is bleeding heavily, rush doctor")
    assert "PCR-14" in ack_custom
    assert any(w in ack_custom.lower() for w in ["paramedic", "trauma", "doctor", "briefed"])

def test_tactical_map_builders(db: Session):
    incident = db.query(Incident).first()
    unit = db.query(ResponseUnit).first()
    assert incident is not None
    assert unit is not None

    # Test tactical single dispatch map (dark and light modes)
    map_dark = build_dispatch_tactical_map(incident, unit, is_dark=True)
    assert map_dark is not None
    map_light = build_dispatch_tactical_map(incident, unit, is_dark=False)
    assert map_light is not None

    # Test fleet overview map
    all_incidents = db.query(Incident).all()
    all_units = db.query(ResponseUnit).all()
    all_dispatches = db.query(DispatchAssignment).all()
    fleet_map = build_fleet_overview_map(all_incidents, all_units, all_dispatches, is_dark=True)
    assert fleet_map is not None
