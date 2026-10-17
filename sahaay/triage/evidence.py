"""M7 Explainer: Evidence span mapping and justification in caller's own words.
Reference: FR-1.3, FR-7.1
"""
import re
from typing import List, Dict, Any

def find_evidence_spans(
    raw_text: str,
    fired_rules: List[Dict[str, str]],
    covert_info: Dict[str, Any],
    location_candidates: List[Dict[str, Any]],
    details: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Locate character start and end offsets in raw text for every key decision fact.
    """
    evidence_list = []
    text_lower = raw_text.lower()
    
    # 1. Evidence from Fired Safety Rules
    for rule in fired_rules:
        # Extract keywords matching rule
        rule_words = []
        if "ACTIVE_VIOLENCE" in rule["rule_id"]:
            rule_words = ["maar raha", "mar rha", "peet raha", "maar rahe", "khoon", "bleeding"]
        elif "WEAPON" in rule["rule_id"]:
            rule_words = ["chaku", "chaaku", "knife", "bandook", "gun"]
        elif "CRITICAL_MEDICAL" in rule["rule_id"]:
            rule_words = ["saans nahi", "sans nahi", "chest pain", "behosh", "unconscious"]
        elif "STALKING" in rule["rule_id"]:
            rule_words = ["peecha kar raha", "picha kar", "following me", "wahi aadmi"]
            
        for rw in rule_words:
            m = re.search(r'\b' + re.escape(rw) + r'\b', text_lower)
            if m:
                evidence_list.append({
                    "field": "urgency",
                    "span": raw_text[m.start():m.end()],
                    "start": m.start(),
                    "end": m.end(),
                    "rule": rule["rule_id"],
                    "reason": rule["reason"]
                })
                break

    # 2. Evidence from Covert Signals
    for match in covert_info.get("matches", []):
        phrase = match.get("phrase", "")
        if phrase:
            m = re.search(r'\b' + re.escape(phrase) + r'\b', text_lower)
            if m:
                evidence_list.append({
                    "field": "covert_signal",
                    "span": raw_text[m.start():m.end()],
                    "start": m.start(),
                    "end": m.end(),
                    "rule": match.get("id", "COV_MATCH"),
                    "reason": match.get("meaning", "Covert distress code phrase")
                })

    # 3. Evidence from Location
    for loc in location_candidates[:2]:
        loc_text = loc.get("text", "")
        m = re.search(r'\b' + re.escape(loc_text) + r'\b', text_lower, re.IGNORECASE)
        if m:
            evidence_list.append({
                "field": "location",
                "span": raw_text[m.start():m.end()],
                "start": m.start(),
                "end": m.end(),
                "rule": f"LOC_{loc.get('type', 'place').upper()}",
                "reason": f"Identified {loc.get('type')} with confidence {loc.get('confidence', 0):.0%}"
            })

    # 4. Evidence from Details (Perpetrator / Weapon / Injury)
    if details.get("perpetrator_rel"):
        perp = details["perpetrator_rel"]
        m = re.search(r'\b' + re.escape(perp) + r'\b', text_lower)
        if m:
            evidence_list.append({
                "field": "perpetrator",
                "span": raw_text[m.start():m.end()],
                "start": m.start(),
                "end": m.end(),
                "rule": "PERP_REL",
                "reason": f"Reported relation: {perp}"
            })

    return evidence_list

def render_highlighted_transcript(raw_text: str, evidence_spans: List[Dict[str, Any]]) -> str:
    """
    Produce HTML snippet with highlighted spans and tooltips.
    """
    if not evidence_spans:
        return f"<div style='font-family: inherit; font-size: 15px; line-height: 1.6;'>{raw_text}</div>"
        
    # Sort non-overlapping spans by start offset
    sorted_spans = sorted(evidence_spans, key=lambda x: x["start"])
    
    html_parts = []
    last_idx = 0
    
    for span in sorted_spans:
        s = span["start"]
        e = span["end"]
        if s < last_idx:
            continue # Skip overlapping spans
            
        html_parts.append(raw_text[last_idx:s])
        
        # Color coding by field
        bg_color = "#FFEBEB" # Red for urgency/covert
        border_color = "#B42318"
        if span["field"] == "location":
            bg_color = "#EBF5FB" # Blue for location
            border_color = "#286A8A"
        elif span["field"] == "perpetrator":
            bg_color = "#FEF9E7" # Amber
            border_color = "#A15C00"
            
        tooltip = f"{span['rule']}: {span.get('reason', '')}"
        highlight = (
            f"<mark style='background-color: {bg_color}; border-bottom: 2px solid {border_color}; "
            f"padding: 2px 4px; border-radius: 3px; font-weight: 500;' title='{tooltip}'>"
            f"{raw_text[s:e]}</mark>"
        )
        html_parts.append(highlight)
        last_idx = e
        
    html_parts.append(raw_text[last_idx:])
    
    return f"<div style='font-family: inherit; font-size: 15px; line-height: 1.6; color: #253445;'>{''.join(html_parts)}</div>"
