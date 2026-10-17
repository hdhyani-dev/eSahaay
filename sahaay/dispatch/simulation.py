"""Deterministic response unit simulation engine.
Reference: Section 8.F, Section 9
"""
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sahaay.models import ResponseUnit, DispatchAssignment, Incident
from sahaay.dispatch.distance import calculate_haversine_km, estimate_route_km
from sahaay.dispatch.eta import compute_eta_details
from sahaay.audit import log_audit_event

STATUS_LIFECYCLE = [
    "assigned",
    "dispatched",
    "acknowledged",
    "en_route",
    "arrived",
    "completed"
]

def step_assignment_simulation(
    db: Session,
    assignment_id: int,
    actor_id: str = "SimulationEngine"
) -> Dict[str, Any]:
    """
    Advance an active dispatch assignment through its deterministic lifecycle:
    assigned -> dispatched -> acknowledged -> en_route (moves coordinates) -> arrived -> completed.
    """
    assignment = db.query(DispatchAssignment).filter(DispatchAssignment.id == assignment_id).first()
    if not assignment:
        return {"error": "Assignment not found"}
        
    unit = db.query(ResponseUnit).filter(ResponseUnit.id == assignment.unit_id).first()
    incident = db.query(Incident).filter(Incident.id == assignment.incident_id).first()
    
    if not unit or not incident:
        return {"error": "Unit or Incident not found"}

    old_status = assignment.status
    now = datetime.datetime.utcnow()
    
    target_lat = incident.latitude or 28.6139
    target_lon = incident.longitude or 77.2090

    # Lifecycle state transitions
    if old_status == "assigned":
        assignment.status = "dispatched"
        assignment.dispatched_at = now
        unit.status = "dispatched"
        
    elif old_status == "dispatched":
        assignment.status = "acknowledged"
        assignment.acknowledged_at = now
        unit.status = "acknowledged"
        
    elif old_status == "acknowledged":
        assignment.status = "en_route"
        assignment.en_route_at = now
        unit.status = "en_route"
        # Move unit 35% towards incident
        unit.current_lat += (target_lat - unit.current_lat) * 0.35
        unit.current_lon += (target_lon - unit.current_lon) * 0.35
        
    elif old_status == "en_route":
        # Check remaining distance
        cur_dist = calculate_haversine_km(unit.current_lat, unit.current_lon, target_lat, target_lon)
        if cur_dist > 0.4:
            # Continue movement towards target
            unit.current_lat += (target_lat - unit.current_lat) * 0.50
            unit.current_lon += (target_lon - unit.current_lon) * 0.50
        else:
            # Arrived at scene!
            unit.current_lat = target_lat
            unit.current_lon = target_lon
            assignment.status = "arrived"
            assignment.arrived_at = now
            unit.status = "arrived"
            
    elif old_status == "arrived":
        assignment.status = "completed"
        assignment.completed_at = now
        unit.status = "available"
        unit.current_assignment_id = None
        # Return to base coordinates
        unit.current_lat = unit.base_lat
        unit.current_lon = unit.base_lon
        incident.status = "resolved"
        incident.resolved_at = now

    # Recalculate remaining distance and ETA
    route_km = estimate_route_km(unit.current_lat, unit.current_lon, target_lat, target_lon)
    if assignment.status == "arrived" or assignment.status == "completed":
        route_km = 0.0
        eta_minutes = 0.0
    else:
        eta_info = compute_eta_details(route_km, unit.speed_kmh)
        eta_minutes = eta_info["eta_minutes"]

    assignment.distance_km = route_km
    assignment.eta_minutes = eta_minutes
    unit.last_updated = now
    
    db.commit()
    db.refresh(assignment)
    db.refresh(unit)

    log_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role="simulator",
        action="DISPATCH_STATUS_STEPPED",
        object_type="dispatch",
        object_id=str(assignment.id),
        before_state={"status": old_status},
        after_state={"status": assignment.status, "unit_status": unit.status, "distance_km": route_km, "eta_minutes": eta_minutes},
        reason=f"Advanced dispatch to {assignment.status}"
    )

    return {
        "assignment_id": assignment.id,
        "old_status": old_status,
        "new_status": assignment.status,
        "unit_status": unit.status,
        "distance_km": route_km,
        "eta_minutes": eta_minutes,
        "unit_lat": round(unit.current_lat, 4),
        "unit_lon": round(unit.current_lon, 4)
    }

def reset_unit_to_base(db: Session, unit_id: str) -> ResponseUnit:
    """Reset unit coordinates to base station and set status to available."""
    unit = db.query(ResponseUnit).filter(ResponseUnit.id == unit_id).first()
    if unit:
        unit.current_lat = unit.base_lat
        unit.current_lon = unit.base_lon
        unit.status = "available"
        unit.current_assignment_id = None
        unit.last_updated = datetime.datetime.utcnow()
        db.commit()
        db.refresh(unit)
    return unit
