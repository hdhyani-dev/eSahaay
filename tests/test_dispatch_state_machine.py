"""Test dispatch state machine transitions, movement, and cancellation.
Reference: Prompt Section 6.F, Section 13
"""
import pytest
from sqlalchemy.orm import Session
from sahaay.database import SessionLocal, init_database
from sahaay.models import ResponseUnit, Incident, DispatchAssignment
from sahaay.dispatch.assignment import assign_unit_to_incident
from sahaay.dispatch.simulation import step_assignment_simulation, reset_unit_to_base

@pytest.fixture
def db_session():
    init_database()
    db = SessionLocal()
    yield db
    db.close()

def test_dispatch_full_state_cycle(db_session: Session):
    # Retrieve an incident and an available response unit
    incident = db_session.query(Incident).first()
    unit = db_session.query(ResponseUnit).filter(ResponseUnit.status == "available").first()
    assert incident is not None
    assert unit is not None

    # 1. Assigned
    assignment = assign_unit_to_incident(db_session, incident.id, unit.id, "OP1042")
    assert assignment.status == "assigned"

    try:
        # 2. Dispatched
        res1 = step_assignment_simulation(db_session, assignment.id, "OP1042")
        assert res1["new_status"] == "dispatched"

        # 3. Acknowledged
        res2 = step_assignment_simulation(db_session, assignment.id, "OP1042")
        assert res2["new_status"] == "acknowledged"

        # 4. En route
        res3 = step_assignment_simulation(db_session, assignment.id, "OP1042")
        assert res3["new_status"] == "en_route"
        assert res3["distance_km"] > 0

    finally:
        # Clean up / reset unit
        reset_unit_to_base(db_session, unit.id)
        db_session.query(DispatchAssignment).filter(DispatchAssignment.id == assignment.id).delete()
        db_session.commit()
