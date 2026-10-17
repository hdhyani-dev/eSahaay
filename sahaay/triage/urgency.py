"""M4 Urgency Engine: Safety-first priority scoring, rules floor, and uncertainty escalation.
Reference: Section 4.1, 4.2, FR-3.1, FR-3.2, FR-3.3
"""
from typing import Dict, List, Any, Tuple
from sahaay.config import settings

# Urgency hierarchy: P0 > P1 > P2 > P3
URGENCY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
RANK_TO_URGENCY = {0: "P0", 1: "P1", 2: "P2", 3: "P3"}

def max_risk(level_a: str, level_b: str) -> str:
    """Return the higher risk (lower rank index) between two levels."""
    rank_a = URGENCY_RANK.get(level_a, 3)
    rank_b = URGENCY_RANK.get(level_b, 3)
    return RANK_TO_URGENCY[min(rank_a, rank_b)]

def escalate_level(level: str, steps: int = 1) -> str:
    """Escalate urgency towards P0. P3 -> P2 -> P1 -> P0."""
    rank = URGENCY_RANK.get(level, 3)
    new_rank = max(0, rank - steps)
    return RANK_TO_URGENCY[new_rank]

def compute_rules_floor(
    text: str,
    threat_types: List[Dict[str, Any]],
    details: Dict[str, Any]
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Evaluate deterministic safety rules.
    Returns (rules_floor, fired_rules).
    """
    text_lower = text.lower()
    fired = []
    current_floor = "P3"
    
    # Rule R1: Active physical violence ongoing
    if any(k in text_lower for k in ["maar raha", "mar rha", "peet raha", "maar rahe", "beating now", "khoon nikal", "bleeding", "मार रहा", "पीट रहा", "खून"]):
        fired.append({"rule_id": "R01_ACTIVE_VIOLENCE", "level": "P0", "reason": "Active physical violence or bleeding reported"})
        current_floor = max_risk(current_floor, "P0")
        
    # Rule R2: Weapon present
    if details.get("weapon") or any(k in text_lower for k in ["chaku", "chaaku", "knife", "bandook", "gun", "talwar", "चाकू", "छुरी", "बंदूक"]):
        fired.append({"rule_id": "R02_WEAPON_PRESENT", "level": "P0", "reason": "Deadly weapon explicitly mentioned"})
        current_floor = max_risk(current_floor, "P0")
        
    # Rule R3: Life-threatening medical emergency
    if any(k in text_lower for k in ["saans nahi", "sans nahi", "chest pain", "behosh", "unconscious", "heart attack", "साँस नहीं", "सांस नहीं", "सीने में दर्द", "बेहोश", "हार्ट अटैक"]):
        fired.append({"rule_id": "R03_CRITICAL_MEDICAL", "level": "P0", "reason": "Respiratory distress, cardiac symptom or unconsciousness"})
        current_floor = max_risk(current_floor, "P0")
        
    # Rule R4: Child at immediate risk
    if (details.get("children_present") or "बच्चे" in text_lower) and current_floor in ["P0", "P1"]:
        fired.append({"rule_id": "R04_CHILD_AT_RISK", "level": "P0", "reason": "Child present in active emergency"})
        current_floor = max_risk(current_floor, "P0")
        
    # Rule R5: Stalking / active pursuit
    if any(k in text_lower for k in ["peecha kar raha", "picha kar", "following me", "wahi aadmi", "पीछा कर रहा"]):
        fired.append({"rule_id": "R05_ACTIVE_STALKING", "level": "P1", "reason": "Active stalking or pursuit in transit"})
        current_floor = max_risk(current_floor, "P1")
        
    # Rule R6: Harassment / non-violent domestic dispute
    if any(t["type"] in ["domestic_violence", "sexual_violence"] for t in threat_types) and current_floor == "P3":
        fired.append({"rule_id": "R06_DOMESTIC_HARASSMENT", "level": "P2", "reason": "Domestic violence or harassment without immediate weapon/injury"})
        current_floor = max_risk(current_floor, "P2")

    # Rule R8: Fire, explosion or catastrophic trauma
    if any(k in text_lower for k in ["aag lag", "cylinder blast", "fire", "overturn", "accident ho gaya", "dhuan", "आग", "सिलेंडर"]):
        fired.append({"rule_id": "R08_FIRE_CRASH_HAZARD", "level": "P0", "reason": "Structural fire, explosion or major crash hazard"})
        current_floor = max_risk(current_floor, "P0")

    # Rule R7: Pure legal aid query
    if any(t["type"] == "legal_query" for t in threat_types) and not any(k in text_lower for k in ["maar", "dhamki", "khatra", "मार", "धमकी"]):
        fired.append({"rule_id": "R07_LEGAL_QUERY", "level": "P3", "reason": "Informational or legal advisory question"})

    return current_floor, fired

def resolve_urgency(
    raw_text: str,
    threat_types: List[Dict[str, Any]],
    details: Dict[str, Any],
    covert_info: Dict[str, Any],
    location_candidates: List[Dict[str, Any]],
    model_predicted_level: str = "P2",
    model_confidence: float = 0.85
) -> Dict[str, Any]:
    """
    Asymmetric Fusion Engine:
    - Rule floor
    - Covert signal floor
    - Model level
    - Uncertainty escalation (VERIFY)
    - Short & evasive transcript safety guard
    """
    rule_floor, fired_rules = compute_rules_floor(raw_text, threat_types, details)
    covert_floor = covert_info.get("covert_level", "P3")
    
    # Max-risk fusion: Start with highest risk among rule floor, covert floor, and model
    level = max_risk(rule_floor, covert_floor)
    level = max_risk(level, model_predicted_level)
    
    flags = []
    if covert_info.get("covert_detected"):
        flags.append("COVERT_SIGNAL")
        
    word_count = len(raw_text.split())
    is_short = word_count <= settings.short_call_word_threshold
    
    # Asymmetric rule: Short and evasive with any risk cue escalates to at least P1
    any_risk = (level in ["P0", "P1"] or covert_info.get("covert_detected") or 
                any(t["type"] not in ["other", "legal_query"] for t in threat_types))
    
    if is_short and any_risk:
        flags.append("SHORT_TRANSCRIPT")
        level = max_risk(level, "P1")
        
    # Missing location with high urgency triggers VERIFY and safety escalation
    missing_loc = len(location_candidates) == 0
    if missing_loc and level in ["P0", "P1"]:
        flags.append("MISSING_LOCATION")
        
    # Uncertainty check (PRD 4.2): conf < TAU, or (missing_location and level in [P0, P1]), or short transcript
    needs_verify = (
        model_confidence < settings.confidence_tau or
        (missing_loc and level in ["P0", "P1"]) or
        "SHORT_TRANSCRIPT" in flags
    )
    if needs_verify:
        flags.append("VERIFY")
        if settings.escalation_rules.get("uncertainty_escalate_one_level", True):
            if level in ["P0", "P1", "P2"]:
                level = escalate_level(level, steps=1)
            
    # Guarantee: Final level CANNOT be lower than rule floor or covert floor
    safety_floor = max_risk(rule_floor, covert_floor)
    if URGENCY_RANK[level] > URGENCY_RANK[safety_floor]:
        level = safety_floor
        
    return {
        "final_urgency": level,
        "confidence": model_confidence,
        "rules_floor": rule_floor,
        "covert_floor": covert_floor,
        "model_level": model_predicted_level,
        "fired_rules": fired_rules,
        "flags": list(set(flags)),
        "requires_verification": "VERIFY" in flags
    }
