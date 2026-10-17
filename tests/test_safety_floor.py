"""Test safety-first urgency scoring, rules floor, and uncertainty escalation."""
import pytest
from sahaay.triage.urgency import resolve_urgency, max_risk, escalate_level

def test_safety_floor_prevents_downgrade():
    # If rules floor is P0 (active violence/weapon), model predicting P2 or P3 MUST NOT downgrade
    details = {"weapon": "knife", "injury": "bleeding", "ongoing": True}
    covert_info = {"covert_detected": False, "covert_level": "P3"}
    locations = [{"text": "Rohini", "confidence": 0.9}]
    threat_types = [{"type": "domestic_violence", "p": 0.95}]

    result = resolve_urgency(
        raw_text="chaku dikha ke maar raha hai",
        threat_types=threat_types,
        details=details,
        covert_info=covert_info,
        location_candidates=locations,
        model_predicted_level="P3", # Attempted model downgrade
        model_confidence=0.90
    )
    # Must remain P0 Critical
    assert result["final_urgency"] == "P0"
    assert result["rules_floor"] == "P0"

def test_uncertainty_escalation():
    # Low confidence (< 0.70) must raise urgency one level and set VERIFY flag
    details = {"ongoing": True}
    covert_info = {"covert_detected": False, "covert_level": "P3"}
    locations = [{"text": "Karol Bagh", "confidence": 0.85}]
    threat_types = [{"type": "other", "p": 0.40}]

    result = resolve_urgency(
        raw_text="kuch ajeeb lag raha hai dar lag raha hai",
        threat_types=threat_types,
        details=details,
        covert_info=covert_info,
        location_candidates=locations,
        model_predicted_level="P2",
        model_confidence=0.50 # Low confidence < 0.70
    )
    assert "VERIFY" in result["flags"]
    assert result["final_urgency"] == "P1" # Escalated from P2 to P1

def test_short_evasive_transcript_safety():
    # FR-4.2: Very short transcript with risk cue escalates to at least P1
    details = {"ongoing": True}
    covert_info = {"covert_detected": False, "covert_level": "P3"}
    locations = []
    threat_types = [{"type": "domestic_violence", "p": 0.70}]

    result = resolve_urgency(
        raw_text="bachao", # 1 word
        threat_types=threat_types,
        details=details,
        covert_info=covert_info,
        location_candidates=locations,
        model_predicted_level="P3",
        model_confidence=0.60
    )
    assert result["final_urgency"] in ["P0", "P1"]
    assert "SHORT_TRANSCRIPT" in result["flags"]
    assert "VERIFY" in result["flags"]
