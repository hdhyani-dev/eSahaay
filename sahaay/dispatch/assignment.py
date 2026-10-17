"""Unit assignment service for simulated dispatch.
Reference: Section 8.F, Section 9
"""
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sahaay.models import Incident, ResponseUnit, DispatchAssignment
from sahaay.dispatch.distance import calculate_haversine_km, estimate_route_km
from sahaay.dispatch.eta import compute_eta_details
from sahaay.audit import log_audit_event

def get_units_for_incident(
    db: Session,
    incident_id: str,
    service_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List candidate responder units sorted by approximate distance to the incident.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident or incident.latitude is None or incident.longitude is None:
        inc_lat, inc_lon = 28.6139, 77.2090 # Default Delhi center
    else:
        inc_lat, inc_lon = incident.latitude, incident.longitude

    query = db.query(ResponseUnit)
    if service_type and service_type != "all":
        query = query.filter(ResponseUnit.service_type == service_type)
        
    units = query.all()
    results = []
    
    for u in units:
        dist_km = calculate_haversine_km(u.current_lat, u.current_lon, inc_lat, inc_lon)
        route_km = estimate_route_km(u.current_lat, u.current_lon, inc_lat, inc_lon)
        eta_info = compute_eta_details(route_km, u.speed_kmh)
        
        results.append({
            "unit_id": u.id,
            "unit_name": u.unit_name,
            "service_type": u.service_type,
            "call_sign": u.call_sign,
            "status": u.status,
            "current_lat": u.current_lat,
            "current_lon": u.current_lon,
            "distance_km": dist_km,
            "route_km": route_km,
            "eta_minutes": eta_info["eta_minutes"],
            "estimated_arrival": eta_info["estimated_arrival_time"],
            "is_available": u.status in ["available", "completed"]
        })
        
    return sorted(results, key=lambda x: (not x["is_available"], x["distance_km"]))

def get_all_services_nearest_units(
    db: Session,
    target_lat: float = 28.6139,
    target_lon: float = 77.2090
) -> List[Dict[str, Any]]:
    """
    Find the single nearest vehicle for EVERY emergency service type:
    - Police (PCR Van - 112)
    - Medical (Ambulance ALS/BLS - 108)
    - Fire (Fire Tender - 101)
    - Shelter / Women Support (Saheli Crisis Van - 181)
    Calculated relative to caller or incident GPS coordinates.
    """
    all_units = db.query(ResponseUnit).all()
    service_order = ["police", "medical", "fire", "shelter"]
    
    evaluated = []
    for u in all_units:
        dist_km = calculate_haversine_km(u.current_lat, u.current_lon, target_lat, target_lon)
        route_km = estimate_route_km(u.current_lat, u.current_lon, target_lat, target_lon)
        eta_info = compute_eta_details(route_km, u.speed_kmh)
        evaluated.append({
            "unit_id": u.id,
            "unit_name": u.unit_name,
            "service_type": u.service_type,
            "call_sign": u.call_sign,
            "status": u.status,
            "current_lat": u.current_lat,
            "current_lon": u.current_lon,
            "distance_km": dist_km,
            "route_km": route_km,
            "eta_minutes": eta_info["eta_minutes"],
            "estimated_arrival": eta_info["estimated_arrival_time"],
            "is_available": u.status in ["available", "completed"]
        })
    
    nearest_by_service = []
    for stype in service_order:
        candidates = [u for u in evaluated if u["service_type"] == stype]
        if candidates:
            sorted_cand = sorted(candidates, key=lambda x: (not x["is_available"], x["distance_km"]))
            nearest_by_service.append(sorted_cand[0])
            
    return nearest_by_service


def assign_unit_to_incident(
    db: Session,
    incident_id: str,
    unit_id: str,
    assigned_by: str = "Operator"
) -> DispatchAssignment:
    """Assign a response unit to an incident and transition unit status."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    unit = db.query(ResponseUnit).filter(ResponseUnit.id == unit_id).first()
    
    if not incident or not unit:
        raise ValueError("Incident or Response Unit not found")
        
    inc_lat = incident.latitude or 28.6139
    inc_lon = incident.longitude or 77.2090
    route_km = estimate_route_km(unit.current_lat, unit.current_lon, inc_lat, inc_lon)
    eta_info = compute_eta_details(route_km, unit.speed_kmh)
    
    # Create assignment record
    assignment = DispatchAssignment(
        incident_id=incident_id,
        unit_id=unit_id,
        service_type=unit.service_type,
        status="assigned",
        dispatched_at=datetime.datetime.utcnow(),
        distance_km=route_km,
        eta_minutes=eta_info["eta_minutes"],
        assigned_by=assigned_by
    )
    db.add(assignment)
    db.flush()
    
    # Update unit state
    unit.status = "assigned"
    unit.current_assignment_id = assignment.id
    unit.last_updated = datetime.datetime.utcnow()
    
    # Update incident state
    incident.status = "dispatched"
    incident.updated_at = datetime.datetime.utcnow()
    
    db.commit()
    db.refresh(assignment)

    log_audit_event(
        db=db,
        actor_id=assigned_by,
        actor_role="operator",
        action="DISPATCH_UNIT_ASSIGNED",
        object_type="dispatch",
        object_id=str(assignment.id),
        after_state={
            "incident_id": incident_id,
            "unit_id": unit_id,
            "service_type": unit.service_type,
            "initial_eta": eta_info["eta_minutes"]
        },
        reason=f"Assigned {unit.unit_name} ({unit_id}) to {incident_id}"
    )
    return assignment
