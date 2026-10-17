"""M6 Repeat-Complaint Matcher: Cautious multi-signal matching with reversible links.
Reference: Section 4.4, 8.3, FR-6.1, FR-6.2, FR-6.3
"""
import math
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from rapidfuzz import fuzz
from sahaay.models import Incident, RepeatLink
from sahaay.repeat_matching.phonetic import get_phonetic_key, phonetic_similarity
from sahaay.audit import log_audit_event

def calculate_time_decay(days_apart: float, half_life_days: float = 30.0) -> float:
    """Exponential time decay weight for recency."""
    if days_apart < 0:
        days_apart = 0
    return math.exp(-0.693 * days_apart / half_life_days)

def match_repeat_complaints(
    current_incident: Incident,
    db: Session,
    lookback_days: int = 180
) -> List[Dict[str, Any]]:
    """
    Find repeat complaint candidates using blocking keys:
    1. Phone HMAC match
    2. Phonetic name key match
    3. Locality token match
    """
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=lookback_days)
    
    # Query candidate pool excluding current incident
    query = db.query(Incident).filter(
        Incident.id != current_incident.id,
        Incident.created_at >= cutoff
    )
    
    candidates = query.all()
    results = []
    
    cur_phone_hmac = current_incident.phone_hmac or ""
    cur_name = current_incident.caller_name or ""
    cur_phonetic = current_incident.name_phonetic or get_phonetic_key(cur_name)
    cur_loc = (current_incident.location_text or "").lower()
    cur_threat = current_incident.primary_threat or ""

    for cand in candidates:
        cand_phone_hmac = cand.phone_hmac or ""
        cand_name = cand.caller_name or ""
        cand_phonetic = cand.name_phonetic or get_phonetic_key(cand_name)
        cand_loc = (cand.location_text or "").lower()
        cand_threat = cand.primary_threat or ""

        # 1. Blocking Key Pre-filter: must share at least ONE blocking signal
        has_phone_match = bool(cur_phone_hmac and cand_phone_hmac and cur_phone_hmac == cand_phone_hmac)
        has_name_match = bool(cur_phonetic and cand_phonetic and cur_phonetic == cand_phonetic)
        has_loc_match = bool(cur_loc and cand_loc and (cur_loc in cand_loc or cand_loc in cur_loc))
        
        if not (has_phone_match or has_name_match or has_loc_match):
            continue # Skip candidates with zero shared blocking keys

        # 2. Individual Signal Scores
        sig_phone = 1.0 if has_phone_match else 0.0
        sig_name = phonetic_similarity(cur_name, cand_name) if (cur_name and cand_name) else 0.0
        sig_place = (fuzz.token_set_ratio(cur_loc, cand_loc) / 100.0) if (cur_loc and cand_loc) else 0.0
        sig_threat = 1.0 if (cur_threat and cand_threat and cur_threat == cand_threat) else 0.0
        
        # Time gap decay
        days_apart = abs((current_incident.created_at - cand.created_at).total_seconds() / 86400.0)
        sig_time = calculate_time_decay(days_apart)
        
        # 3. Multi-signal Weighted Fusion
        # Strict weights from policy
        weights = {"phone": 0.45, "name": 0.20, "place": 0.15, "threat": 0.10, "time": 0.10}
        total_score = (
            sig_phone * weights["phone"] +
            sig_name * weights["name"] +
            sig_place * weights["place"] +
            sig_threat * weights["threat"] +
            sig_time * weights["time"]
        )
        total_score = round(total_score, 3)

        # Count strong independent signals
        strong_signals = sum([
            sig_phone > 0.9,
            sig_name > 0.85,
            sig_place > 0.80
        ])

        # 4. Three-Band Decision Rule:
        # Auto-link requires score >= 0.92 AND at least 2 independent strong signals!
        # Name alone or phone alone NEVER auto-merges!
        if total_score >= 0.92 and strong_signals >= 2:
            band = "auto"
        elif total_score >= 0.55:
            band = "suggest"
        else:
            band = "new"

        if band in ["auto", "suggest"]:
            results.append({
                "candidate_case_id": cand.id,
                "score": total_score,
                "band": band,
                "strong_signals_count": strong_signals,
                "signals": {
                    "phone_match": sig_phone > 0.9,
                    "phonetic_name_score": round(sig_name, 2),
                    "place_match_score": round(sig_place, 2),
                    "threat_match": sig_threat > 0.9,
                    "days_apart": round(days_apart, 1)
                },
                "summary": f"{cand.primary_threat or 'Emergency'} at {cand.location_text or 'Unknown'} ({round(days_apart)}d ago)"
            })

    # Sort results by score descending
    return sorted(results, key=lambda x: -x["score"])

def approve_or_create_link(
    db: Session,
    incident_a_id: str,
    incident_b_id: str,
    score: float,
    band: str,
    signals: Dict[str, Any],
    created_by: str = "supervisor"
) -> RepeatLink:
    """Create or activate a reversible repeat link between two incidents."""
    link = RepeatLink(
        incident_a_id=incident_a_id,
        incident_b_id=incident_b_id,
        score=score,
        band=band,
        signals=signals,
        status="active",
        created_by=created_by,
        created_at=datetime.datetime.utcnow()
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    log_audit_event(
        db=db,
        actor_id=created_by,
        actor_role="supervisor",
        action="REPEAT_LINK_APPROVED",
        object_type="repeat_link",
        object_id=str(link.id),
        before_state={"status": "unlinked"},
        after_state={"status": "active", "band": band, "score": score},
        reason=f"Linked cases {incident_a_id} and {incident_b_id}"
    )
    return link

def undo_repeat_link(
    db: Session,
    link_id: int,
    undone_by: str,
    reason: str
) -> Optional[RepeatLink]:
    """Reversibly undo an auto or suggested repeat link, restoring both case histories."""
    link = db.query(RepeatLink).filter(RepeatLink.id == link_id).first()
    if not link:
        return None
        
    before_state = {"status": link.status}
    link.status = "undone"
    link.undone_at = datetime.datetime.utcnow()
    link.undone_by = undone_by
    link.undo_reason = reason
    db.commit()
    db.refresh(link)

    log_audit_event(
        db=db,
        actor_id=undone_by,
        actor_role="supervisor",
        action="REPEAT_LINK_UNDONE",
        object_type="repeat_link",
        object_id=str(link_id),
        before_state=before_state,
        after_state={"status": "undone", "reason": reason},
        reason=reason
    )
    return link
