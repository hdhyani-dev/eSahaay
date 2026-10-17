"""Test every priority level (P0, P1, P2, P3), language scripts, and multi-label routing order.
Reference: Prompt Section 7, Section 13
"""
import pytest
from sahaay.triage.pipeline import run_triage_pipeline
from sahaay.triage.routing import determine_service_routes

def test_p0_critical_urgency_hinglish():
    # Active assault + weapon + child present
    text = "bhaiya pati chaku leke maar raha hai, Sector 14 Rohini, bacche ro rahe hain"
    res = run_triage_pipeline(text)
    assert res["urgency"] == "P0"
    assert res["rules_floor"] == "P0"
    assert "police" in res["routes"]
    assert "shelter" in res["routes"]

def test_p0_critical_urgency_devanagari():
    # Hindi written in Devanagari script
    text = "मेरी माँ को सीने में बहुत दर्द है और साँस नहीं आ रही है, जल्दी एम्बुलेंस भेजो"
    res = run_triage_pipeline(text)
    assert res["urgency"] == "P0"
    assert "medical" in res["routes"]

def test_p1_high_urgency_stalking():
    # Stalking in transit
    text = "wahi aadmi phir se bike se peecha kar raha hai Patel Nagar metro ke paas"
    res = run_triage_pipeline(text)
    assert res["urgency"] in ["P0", "P1"]
    assert "police" in res["routes"]

def test_p2_medium_urgency_harassment():
    # Past dispute without active weapon
    text = "kal padosi ne jhagda kiya tha aur gali di thi, complaint darj karwani hai"
    res = run_triage_pipeline(text)
    assert res["urgency"] in ["P1", "P2"]

def test_p3_low_urgency_legal_query():
    # Non-immediate legal advice
    text = "talaq ke baad maintenance claim karne ka kya procedure hota hai court mein"
    res = run_triage_pipeline(text)
    assert res["urgency"] == "P3"
    assert "legal" in res["routes"]
    assert "police" not in res["routes"]

def test_service_routing_ordering():
    # Life-threatening medical emergency should prioritize medical before police
    threat_types = [{"type": "medical_emergency", "p": 0.95}, {"type": "accident_fire", "p": 0.85}]
    details = {"injury": "bleeding", "ongoing": True}
    routes = determine_service_routes(threat_types, details, "P0", {})
    route_services = [r["service"] for r in routes]
    assert route_services[0] == "medical"
    if "police" in route_services:
        assert route_services.index("medical") < route_services.index("police")
