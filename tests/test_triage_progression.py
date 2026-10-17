"""Test progressive emergency triage revelation as speech segments arrive.
Ensures emergency types (Medical, Violence, Fire, etc.) do NOT appear prematurely
until the caller explicitly states cues related to that emergency.
"""
import pytest
from sahaay.triage.extract import extract_threat_types
from sahaay.triage.pipeline import run_triage_pipeline
from sahaay.ui.components import render_triage_card

def get_active_threats(text: str):
    res = run_triage_pipeline(text)
    threats = res.get("threat_types", [])
    return [t for t in threats if t.get("type") not in ("other", None)]

def test_greeting_segments_have_no_premature_emergency():
    # Caller only said greeting or cry for help
    t1 = get_active_threats("Hello... bhaiya jaldi aao...")
    assert len(t1) == 0, "No emergency type should trigger on simple greeting"

    t2 = get_active_threats("Hello... bhaiya jaldi aao please, ghar me bahut jhagda ho raha hai.")
    assert len(t2) == 0, "General household argument should not prematurely trigger domestic violence"

def test_emergency_type_triggers_when_violence_stated():
    # Caller explicitly mentions physical beating
    t = get_active_threats("Hello bhaiya, pati maar raha hai bohot buri tarah se...")
    assert len(t) > 0
    assert t[0]["type"] == "domestic_violence"
    assert "Domestic Violence" in t[0]["description"]

def test_emergency_type_triggers_when_medical_stated():
    # Caller explicitly mentions cardiac chest pain or breathlessness
    t = get_active_threats("meri maa ko achanak se severe chest pain ho raha hai, saans nahi aa rahi!")
    assert len(t) > 0
    assert t[0]["type"] == "medical_emergency"
    assert "Medical Emergency" in t[0]["description"]

def test_emergency_type_triggers_when_fire_stated():
    # Caller explicitly mentions building fire
    t = get_active_threats("Aamader flat er ground floor electrical meter box theke bishal agun legeche!")
    assert len(t) > 0
    assert t[0]["type"] == "accident_fire"
