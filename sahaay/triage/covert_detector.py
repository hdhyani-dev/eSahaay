"""M3 Covert-Signal Detector: Identifies indirect distress, code words, and whispered calls.
Reference: FR-4.1, FR-4.2, FR-4.3
"""
import re
from typing import Dict, List, Any, Optional
from rapidfuzz import fuzz
from sahaay.config import _load_yaml, CONFIG_DIR

# Load covert signals lexicon
covert_path = CONFIG_DIR / "lexicon" / "covert_signals.yaml"
COVERT_ENTRIES = _load_yaml(covert_path).get("entries", [])

WHISPER_INDICATORS = [
    r'\(whisper.*?\)',
    r'\(fusfus.*?\)',
    r'dheere\s+bol',
    r'chupke\s+se',
    r'awaaz\s+mat\s+karo',
    r'sun\s+lega',
    r'koi\s+sun\s+raha',
    r'room\s+mein\s+hai'
]

SILENCE_TRUNCATION_INDICATORS = [
    r'\.\.\.',
    r'phone\s+kat\s+gaya',
    r'cut\s+call',
    r'line\s+drop',
    r'\(then\s+silence\)'
]

def detect_covert_signals(raw_text: str, normalized_text: str) -> Dict[str, Any]:
    """
    Scan transcript for covert distress phrases, whispered signals, and secrecy indicators.
    Returns covert risk floor, matched lexicon items, and safety-oriented questions.
    """
    text_lower = (raw_text + " " + normalized_text).lower().strip()
    
    if not text_lower:
        return {
            "covert_detected": False,
            "covert_level": "P3",
            "has_whisper": False,
            "has_truncation": False,
            "matched_entries": [],
            "suggested_safe_question": None,
            "suggested_safe_question_hi": None,
            "safe_contact_flag": True
        }

    matches = []
    max_covert_level = "P3"
    suggested_question = None
    suggested_question_hi = None
    safe_contact = True
    
    # 1. Check covert lexicon entries
    for entry in COVERT_ENTRIES:
        phrase = entry["phrase"].lower()
        variants = [v.lower() for v in entry.get("variants", [])]
        all_phrases = [phrase] + variants
        
        found = False
        matched_str = ""
        for p in all_phrases:
            if re.search(r'\b' + re.escape(p) + r'\b', text_lower):
                found = True
                matched_str = p
                break
            elif len(p) > 6 and fuzz.partial_ratio(p, text_lower) >= 88:
                found = True
                matched_str = p
                break
                
        if found:
            risk = entry.get("risk_class", "P1")
            matches.append({
                "id": entry["id"],
                "phrase": matched_str,
                "threat_type": entry["threat_type"],
                "risk_class": risk,
                "meaning": entry["canonical_meaning"],
                "evidence_span": matched_str
            })
            if risk == "P0" or (risk == "P1" and max_covert_level != "P0"):
                max_covert_level = risk
            if not suggested_question:
                suggested_question = entry.get("suggested_safe_question")
                suggested_question_hi = entry.get("suggested_safe_question_hi")
            safe_contact = False # Covert calls must NEVER receive an unsafe callback

    # 2. Check for whisper or secrecy cues
    has_whisper = any(re.search(pat, text_lower) for pat in WHISPER_INDICATORS)
    has_truncation = any(re.search(pat, text_lower) for pat in SILENCE_TRUNCATION_INDICATORS)
    
    if has_whisper or has_truncation:
        if max_covert_level == "P3":
            max_covert_level = "P1" # Whisper or silence with distress elevates to P1
        safe_contact = False
        if not suggested_question:
            suggested_question = "Are you in immediate danger? Answer with Yes or No only."
            suggested_question_hi = "Kya aap khatre mein hain? Sirf Haan ya Nahi bolein."

    return {
        "covert_detected": len(matches) > 0 or has_whisper,
        "covert_level": max_covert_level,
        "matches": matches,
        "has_whisper": has_whisper,
        "has_truncation": has_truncation,
        "safe_contact_flag": safe_contact,
        "suggested_safe_question": suggested_question,
        "suggested_safe_question_hi": suggested_question_hi
    }
