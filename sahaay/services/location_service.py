"""Location Recovery Service: Handles missing, ambiguous, and candidate location resolution.
Reference: PRD Section 6.H, FR-2.1
"""
import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sahaay.models import Incident, TranscriptSegment, AuditEvent
from sahaay.triage.geo import extract_location_candidates, DELHI_GAZETTEER
from sahaay.audit import log_audit_event
from rapidfuzz import fuzz

CLARIFICATION_QUESTIONS = [
    {
        "type": "landmark",
        "question": "Aapke aas-paas koi mashhoor hospital, school, ya petrol pump hai? (Is there a known hospital, school or petrol pump nearby?)"
    },
    {
        "type": "metro",
        "question": "Aapke sabse nazdeek kaunsa metro station ya bus stand hai? (Which is the nearest metro station or bus stand?)"
    },
    {
        "type": "street_gate",
        "question": "Aap kis gali number, block ya gate number par khade hain? (Which lane, block or gate number are you at?)"
    },
    {
        "type": "safe_yes_no",
        "question": "Kya aap kisi safe dukaan ya building ke andar ja sakte hain aur wahan ka board dekh sakte hain? (Can you step inside a shop/building and read the board safely?)"
    }
]

def get_incidents_needing_location_recovery(db: Session) -> List[Incident]:
    """Retrieve all open or active incidents where location is missing, low-confidence, or unconfirmed."""
    incidents = db.query(Incident).filter(
        Incident.status.in_(["active", "in_progress", "dispatched"])
    ).all()
    
    needing_recovery = []
    for inc in incidents:
        is_missing = not inc.location_text or inc.location_text.strip() == "" or inc.location_source == "missing"
        is_low_conf = (inc.location_confidence or 0.0) < 0.85
        is_relative = inc.location_source in ["relative_direction", "approximate"]
        
        if is_missing or is_low_conf or is_relative:
            needing_recovery.append(inc)
            
    return needing_recovery

def get_location_recovery_details(incident: Incident, db: Session) -> Dict[str, Any]:
    """
    Compute structured location recovery details for a selected incident:
    - Combined transcript text
    - Extracted candidates from gazetteer & spatial syntax
    - Suggested clarification questions
    """
    # Fetch all transcript segments
    segments = db.query(TranscriptSegment).filter(TranscriptSegment.incident_id == incident.id).order_by(TranscriptSegment.id.asc()).all()
    combined_text = " ".join([seg.raw_text for seg in segments]) if segments else (incident.primary_threat or "")
    
    # Extract candidates
    candidates = extract_location_candidates(combined_text)
    
    # If no candidates from transcript, populate top nearby hubs as fallback candidates
    fallback_candidates = []
    if not candidates:
        for name, meta in list(DELHI_GAZETTEER.items())[:4]:
            fallback_candidates.append({
                "text": name.title(),
                "type": meta["type"],
                "confidence": 0.35,
                "lat": meta["lat"],
                "lon": meta["lon"],
                "source": "city_fallback_candidate"
            })
            
    is_confirmed = (incident.location_confidence or 0.0) >= 0.95 and incident.location_source == "operator_confirmed"
    
    return {
        "incident_id": incident.id,
        "caller_name": incident.caller_name or "Caller",
        "current_location_text": incident.location_text,
        "current_confidence": incident.location_confidence or 0.0,
        "current_source": incident.location_source or "missing",
        "is_confirmed": is_confirmed,
        "candidates": candidates if candidates else fallback_candidates,
        "suggested_questions": CLARIFICATION_QUESTIONS,
        "transcript_text": combined_text
    }

def confirm_candidate_location(
    db: Session,
    incident_id: str,
    location_text: str,
    latitude: float,
    longitude: float,
    actor_id: str,
    location_type: str = "confirmed_place"
) -> Incident:
    """Confirm an extracted candidate or operator-selected location."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise ValueError(f"Incident {incident_id} not found")
        
    before_state = {
        "location_text": incident.location_text,
        "confidence": incident.location_confidence,
        "source": incident.location_source
    }
    
    incident.location_text = location_text
    incident.latitude = latitude
    incident.longitude = longitude
    incident.location_confidence = 1.0
    incident.location_source = "operator_confirmed"
    incident.location_type = location_type
    incident.updated_at = datetime.datetime.utcnow()
    
    db.commit()
    db.refresh(incident)
    
    log_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role="operator",
        action="LOCATION_CONFIRMED",
        object_type="incident",
        object_id=incident_id,
        before_state=before_state,
        after_state={
            "location_text": location_text,
            "latitude": latitude,
            "longitude": longitude,
            "confidence": 1.0,
            "source": "operator_confirmed"
        },
        reason=f"Operator verified and confirmed location: {location_text}"
    )
    return incident

def manual_search_gazetteer(query: str) -> List[Dict[str, Any]]:
    """Search Delhi NCR gazetteer by place name, pincode or landmark."""
    q_clean = query.strip().lower()
    matches = []
    
    for place, meta in DELHI_GAZETTEER.items():
        score = 0.0
        if q_clean == place:
            score = 1.0
        elif q_clean in place or place in q_clean:
            score = 0.85
        else:
            sim = fuzz.partial_ratio(q_clean, place)
            if sim >= 75:
                score = sim / 100.0
                
        if meta.get("pincode") and q_clean in meta["pincode"]:
            score = max(score, 0.95)
            
        if score > 0.65:
            matches.append({
                "text": place.title(),
                "type": meta["type"],
                "pincode": meta.get("pincode", "N/A"),
                "lat": meta["lat"],
                "lon": meta["lon"],
                "confidence": round(score, 2),
                "source": "gazetteer_search"
            })
            
    return sorted(matches, key=lambda x: -x["confidence"])[:5]
