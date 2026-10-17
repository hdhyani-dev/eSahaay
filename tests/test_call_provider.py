"""Test CallSessionProvider, SimulatedCallProvider, and call lifecycle.
Reference: Prompt Section 3, Section 13
"""
import pytest
from sahaay.providers.call_provider import (
    SimulatedCallProvider,
    CallSessionState,
    PREDEFINED_SIMULATION_SCENARIOS
)

def test_simulated_call_provider_lifecycle():
    provider = SimulatedCallProvider()
    assert provider.is_simulation() is True

    # 1. Start incoming call
    session = provider.start_call("scen_domestic_violence")
    assert session is not None
    assert session["state"] == CallSessionState.RINGING
    assert session["caller_name"] == "Sunita Verma"
    assert len(session["segments_queue"]) > 0

    session_id = session["session_id"]

    # 2. Answer call
    answered = provider.answer_call(session_id)
    assert answered["state"] == CallSessionState.CONNECTED

    # 3. Stream next transcript event
    evt1 = provider.get_next_transcript_event(session_id)
    assert evt1 is not None
    assert evt1.segment_id == 1
    assert evt1.is_final is False  # First is partial
    assert "jaldi aao" in evt1.text

    evt2 = provider.get_next_transcript_event(session_id)
    assert evt2 is not None
    assert evt2.segment_id == 2
    assert evt2.is_final is True

    # 4. Pause and Resume
    paused = provider.pause_call(session_id)
    assert paused["state"] == CallSessionState.PAUSED
    resumed = provider.resume_call(session_id)
    assert resumed["state"] == CallSessionState.CONNECTED

    # 5. End call
    ended = provider.end_call(session_id)
    assert ended["state"] == CallSessionState.ENDED

def test_call_rejection():
    provider = SimulatedCallProvider()
    session = provider.start_call("scen_cardiac_medical")
    session_id = session["session_id"]
    rejected = provider.reject_call(session_id)
    assert rejected["state"] == CallSessionState.REJECTED

def test_accumulated_transcript():
    provider = SimulatedCallProvider()
    session = provider.start_call("scen_covert_pizza")
    session_id = session["session_id"]
    provider.answer_call(session_id)
    
    # Read two segments
    provider.get_next_transcript_event(session_id)
    provider.get_next_transcript_event(session_id)
    
    accum = provider.get_accumulated_transcript(session_id)
    assert len(accum) > 0
    assert "pizza" in accum.lower()

def test_concurrent_sessions_isolation():
    # Two distinct provider instances or distinct session IDs must isolate caller state
    p1 = SimulatedCallProvider()
    p2 = SimulatedCallProvider()

    s1 = p1.start_call("scen_domestic_violence")
    s2 = p2.start_call("scen_cardiac_medical")

    assert s1["session_id"] != s2["session_id"]
    assert s1["caller_name"] != s2["caller_name"]

    p1.answer_call(s1["session_id"])
    assert s1["state"] == CallSessionState.CONNECTED
    assert s2["state"] == CallSessionState.RINGING

def test_empty_or_noisy_input_resilience():
    from sahaay.triage.pipeline import run_triage_pipeline
    # Empty string is treated as uncertain and escalated with VERIFY flag
    res_empty = run_triage_pipeline("")
    assert res_empty["urgency"] in ["P1", "P2", "P3"]
    assert "VERIFY" in res_empty["flags"]
    assert res_empty["confidence"] > 0

    # Very noisy non-emergency string
    res_noise = run_triage_pipeline("asdfgh jkloiuy trewq 9988")
    assert res_noise["urgency"] in ["P1", "P2", "P3"]
    assert "other" in [t["type"] for t in res_noise["threat_types"]]
