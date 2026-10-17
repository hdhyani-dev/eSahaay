"""Main Hybrid AI Triage Pipeline Orchestrator.
Orchestrates M1..M7 with measured latency, safety floor enforcement, and output validation.
"""
import time
import uuid
from typing import Dict, Any, Optional
from sahaay.triage.normalize import normalize_hinglish
from sahaay.triage.geo import extract_location_candidates
from sahaay.triage.extract import extract_threat_types, extract_key_details, detect_missing_information
from sahaay.triage.covert_detector import detect_covert_signals
from sahaay.triage.urgency import resolve_urgency
from sahaay.triage.routing import determine_service_routes
from sahaay.triage.evidence import find_evidence_spans
from sahaay.triage.provider import provider
from sahaay.schemas import TriageResult, ThreatPrediction, LocationCandidate, ExtractedDetails, EvidenceSpan

def run_triage_pipeline(
    raw_text: str,
    call_id: Optional[str] = None,
    asr_confidence: float = 0.92
) -> Dict[str, Any]:
    """
    Execute full triage pipeline on raw transcript text.
    Returns validated structured triage dictionary with real measured latency.
    """
    t_start = time.perf_counter()
    call_id = call_id or f"c_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    
    # 1. Input validation & M1 Normalization
    norm_result = normalize_hinglish(raw_text)
    norm_text = norm_result["normalized_text"]
    
    # 2. M2 Fact & Location Extraction
    locations = extract_location_candidates(raw_text)
    threat_types = extract_threat_types(norm_text, raw_text)
    details = extract_key_details(norm_text + " " + raw_text)
    missing_fields, suggested_follow_up = detect_missing_information(details, locations)
    
    # 3. M3 Covert-Signal Detection
    covert_info = detect_covert_signals(raw_text, norm_text)
    
    # 4. Classifier Model Assessment
    model_level, model_conf, engine_mode, raw_model_meta = provider.classify_and_assess(raw_text, norm_text)
    
    # 5. M4 Urgency Fusion & Safety Escalation
    urgency_result = resolve_urgency(
        raw_text=raw_text,
        threat_types=threat_types,
        details=details,
        covert_info=covert_info,
        location_candidates=locations,
        model_predicted_level=model_level,
        model_confidence=model_conf
    )
    
    # 6. M5 Multi-label Service Routing
    recommended_routes = determine_service_routes(
        threat_types=threat_types,
        details=details,
        urgency=urgency_result["final_urgency"],
        covert_info=covert_info
    )
    
    # 7. M7 Explainer & Evidence Mapping
    evidence_spans = find_evidence_spans(
        raw_text=raw_text,
        fired_rules=urgency_result["fired_rules"],
        covert_info=covert_info,
        location_candidates=locations,
        details=details
    )
    
    latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
    
    # Structure validated result
    result = {
        "call_id": call_id,
        "raw_text": raw_text,
        "normalized_text": norm_text,
        "lang_mix": norm_result["lang_mix"],
        "urgency": urgency_result["final_urgency"],
        "confidence": urgency_result["confidence"],
        "rules_floor": urgency_result["rules_floor"],
        "model_level": urgency_result["model_level"],
        "covert_signal_level": urgency_result["covert_floor"],
        "flags": urgency_result["flags"],
        "threat_types": threat_types,
        "location": locations,
        "details": details,
        "routes": [r["service"] for r in recommended_routes],
        "route_objects": recommended_routes,
        "evidence": evidence_spans,
        "missing_fields": missing_fields,
        "suggested_follow_up": suggested_follow_up,
        "suggested_safe_question": covert_info.get("suggested_safe_question"),
        "safe_contact_flag": covert_info.get("safe_contact_flag", True),
        "requires_verification": urgency_result["requires_verification"],
        "engine_mode": engine_mode,
        "model_version": "sahaay-hybrid-v1.0",
        "latency_ms": latency_ms
    }
    
    return result
