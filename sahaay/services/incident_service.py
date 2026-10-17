"""Incident management service: Lifecycle, triage persistence, overrides and queue sorting.
Reference: Section 3, Section 8.B, 8.C, 8.D, 8.E
"""
import datetime
import uuid
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, case
from sahaay.models import Incident, TranscriptSegment, TriageAssessment, RepeatLink
from sahaay.triage.pipeline import run_triage_pipeline
from sahaay.repeat_matching.hashing import hash_phone_hmac, mask_phone_number
from sahaay.repeat_matching.phonetic import get_phonetic_key
from sahaay.repeat_matching.matcher import match_repeat_complaints, approve_or_create_link
from sahaay.audit import log_audit_event

def create_incident_from_transcript(
    db: Session,
    raw_text: str,
    caller_phone: str = "9876543210",
    caller_name: Optional[str] = None,
    created_by: str = "Operator"
) -> Tuple[Incident, TriageAssessment, List[Dict[str, Any]]]:
    """
    Ingest a new call transcript, run the hybrid triage pipeline,
    persist records, check repeat complaint candidates, and return them.
    """
    now = datetime.datetime.utcnow()
    # Generate sequential incident ID
    count = db.query(Incident).count() + 1040
    incident_id = f"INC-{count}"
    
    # Run AI Triage
    triage_dict = run_triage_pipeline(raw_text, call_id=incident_id)
    
    # Phone hashing and masking
    phone_hmac = hash_phone_hmac(caller_phone)
    masked_phone = mask_phone_number(caller_phone)
    phonetic_name = get_phonetic_key(caller_name) if caller_name else None
    
    # Extract best location
    loc_text = None
    lat, lon = None, None
    loc_source = "missing"
    loc_conf = 0.0
    loc_type = None
    
    if triage_dict["location"]:
        best_loc = triage_dict["location"][0]
        loc_text = best_loc["text"]
        lat = best_loc.get("lat")
        lon = best_loc.get("lon")
        loc_conf = best_loc.get("confidence", 0.0)
        loc_source = best_loc.get("source", "transcript")
        loc_type = best_loc.get("type", "locality")

    # Primary threat
    primary_threat = None
    if triage_dict["threat_types"]:
        primary_threat = triage_dict["threat_types"][0]["description"]

    # Create Incident
    incident = Incident(
        id=incident_id,
        caller_masked_phone=masked_phone,
        phone_hmac=phone_hmac,
        caller_name=caller_name,
        name_phonetic=phonetic_name,
        current_urgency=triage_dict["urgency"],
        original_urgency=triage_dict["urgency"],
        is_urgent_pinned=(triage_dict["urgency"] == "P0"),
        status="active",
        primary_threat=primary_threat,
        location_text=loc_text,
        latitude=lat,
        longitude=lon,
        location_confidence=loc_conf,
        location_source=loc_source,
        location_type=loc_type,
        safe_contact_flag=triage_dict["safe_contact_flag"],
        requires_verification=triage_dict["requires_verification"],
        verification_reasons=triage_dict["flags"],
        created_at=now,
        updated_at=now
    )
    db.add(incident)
    db.flush()

    # Add initial transcript segment
    segment = TranscriptSegment(
        incident_id=incident.id,
        timestamp_offset="00:15",
        speaker="Caller",
        raw_text=raw_text,
        normalized_text=triage_dict["normalized_text"],
        lang_mix=triage_dict["lang_mix"],
        asr_confidence=0.92,
        is_whisper=("COVERT_SIGNAL" in triage_dict["flags"])
    )
    db.add(segment)

    # Add TriageAssessment
    assessment = TriageAssessment(
        incident_id=incident.id,
        call_id=incident_id,
        urgency=triage_dict["urgency"],
        confidence=triage_dict["confidence"],
        rules_floor=triage_dict["rules_floor"],
        model_level=triage_dict["model_level"],
        covert_signal_level=triage_dict["covert_signal_level"],
        flags=triage_dict["flags"],
        threat_types=triage_dict["threat_types"],
        details=triage_dict["details"],
        suggested_routes=triage_dict["routes"],
        confirmed_routes=triage_dict["routes"],
        evidence_spans=triage_dict["evidence"],
        missing_fields=triage_dict["missing_fields"],
        suggested_follow_up=triage_dict["suggested_follow_up"],
        suggested_safe_question=triage_dict["suggested_safe_question"],
        model_version=triage_dict["model_version"],
        latency_ms=triage_dict["latency_ms"],
        created_at=now
    )
    db.add(assessment)
    db.commit()
    db.refresh(incident)
    db.refresh(assessment)

    # Check for repeat complaints
    repeat_cands = match_repeat_complaints(incident, db)
    
    # Auto-link if score >= 0.92 and >= 2 strong signals
    for cand in repeat_cands:
        if cand["band"] == "auto":
            approve_or_create_link(
                db=db,
                incident_a_id=incident.id,
                incident_b_id=cand["candidate_case_id"],
                score=cand["score"],
                band="auto",
                signals=cand["signals"],
                created_by="system_auto_link"
            )

    log_audit_event(
        db=db,
        actor_id=created_by,
        actor_role="operator",
        action="INCIDENT_CREATED",
        object_type="incident",
        object_id=incident.id,
        after_state={"urgency": incident.current_urgency, "threat": primary_threat, "routes": triage_dict["routes"]},
        reason="Initial call triage completed"
    )

    return incident, assessment, repeat_cands

def get_live_queue(db: Session) -> List[Incident]:
    """
    Get live incoming queue sorted strictly by:
    1. Pinned P0 Critical calls first
    2. Urgency level: P0 > P1 > P2 > P3
    3. Oldest wait time first (created_at ascending)
    """
    urgency_order = case(
        (Incident.current_urgency == 'P0', 0),
        (Incident.current_urgency == 'P1', 1),
        (Incident.current_urgency == 'P2', 2),
        (Incident.current_urgency == 'P3', 3),
        else_=4
    )
    return db.query(Incident).filter(
        Incident.status.in_(["active", "in_progress", "dispatched"])
    ).order_by(
        desc(Incident.is_urgent_pinned),
        urgency_order,
        Incident.created_at.asc()
    ).all()

def override_incident_urgency(
    db: Session,
    incident_id: str,
    new_urgency: str,
    reason: str,
    actor_id: str,
    actor_role: str
) -> Incident:
    """Override incident priority level with mandatory reason and audit entry."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise ValueError(f"Incident {incident_id} not found")
        
    old_urgency = incident.current_urgency
    incident.current_urgency = new_urgency
    incident.is_urgent_pinned = (new_urgency == "P0")
    incident.override_reason = reason
    incident.override_by = actor_id
    incident.updated_at = datetime.datetime.utcnow()
    
    db.commit()
    db.refresh(incident)

    log_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="PRIORITY_OVERRIDE",
        object_type="incident",
        object_id=incident_id,
        before_state={"urgency": old_urgency},
        after_state={"urgency": new_urgency, "reason": reason},
        reason=reason
    )
    return incident

def confirm_incident_urgency(
    db: Session,
    incident_id: str,
    actor_id: str
) -> Incident:
    """Confirm the recommended priority and move incident to confirmed state."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise ValueError(f"Incident {incident_id} not found")
        
    incident.confirmed_by = actor_id
    incident.confirmed_at = datetime.datetime.utcnow()
    incident.updated_at = datetime.datetime.utcnow()
    
    db.commit()
    db.refresh(incident)

    log_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role="operator",
        action="PRIORITY_CONFIRMED",
        object_type="incident",
        object_id=incident_id,
        after_state={"urgency": incident.current_urgency, "confirmed_by": actor_id},
        reason="Operator confirmed recommended triage priority"
    )
    return incident
