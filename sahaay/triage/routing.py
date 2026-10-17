"""M5 Router: Multi-label service routing and priority ordering.
Reference: Section 4.3, FR-5.1, FR-5.2
"""
from typing import List, Dict, Any
from sahaay.config import settings

SERVICE_METADATA = {
    "police": {"name": "Police (112)", "contact": "112", "icon": "🚓", "base_priority": 1},
    "medical": {"name": "Medical / Ambulance (108)", "contact": "108", "icon": "🚑", "base_priority": 0}, # Medical first in life hazards
    "fire": {"name": "Fire Services (101)", "contact": "101", "icon": "🚒", "base_priority": 0},
    "shelter": {"name": "Shelter / NGO (181)", "contact": "181", "icon": "🏠", "base_priority": 2},
    "legal": {"name": "Legal Aid (15100)", "contact": "15100", "icon": "⚖️", "base_priority": 3},
    "counseling": {"name": "Counseling / Tele-MANAS (14416)", "contact": "14416", "icon": "🧠", "base_priority": 4},
    "no_action": {"name": "No Action / Log Query", "contact": "N/A", "icon": "📁", "base_priority": 5}
}

def determine_service_routes(
    threat_types: List[Dict[str, Any]],
    details: Dict[str, Any],
    urgency: str,
    covert_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Compute multi-label service recommendations with priority ordering and reasons.
    """
    recommended = {}
    
    # 1. Check covert distress
    if covert_info.get("covert_detected"):
        recommended["police"] = {
            "service": "police",
            "priority_order": 1,
            "reason": "Covert distress detected; silent police dispatch recommended without callback."
        }
        recommended["shelter"] = {
            "service": "shelter",
            "priority_order": 2,
            "reason": "Safe accommodation and protection outreach."
        }

    # 2. Check threat types
    for t in threat_types:
        threat = t["type"]
        
        if threat == "domestic_violence":
            recommended["police"] = {
                "service": "police",
                "priority_order": 1,
                "reason": "Immediate physical protection and law enforcement intervention."
            }
            recommended["shelter"] = {
                "service": "shelter",
                "priority_order": 2,
                "reason": "Temporary emergency shelter and victim protection."
            }
            if details.get("injury"):
                recommended["medical"] = {
                    "service": "medical",
                    "priority_order": 0,
                    "reason": f"Immediate medical care for {details.get('injury')}."
                }
            if not details.get("ongoing"):
                recommended["legal"] = {
                    "service": "legal",
                    "priority_order": 3,
                    "reason": "Legal aid for DV protection orders and maintenance."
                }

        elif threat == "medical_emergency":
            recommended["medical"] = {
                "service": "medical",
                "priority_order": 0,
                "reason": "Immediate emergency ambulance dispatch and life support."
            }
            if any(k in str(details) for k in ["accident", "chaku", "violence", "wound"]):
                recommended["police"] = {
                    "service": "police",
                    "priority_order": 1,
                    "reason": "Police notification for medico-legal investigation."
                }

        elif threat == "accident_fire":
            recommended["fire"] = {
                "service": "fire",
                "priority_order": 0,
                "reason": "Immediate Fire Brigade (101) dispatch for structural fire / explosion suppression."
            }
            recommended["police"] = {
                "service": "police",
                "priority_order": 1,
                "reason": "Police dispatch for perimeter security, cordon and traffic evacuation."
            }
            recommended["medical"] = {
                "service": "medical",
                "priority_order": 0,
                "reason": "Ambulance dispatch for burn trauma, asphyxiation and casualties."
            }

        elif threat == "sexual_violence":
            recommended["police"] = {
                "service": "police",
                "priority_order": 1,
                "reason": "Emergency police dispatch and evidence preservation."
            }
            recommended["medical"] = {
                "service": "medical",
                "priority_order": 0,
                "reason": "Immediate medical examination and trauma treatment."
            }
            recommended["shelter"] = {
                "service": "shelter",
                "priority_order": 2,
                "reason": "Crisis intervention and shelter support."
            }
            recommended["legal"] = {
                "service": "legal",
                "priority_order": 3,
                "reason": "Legal aid for victim representation."
            }

        elif threat == "stalking_harassment":
            recommended["police"] = {
                "service": "police",
                "priority_order": 1,
                "reason": "Police dispatch / PCR van alert for active harassment or pursuit."
            }
            recommended["legal"] = {
                "service": "legal",
                "priority_order": 2,
                "reason": "Legal advice regarding restraining orders."
            }

        elif threat == "child_at_risk":
            recommended["police"] = {
                "service": "police",
                "priority_order": 1,
                "reason": "Child protection emergency dispatch."
            }
            recommended["shelter"] = {
                "service": "shelter",
                "priority_order": 2,
                "reason": "Childline 1098 and Child Welfare Committee notification."
            }

        elif threat == "mental_health_crisis":
            recommended["counseling"] = {
                "service": "counseling",
                "priority_order": 1,
                "reason": "Tele-MANAS psychological first aid and psychiatric crisis support."
            }
            if urgency in ["P0", "P1"]:
                recommended["medical"] = {
                    "service": "medical",
                    "priority_order": 0,
                    "reason": "Emergency medical team for acute self-harm risk."
                }

        elif threat == "legal_query":
            recommended["legal"] = {
                "service": "legal",
                "priority_order": 1,
                "reason": "Free legal aid counseling and court procedure assistance."
            }

    # 2.5 Safety floor routing for high-urgency incidents with weapons or violence
    if urgency in ["P0", "P1"]:
        if "police" not in recommended:
            recommended["police"] = {
                "service": "police",
                "priority_order": 1,
                "reason": "Immediate police emergency response for active life hazard or violent escalation."
            }

    # 3. Default fallback if no active threat
    if not recommended:
        recommended["no_action"] = {
            "service": "no_action",
            "priority_order": 5,
            "reason": "Caller inquiry logged; no emergency field dispatch required."
        }

    # Sort services by priority order
    sorted_services = sorted(recommended.values(), key=lambda x: x["priority_order"])
    return sorted_services
